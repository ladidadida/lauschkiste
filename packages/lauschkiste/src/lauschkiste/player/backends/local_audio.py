# -*- coding: utf-8 -*-
"""
Default player backend: decodes audio directly (PyAV) and writes PCM to the machine's normal
audio output (sounddevice/PortAudio) -- no mpd, no external player process, works on any Linux
box. See documentation/developers/roadmap-core-architecture.md, "Advanced plugin system".

Folder scanning reuses `lauschkiste.playlistgenerator.PlaylistCollector` (already backend-agnostic --
`backends/mpd.py` uses the exact same class, just pushes the resulting paths into MPD's queue
instead of this backend's own in-process one).

Playback runs on one dedicated worker thread. Every control method (play/pause/stop/next/prev/
seek/play_folder/...) updates `_state`/`_index`/`_position` under `_cv` and sets `_abort` to
interrupt whatever the worker is currently doing; the worker reopens/seeks the current track
whenever it's told to (re)start one. This keeps the state machine in one place instead of trying
to signal a live decode loop with finer-grained commands.
"""
import logging
import os
import random
import threading

import av
import sounddevice as sd
from av.audio.resampler import AudioResampler

import lauschkiste.paths
import lauschkiste.library
import lauschkiste.cfghandler
import lauschkiste.utils as utils
import lauschkiste.multitimer as multitimer
import lauschkiste.playlistgenerator as playlistgenerator

from lauschkiste.audio_output import CHANNELS, SAMPLE_RATE, PortAudioSink, scale_volume
from lauschkiste.nv_manager import nv_manager

logger = logging.getLogger('lauschkiste.PlayerLocalAudio')
cfg = lauschkiste.cfghandler.get_handler('lauschkiste')

class PlayerLocalAudio:
    """Decode-and-output player backend. See module docstring for the state machine."""

    def __init__(self):
        self.nvm = nv_manager()
        self._status_store = self.nvm.load(str(lauschkiste.paths.resolve(
            cfg.getn('player', 'status_file', default='settings/local_audio_status.json'))))
        if not self._status_store:
            self._status_store['last_played_folder'] = ''

        self._status_callback = lambda status: None
        self._cv = threading.Condition(threading.RLock())
        self._abort = threading.Event()
        self._closing = False
        self._active = False

        self._queue: list[str] = []
        self._index = -1
        self._position = 0.0
        self._duration = None
        self._state = 'stop'           # 'play' | 'pause' | 'stop'
        self._random = False
        self._repeat_mode = 'off'      # 'off' | 'repeat' | 'single'
        self._volume = int(cfg.getn('player', 'volume', default=100))
        self._last_played_folder = self._status_store.get('last_played_folder', '')

        self._second_swipe_action_dict = {
            'toggle': self.toggle,
            'play': self.play,
            'skip': self.next,
            'rewind': self.rewind,
            'replay': self.replay,
            'replay_if_stopped': self.replay_if_stopped,
        }
        self.second_swipe_action = None
        self._decode_2nd_swipe_option()

        self._end_of_playlist_next_action = utils.get_config_action(
            cfg, 'player', 'end_of_playlist_next_action', 'none',
            {'rewind': self.rewind, 'stop': self.stop, 'none': lambda: None}, logger)
        self._stopped_prev_action = utils.get_config_action(
            cfg, 'player', 'stopped_prev_action', 'prev',
            {'rewind': self.rewind, 'prev': self._prev_in_stopped_state, 'none': lambda: None}, logger)
        self._stopped_next_action = utils.get_config_action(
            cfg, 'player', 'stopped_next_action', 'next',
            {'rewind': self.rewind, 'next': self._next_in_stopped_state, 'none': lambda: None}, logger)

        self._sink = PortAudioSink()
        self._worker = threading.Thread(target=self._run, name='LocalAudioPlayback', daemon=True)
        self._worker.start()

        self._status_thread = multitimer.GenericEndlessTimerClass(
            'local_audio.timer_status', 0.25, self._publish_status)
        self._status_thread.start()

    # -- worker -----------------------------------------------------------------------------

    def _run(self):
        while True:
            with self._cv:
                while self._state != 'play' and not self._closing:
                    self._cv.wait()
                if self._closing:
                    return
                index = self._index
                position = self._position
            if not (0 <= index < len(self._queue)):
                with self._cv:
                    self._state = 'stop'
                continue
            self._abort.clear()
            ended_naturally = self._decode_track(self._queue[index], position)
            with self._cv:
                if self._closing:
                    return
                if not ended_naturally or self._state != 'play' or self._index != index:
                    # Interrupted by an external control call (stop/pause/next/prev/seek/new
                    # play_folder) -- it already set _index/_position/_state to what it wants.
                    continue
                if self._repeat_mode == 'single':
                    self._position = 0.0
                elif self._random and len(self._queue) > 1:
                    self._index = random.randrange(len(self._queue))
                    self._position = 0.0
                elif index + 1 < len(self._queue):
                    self._index = index + 1
                    self._position = 0.0
                elif self._repeat_mode == 'repeat':
                    self._index = 0
                    self._position = 0.0
                else:
                    self._state = 'stop'
                    self._position = 0.0
                    self._end_of_playlist_next_action()

    def _decode_track(self, path: str, start_position: float) -> bool:
        """Decode+play `path` from `start_position`. Returns True if it ran to completion (or
        failed to decode at all -- either way, the caller should move on), False if `_abort`
        interrupted it early."""
        logger.info(f"Playing '{path}' from {start_position:.3f}s")
        try:
            container = av.open(path)
        except Exception as e:
            logger.error(f"Could not open '{path}': {e.__class__.__name__}: {e}")
            return True
        self._duration = container.duration / 1_000_000 if container.duration else None
        try:
            try:
                return self._decode_loop(container, start_position)
            except Exception as e:
                # A single bad/corrupt file must not take down the whole playback worker --
                # treat it as "ended" so the queue moves on to the next track.
                logger.error(f"Error decoding '{path}', skipping: {e.__class__.__name__}: {e}")
                return True
        finally:
            container.close()

    def _decode_loop(self, container, start_position: float) -> bool:
        stream = container.streams.audio[0]
        resampler = AudioResampler(format='s16', layout='stereo', rate=SAMPLE_RATE)
        if start_position:
            try:
                container.seek(int(start_position * 1_000_000), backward=True)
            except Exception as e:
                logger.warning(f"Seek to {start_position:.3f}s failed, starting from the top: {e}")
        self._sink.open(SAMPLE_RATE, CHANNELS)
        try:
            for frame in container.decode(stream):
                if self._abort.is_set():
                    return False
                for rframe in resampler.resample(frame):
                    if self._abort.is_set():
                        return False
                    n = rframe.samples * CHANNELS * 2
                    data = bytes(rframe.planes[0])[:n]
                    self._sink.write(scale_volume(data, self._volume))
                    self._position += rframe.samples / SAMPLE_RATE
            return True
        finally:
            self._sink.close()

    def _jump_to(self, index: int, position: float = 0.0):
        with self._cv:
            self._index = index
            self._position = position
            self._state = 'play'
            self._abort.set()
            self._cv.notify_all()

    def _prev_in_stopped_state(self):
        self._jump_to(max(0, self._index - 1))

    def _next_in_stopped_state(self):
        pos = self._index + 1
        if pos > len(self._queue) - 1:
            return self._end_of_playlist_next_action()
        self._jump_to(pos)

    # -- second-swipe / config ---------------------------------------------------------------

    def _decode_2nd_swipe_option(self):
        # A custom action ('action: <module>.<action>') is run by the player module itself.
        action = str(cfg.getn('player', 'second_swipe_action', 'alias', default='none')).lower()
        if action not in [*self._second_swipe_action_dict, 'none', 'custom']:
            logger.error(f"Config player.second_swipe_action must be one of "
                         f"{[*self._second_swipe_action_dict, 'none']}. Ignore setting.")
        self.second_swipe_action = self._second_swipe_action_dict.get(action)

    # -- coordinator-facing surface -----------------------------------------------------------

    def set_status_callback(self, callback):
        self._status_callback = callback

    def set_active(self, active):
        self._active = active
        if active:
            self._status_callback(self._status_dict())

    def _publish_status(self):
        if self._active:
            self._status_callback(self._status_dict())

    def _status_dict(self):
        with self._cv:
            index, position, state, queue_len = self._index, self._position, self._state, len(self._queue)
            current_file = self._queue[index] if 0 <= index < queue_len else None
        return {
            'state': state,
            'song': str(index),
            'pos': str(index),
            'file': current_file,
            'elapsed': f'{position:.3f}',
            'duration': self._duration,
            'playlistlength': str(queue_len),
            'volume': str(self._volume),
            'random': '1' if self._random else '0',
            'repeat': '1' if self._repeat_mode in ('repeat', 'single') else '0',
            'single': '1' if self._repeat_mode == 'single' else '0',
            'provider': 'local_audio',
        }

    def get_player_type_and_version(self):
        return f"lauschkiste-local-audio (pyav {av.__version__}, sounddevice {sd.__version__})"

    def play(self):
        with self._cv:
            if not self._queue:
                logger.warning("play() called with nothing queued")
                return
            self._state = 'play'
            self._cv.notify_all()

    def stop(self):
        with self._cv:
            self._state = 'stop'
            self._position = 0.0
            self._abort.set()

    def pause(self, state: int = 1):
        with self._cv:
            if state:
                self._state = 'pause'
                self._abort.set()
            else:
                self._state = 'play'
                self._cv.notify_all()

    def prev(self):
        with self._cv:
            if self._state == 'stop':
                return self._stopped_prev_action()
            new_index = max(0, self._index - 1)
        self._jump_to(new_index)

    def next(self):
        with self._cv:
            if self._state == 'stop':
                return self._stopped_next_action()
            if self._index >= len(self._queue) - 1:
                return self._end_of_playlist_next_action()
            new_index = self._index + 1
        self._jump_to(new_index)

    def seek(self, new_time):
        with self._cv:
            self._position = float(new_time)
            self._abort.set()

    def rewind(self):
        """Re-start current playlist from the first track."""
        self._jump_to(0)

    def replay(self):
        """Re-start playing the last-played folder."""
        self.play_folder(self._last_played_folder)

    def toggle(self):
        with self._cv:
            if self._state == 'play':
                return self.pause(1)
            return self.pause(0)

    def replay_if_stopped(self):
        with self._cv:
            if self._state == 'stop':
                self.replay()

    def shuffle(self, option='toggle'):
        with self._cv:
            if option == 'toggle':
                self._random = not self._random
            elif option == 'enable':
                self._random = True
            elif option == 'disable':
                self._random = False
            else:
                logger.error(f"'{option}' does not exist for 'shuffle'")

    def repeat(self, option='toggle'):
        with self._cv:
            if option == 'toggle':
                self._repeat_mode = {'off': 'repeat', 'repeat': 'single', 'single': 'off'}[self._repeat_mode]
            elif option == 'toggle_repeat':
                self._repeat_mode = 'off' if self._repeat_mode == 'repeat' else 'repeat'
            elif option == 'toggle_repeat_single':
                self._repeat_mode = 'off' if self._repeat_mode == 'single' else 'single'
            elif option == 'enable_repeat':
                self._repeat_mode = 'repeat'
            elif option == 'enable_repeat_single':
                self._repeat_mode = 'single'
            elif option == 'disable':
                self._repeat_mode = 'off'
            else:
                logger.error(f"'{option}' does not exist for 'repeat'")

    def get_current_song(self, param):
        return self._status_dict()

    def map_filename_to_playlist_pos(self, filename):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def move(self):
        raise NotImplementedError

    def play_single(self, song_url):
        with self._cv:
            self._queue = [song_url]
            self._index = 0
            self._position = 0.0
            self._state = 'play'
            self._abort.set()
            self._cv.notify_all()

    def is_second_swipe(self, folder: str) -> bool:
        return self.second_swipe_action is not None and self._last_played_folder == folder

    def play_second_swipe(self):
        if self.second_swipe_action is not None:
            self.second_swipe_action()

    def get_folder_content(self, folder: str):
        plc = playlistgenerator.PlaylistCollector(lauschkiste.library.root())
        plc.get_directory_content(folder)
        return plc.playlist

    def play_folder(self, folder: str, recursive: bool = False) -> None:
        plc = playlistgenerator.PlaylistCollector(lauschkiste.library.root())
        plc.parse(folder, recursive)
        paths = list(plc)
        with self._cv:
            self._queue = paths
            self._last_played_folder = folder
            self._status_store['last_played_folder'] = folder
            if paths:
                self._index = 0
                self._position = 0.0
                self._state = 'play'
                self._abort.set()
                self._cv.notify_all()
            else:
                logger.warning(f"Folder '{folder}' has no playable content")
                self._index = -1
                self._state = 'stop'
        self._status_store.save_to_json()

    def play_files(self, paths):
        root = os.path.expanduser(lauschkiste.library.root() or '')
        queue = [p if os.path.isabs(p) or '://' in p else os.path.join(root, p) for p in paths]
        with self._cv:
            self._queue = queue
            self._last_played_folder = ''
            if queue:
                self._index = 0
                self._position = 0.0
                self._state = 'play'
                self._abort.set()
                self._cv.notify_all()
            else:
                self._index = -1
                self._state = 'stop'

    def queue_load(self, folder):
        pass

    def playerstatus(self):
        return self._status_dict()

    def playlistinfo(self):
        with self._cv:
            return [{'file': path, 'pos': str(i)} for i, path in enumerate(self._queue)]

    def list_all_dirs(self):
        base = os.path.expanduser(lauschkiste.library.root())
        result = []
        for root, _dirs, files in os.walk(base):
            for f in files:
                result.append({'file': os.path.relpath(os.path.join(root, f), base)})
        return result

    def get_volume(self):
        return self._volume

    def set_volume(self, volume):
        with self._cv:
            self._volume = max(0, min(100, int(volume)))
        return self._volume

    def exit(self):
        logger.debug("Exit routine of PlayerLocalAudio started")
        self._status_thread.close()
        with self._cv:
            self._closing = True
            self._abort.set()
            self._cv.notify_all()
        self._status_store.save_to_json()
        return self._worker
