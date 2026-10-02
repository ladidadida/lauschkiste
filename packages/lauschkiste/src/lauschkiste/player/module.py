"""The player core module: playback through registered backends, typed status events."""

import logging
import threading
from functools import partial
from typing import Any, Dict, List, Mapping, Optional

from pydantic import BaseModel

from lauschkiste.contract import CoreModule, OperationError, action, event, extension_point, query
from lauschkiste.player.backend import PlayerBackend
from lauschkiste.player.coordinator import PlayerCoordinator
from lauschkiste.player.status import ContentKind, PlaybackContext, PlayerStatus, status_from_backend

logger = logging.getLogger('lauschkiste.player')

DEFAULT_BACKEND = 'local_audio'


class VolumeLevel(BaseModel):
    volume: int


class QueueEntry(BaseModel):
    position: int
    file: str
    title: Optional[str] = None
    duration: Optional[float] = None


class BackendName(BaseModel):
    name: Optional[str] = None


class Player(CoreModule):
    """Playback of folders, songs and albums; backends plug in at ``player.backends``."""

    name = 'player'
    interface_version = '5.0'
    concurrency = 'threadsafe'
    requires = ('library',)

    status = event('status', PlayerStatus)
    backends = extension_point('backends', PlayerBackend)

    def __init__(self):
        self._ctx = None
        self._coordinator = PlayerCoordinator()
        self._configured_backend = DEFAULT_BACKEND
        self._metadata_lock = threading.Lock()
        self._metadata_file: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
        self._context: Optional[PlaybackContext] = None

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._configured_backend = ctx.config.get('backend', default=DEFAULT_BACKEND)
        self.backends.on_register(self._add_backend)

        from lauschkiste.player.backends.local_audio import PlayerLocalAudio
        self.backends.register('local_audio', PlayerLocalAudio())

    def _add_backend(self, name: str, backend: Any) -> None:
        backend.set_status_callback(partial(self._publish_status, name))
        is_configured = name == self._configured_backend
        self._coordinator.register_backend(name, backend, make_active=is_configured)
        if is_configured:
            self._coordinator.set_default_backend(name)

    def _publish_status(self, provider: str, raw: Mapping[str, Any]) -> None:
        self._ctx.publish(self.status, self._with_metadata(status_from_backend(raw, provider)))

    def _song_metadata(self, file: str) -> Dict[str, Any]:
        """Library metadata and cover of ``file``, looked up once per song."""
        with self._metadata_lock:
            if file == self._metadata_file:
                return self._metadata
        library = self._ctx.modules.library
        metadata: Dict[str, Any] = {}
        try:
            song = library.get_song(file)
            if song is not None:
                metadata = song.model_dump(include={'title', 'artist', 'album', 'albumartist', 'track', 'duration'})
            metadata['cover_url'] = library.get_song_cover(file).cover_url
        except Exception as error:
            logger.debug(f"No library metadata for '{file}': {error}")
        with self._metadata_lock:
            self._metadata_file, self._metadata = file, metadata
        return metadata

    def _with_metadata(self, status: PlayerStatus) -> PlayerStatus:
        if not status.file:
            return status
        update = {key: value for key, value in self._song_metadata(status.file).items()
                  if value is not None and getattr(status, key) is None}
        with self._metadata_lock:
            update['context'] = self._context
        return status.model_copy(update=update)

    def _set_context(self, kind: ContentKind, title: Optional[str], action: str, args: Dict[str, Any]) -> None:
        context = PlaybackContext(kind=kind, title=title, action=action,
                                  args={key: value for key, value in args.items() if value is not None})
        with self._metadata_lock:
            self._context = context

    def ready(self) -> None:
        if self._configured_backend not in self.backends:
            logger.error(f"Configured player backend '{self._configured_backend}' is not available "
                         f"(registered: {self.backends.names()}); is its plugin enabled?")
        self._configure_second_swipe()

    def _configure_second_swipe(self) -> None:
        entry = self._ctx.config.get('second_swipe_action', default=None)
        if not isinstance(entry, dict):
            return
        if 'action' not in entry and entry.get('alias', 'custom') != 'custom':
            return
        action = self._ctx.actions.bind(entry, 'player.second_swipe_action', logger)
        if action is not None:
            self._coordinator.set_second_swipe_action(action)

    def stop(self) -> List[threading.Thread]:
        results = self._coordinator.exit()
        return [r for r in results if isinstance(r, threading.Thread)]

    # -- transport ------------------------------------------------------------------------------

    @action(path='/play')
    def play(self) -> None:
        """Start or resume playback."""
        self._coordinator.play()

    @action(path='/pause')
    def pause(self, state: int = 1) -> None:
        """Pause (state=1) or resume (state=0)."""
        self._coordinator.pause(state)

    @action(path='/toggle')
    def toggle(self) -> None:
        """Toggle between play and pause."""
        self._coordinator.toggle()

    @action(path='/next')
    def next(self) -> None:
        """Skip to the next song."""
        self._coordinator.next()

    @action(path='/prev')
    def prev(self) -> None:
        """Go back to the previous song."""
        self._coordinator.prev()

    @action(name='stop', path='/stop')
    def stop_playback(self) -> None:
        """Stop playback."""
        self._coordinator.stop()

    @action(path='/seek')
    def seek(self, position: float) -> None:
        """Jump to a position (seconds) in the current song."""
        self._coordinator.seek(position)

    @action(path='/shuffle')
    def shuffle(self, option: str = 'toggle') -> None:
        """Shuffle mode: 'toggle', 'enable' or 'disable'."""
        self._coordinator.shuffle(option)

    @action(path='/repeat')
    def repeat(self, option: str = 'toggle') -> None:
        """Repeat mode: 'toggle', 'enable', 'enable_repeat_single' or 'disable'."""
        self._coordinator.repeat(option)

    @action(path='/jump')
    def jump(self, position: int) -> None:
        """Play the entry at ``position`` of the queue."""
        self._coordinator.jump(position)

    @action(path='/speed')
    def set_speed(self, speed: float) -> None:
        """Playback speed (0.5 to 2.0) of audiobooks and podcasts; music and radio always play at 1.0."""
        try:
            self._coordinator.set_speed(speed)
        except NotImplementedError as error:
            raise OperationError(501, 'not_supported', str(error)) from None

    @query(path='/queue')
    def get_queue(self) -> List[QueueEntry]:
        """The queue with title and duration from the library."""
        library = self._ctx.modules.library
        entries = []
        for position, item in enumerate(self._coordinator.playlistinfo() or []):
            file = str(item.get('file') or '')
            song = None
            if file and '://' not in file:
                try:
                    song = library.get_song(file)
                except Exception:
                    song = None
            entries.append(QueueEntry(position=position, file=file, title=(song.title if song else None)
                                      or item.get('title'), duration=song.duration if song else None))
        return entries

    @action(path='/stop-after-current')
    def stop_after_current(self, enabled: bool = True) -> None:
        """Stop once the current song, chapter or episode has played to its end (sleep timer)."""
        self._coordinator.stop_after_current(enabled)
        self._publish_status(self._coordinator.get_active_backend() or '', self._coordinator.playerstatus())

    @action(path='/rewind')
    def rewind(self) -> None:
        """Restart the playlist from its first song."""
        self._coordinator.rewind()

    @action(path='/replay')
    def replay(self) -> None:
        """Replay the current folder from the start."""
        self._coordinator.replay()

    @action(path='/replay-if-stopped')
    def replay_if_stopped(self) -> None:
        """Replay the current folder if playback has stopped."""
        self._coordinator.replay_if_stopped()

    @action(path='/resume')
    def resume(self) -> None:
        """Resume the last played folder where it stopped."""
        self._coordinator.resume()

    # -- content --------------------------------------------------------------------------------

    @action(path='/folder')
    def play_folder(self, folder: str, recursive: bool = False) -> None:
        """Play a folder of the music library."""
        self._set_context('music', folder.rstrip('/').rsplit('/', 1)[-1], 'player.play_folder',
                          {'folder': folder, 'recursive': recursive or None})
        self._coordinator.play_folder(folder, recursive)

    @action()
    def play_card(self, folder: str, recursive: bool = False) -> None:
        """Play a folder; a second swipe of the same card runs the second-swipe action."""
        self._set_context('music', folder.rstrip('/').rsplit('/', 1)[-1], 'player.play_folder',
                          {'folder': folder, 'recursive': recursive or None})
        self._coordinator.play_card(folder, recursive)

    @action(path='/song')
    def play_single(self, song_url: str, provider: Optional[str] = None) -> None:
        """Play a single song."""
        self._set_context('music', None, 'player.play_single', {'song_url': song_url, 'provider': provider})
        self._coordinator.play_single(song_url, provider)

    @action(path='/album')
    def play_album(self, albumartist: str, album: str, content_uri: Optional[str] = None,
                   provider: Optional[str] = None) -> None:
        """Play an album of the library or of a backend's own catalog (``provider``)."""
        self._set_context('music', album, 'player.play_album', {'albumartist': albumartist, 'album': album,
                                                                 'content_uri': content_uri, 'provider': provider})
        if provider and provider in self.backends:
            self._coordinator.play_album(albumartist, album, content_uri, provider)
            return
        songs = self._ctx.modules.library.list_songs(albumartist, album, content_uri, provider)
        if not songs:
            raise OperationError(404, 'unknown_album', f"No songs found for '{album}' by '{albumartist}'")
        self._coordinator.play_files([song.file for song in songs])

    @action(path='/files')
    def play_files(self, files: List[str], start: int = 0, position: float = 0.0, ordered: bool = False,
                   context: Optional[PlaybackContext] = None) -> None:
        """Play files of the library (or URLs), from ``position`` seconds into the file at index ``start``;
        ``ordered`` plays them in order, ignoring shuffle and repeat. ``context`` says what is played
        (shown by the web app; without it, music)."""
        if not files:
            raise OperationError(422, 'no_files', 'No files to play')
        with self._metadata_lock:
            self._context = PlaybackContext.model_validate(context) if context else PlaybackContext(kind='music')
        self._coordinator.play_files(files, start, position, ordered)

    @action(path='/queue')
    def queue_load(self, folder: str) -> None:
        """Load a folder into the queue without playing it."""
        self._coordinator.queue_load(folder)

    @action(path='/update')
    def update(self) -> Any:
        """Rescan the music library of the default backend."""
        return self._coordinator.update()

    @action(path='/update-wait')
    def update_wait(self) -> Any:
        """Rescan the music library and wait for it to finish."""
        return self._coordinator.update_wait()

    # -- status and volume ----------------------------------------------------------------------

    @query(path='/status')
    def playerstatus(self) -> PlayerStatus:
        """Current player status."""
        name = self._coordinator.get_active_backend()
        return self._with_metadata(status_from_backend(self._coordinator.playerstatus(), name or ''))

    @query(path='/volume')
    def get_volume(self) -> VolumeLevel:
        """Current playback volume of the active backend."""
        return VolumeLevel(volume=int(self._coordinator.get_volume()))

    @action(method='PUT', path='/volume')
    def set_volume(self, volume: int) -> VolumeLevel:
        """Set the playback volume of the active backend."""
        return VolumeLevel(volume=int(self._coordinator.set_volume(volume)))

    @query(path='/playlist')
    def playlistinfo(self) -> List[Dict[str, Any]]:
        """The current queue."""
        return self._coordinator.playlistinfo()

    @query(path='/current-song')
    def get_current_song(self, param: Optional[str] = None) -> Any:
        """Details of the current song."""
        return self._coordinator.get_current_song(param)

    @query(path='/type')
    def get_player_type_and_version(self) -> str:
        """Type and version of the active backend."""
        return self._coordinator.get_player_type_and_version()

    # -- backends -------------------------------------------------------------------------------

    @query(path='/backends')
    def list_backends(self) -> List[str]:
        """Registered backends."""
        return self._coordinator.list_backends()

    @query(path='/backends/active')
    def get_active_backend(self) -> BackendName:
        """The backend playing right now."""
        return BackendName(name=self._coordinator.get_active_backend())

    @query(path='/backends/default')
    def get_default_backend(self) -> BackendName:
        """The backend used for content without an explicit provider."""
        return BackendName(name=self._coordinator.get_default_backend())

    @action(method='PUT', path='/backends/active')
    def select_backend(self, name: str) -> BackendName:
        """Stop the current backend and switch to another one."""
        return BackendName(name=self._coordinator.select_backend(name))
