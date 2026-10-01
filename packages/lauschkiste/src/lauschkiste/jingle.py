"""The jingle core module: startup and shutdown sounds, and playing a sound on demand."""

import logging
import signal
import threading
from pathlib import Path

import lauschkiste.paths
from lauschkiste.audio_output import play_file
from lauschkiste.contract import CoreModule, OperationError, action

logger = logging.getLogger('jb.jingle')

SHUTDOWN_SOUND_TIMEOUT = 3.0
DEFAULT_SOUNDS = {'startup_sound': 'startupsound.wav', 'shutdown_sound': 'shutdownsound.wav'}


def sound_path(value: str, key: str = 'startup_sound') -> Path:
    """``default`` or ``resources/audio/<file>``: a packaged sound; anything else: a path below the home."""
    if value == 'default':
        return lauschkiste.paths.resource('audio', DEFAULT_SOUNDS[key])
    parts = tuple(part for part in Path(value).parts if part != '..')
    if parts[:2] == ('resources', 'audio'):
        return lauschkiste.paths.resource('audio', *parts[2:])
    return lauschkiste.paths.resolve(value)


class Jingle(CoreModule):
    """Plays the startup sound when ready and the shutdown sound when stopping."""

    name = 'jingle'
    interface_version = '1.0'
    concurrency = 'threadsafe'

    def __init__(self):
        self._ctx = None
        self._executor = None
        self._stopping = threading.Event()

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._executor = ctx.executor('sound')

    def _volume(self) -> int:
        volume = self._ctx.config.get('volume', default=None)
        return 100 if volume is None else max(0, min(100, int(volume)))

    def _play(self, sound: str, key: str = 'startup_sound') -> None:
        try:
            play_file(str(sound_path(sound, key)), self._volume(), should_stop=self._stopping.is_set)
        except Exception as error:
            logger.error(f"Could not play '{sound}': {error.__class__.__name__}: {error}")

    def ready(self) -> None:
        sound = self._ctx.config.get('startup_sound', default='default')
        if sound:
            self._executor.submit(self._play, sound)

    def stop(self):
        sound = self._ctx.config.get('shutdown_sound', default='default')
        from lauschkiste.daemon import shutdown_signal
        if sound and shutdown_signal() != signal.SIGINT:
            done = threading.Thread(target=self._play, args=(sound, 'shutdown_sound'), name='jingle.shutdown', daemon=True)
            done.start()
            done.join(SHUTDOWN_SOUND_TIMEOUT)
        self._stopping.set()
        return []

    @action()
    def play(self, sound: str) -> None:
        """Play a sound file (path relative to the jukebox directory or absolute)."""
        if not sound_path(sound).is_file():
            raise OperationError(404, 'unknown_sound', f"Sound file '{sound}' not found")
        self._executor.submit(self._play, sound)
