"""The player core module: playback through registered backends, typed status events."""

import logging
import threading
import time
from functools import partial
from typing import Any, Dict, List, Literal, Mapping, Optional

from pydantic import BaseModel, Field

import lauschkiste.common.paths
import lauschkiste.common.statefile as statefile
import lauschkiste.content.resume
from lauschkiste.contract import CoreModule, OperationError, action, event, extension_point, query
from lauschkiste.player.backend import LevelMeter, PlayerBackend, Resolver
from lauschkiste.player.coordinator import PlayerCoordinator
from lauschkiste.player.status import ContentKind, PlaybackContext, PlayerStatus, status_from_backend

logger = logging.getLogger('lauschkiste.player')

DEFAULT_BACKEND = 'local_audio'
SESSION_FILE = 'settings/player_session.json'
SESSION_SAVE_SEC = 30.0
#: Content whose module keeps its own position: restored through its action
TRACKED_KINDS = ('audiobook', 'podcast')


SECOND_SWIPE_ACTIONS = {'toggle': 'player.toggle', 'play': 'player.play', 'skip': 'player.next',
                        'rewind': 'player.rewind'}


class SecondSwipe(BaseModel):
    alias: Literal['toggle', 'play', 'skip', 'rewind', 'none'] = Field(
        'none', title='Same card placed again',
        description='What a folder card does when it is placed again while its folder plays')


class PlayerSettings(BaseModel):
    backend: str = Field(DEFAULT_BACKEND, title='Player backend',
                         description="'local_audio' plays directly")
    volume: int = Field(100, ge=0, le=100, title='Player volume',
                        description='Of the local_audio backend, on top of the system volume; cubic like PulseAudio')
    second_swipe_action: SecondSwipe = Field(default_factory=SecondSwipe, title='Second swipe')


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
    interface_version = '8.0'
    concurrency = 'threadsafe'
    requires = ('library',)

    settings = PlayerSettings
    status = event('status', PlayerStatus)
    backends = extension_point('backends', PlayerBackend)
    level_meters = extension_point('level_meters', LevelMeter)
    resolvers = extension_point('resolvers', Resolver)

    def __init__(self):
        self._ctx = None
        self._coordinator = PlayerCoordinator()
        self._configured_backend = DEFAULT_BACKEND
        self._metadata_lock = threading.Lock()
        self._metadata_file: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
        self._context: Optional[PlaybackContext] = None
        self._ordered = False
        self._session_path: Any = None
        self._session: Dict[str, Any] = {}
        self._session_lock = threading.Lock()
        self._session_restored = False
        self._session_key: Any = None
        self._session_saved_at = 0.0
        self._session_worker: Any = None
        self._loading_thread: Optional[int] = None

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._configured_backend = ctx.config.get('backend', default=DEFAULT_BACKEND)
        self._session_path = lauschkiste.common.paths.resolve(SESSION_FILE)
        self._session = statefile.read_json(self._session_path)
        self._session_worker = ctx.executor('session')
        self.backends.on_register(self._add_backend)
        self.level_meters.on_register(lambda name, meter: self._connect_levels())

        from lauschkiste.player.backends.local_audio import PlayerLocalAudio
        self.backends.register('local_audio', PlayerLocalAudio())

    def _resolve(self, url: str):
        """(url, headers) to open for a track URL; the resolver registered for its scheme decides."""
        scheme = url.split('://', 1)[0]
        if scheme in self.resolvers:
            return self.resolvers.get(scheme).resolve(url)
        return url, {}

    def _add_backend(self, name: str, backend: Any) -> None:
        if hasattr(backend, 'set_resolver'):
            backend.set_resolver(self._resolve)
        backend.set_status_callback(partial(self._publish_status, name))
        self._connect_levels()
        is_configured = name == self._configured_backend
        self._coordinator.register_backend(name, backend, make_active=is_configured)
        if is_configured:
            self._coordinator.set_default_backend(name)

    def _connect_levels(self) -> None:
        """Backends that can measure their output level report it once a level meter is registered."""
        callback = self._dispatch_level if self.level_meters.names() else None
        for _, backend in self.backends.items():
            if hasattr(backend, 'set_level_callback'):
                backend.set_level_callback(callback)

    def _dispatch_level(self, left: float, right: float, delay: float) -> None:
        for name, meter in self.level_meters.items():
            try:
                meter.level(left, right, delay)
            except Exception as error:
                logger.debug(f"Level meter '{name}' failed: {error}")

    def _publish_status(self, provider: str, raw: Mapping[str, Any]) -> None:
        status = self._with_metadata(status_from_backend(raw, provider))
        self._ctx.publish(self.status, status)
        self._note_session(status)

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
        if self._context and self._context.image and not update.get('cover_url') and not status.cover_url:
            update['cover_url'] = self._context.image
        if self._context and self._context.cover:
            update['cover_url'] = self._context.cover
        if self._context and self._context.titles:
            title = self._context.titles.get(lauschkiste.content.resume.relative(status.file) or '')
            if title:
                update['title'] = title
        return status.model_copy(update=update)

    def _set_context(self, kind: ContentKind, title: Optional[str], action: str, args: Dict[str, Any]) -> None:
        context = PlaybackContext(kind=kind, title=title, action=action,
                                  args={key: value for key, value in args.items() if value is not None})
        with self._metadata_lock:
            self._context = context
            self._ordered = False

    def ready(self) -> None:
        if self._configured_backend not in self.backends:
            logger.error(f"Configured player backend '{self._configured_backend}' is not available "
                         f"(registered: {self.backends.names()}); is its plugin enabled?")
        self._configure_second_swipe()
        self._session_worker.submit(self._restore_session)

    def _configure_second_swipe(self) -> None:
        entry = self._ctx.config.get('second_swipe_action', default=None)
        if not isinstance(entry, dict):
            return
        if 'action' not in entry:
            action_id = SECOND_SWIPE_ACTIONS.get(str(entry.get('alias', 'none')).lower())
            if action_id is None:
                return
            entry = {'action': action_id}
        action = self._ctx.actions.bind(entry, 'player.second_swipe_action', logger)
        if action is not None:
            self._coordinator.set_second_swipe_action(action)

    def stop(self) -> List[threading.Thread]:
        if self._session_restored:
            try:
                self._session_worker.submit(self._save_session, self.playerstatus()).result(timeout=5)
            except Exception as error:
                logger.error(f"Could not save what plays: {error}")
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
            self._ordered = ordered
        if self._loading_thread == threading.get_ident():
            self._coordinator.load_files(files, start, position, ordered)
        else:
            self._coordinator.play_files(files, start, position, ordered)

    # -- session: what plays is loaded again after a restart ------------------------------------

    def _note_session(self, status: PlayerStatus) -> None:
        """Save what plays when it changed, and every SESSION_SAVE_SEC while it plays."""
        with self._session_lock:
            if not self._session_restored:
                return
            key = (status.state, status.file, status.context)
            due = status.state == 'play' and time.monotonic() - self._session_saved_at >= SESSION_SAVE_SEC
            if key == self._session_key and not due:
                return
            self._session_key = key
            self._session_saved_at = time.monotonic()
        self._session_worker.submit(self._save_session, status)

    def _save_session(self, status: PlayerStatus) -> None:
        with self._metadata_lock:
            ordered = self._ordered
        files = [str(item.get('file') or '') for item in self._coordinator.playlistinfo() or []]
        session = {'context': status.context.model_dump(mode='json') if status.context else None,
                   'files': files, 'index': status.position or 0, 'elapsed': status.elapsed, 'ordered': ordered}
        try:
            statefile.write_json(self._session_path, session)
        except OSError as error:
            logger.error(f"Could not save what plays to '{self._session_path}': {error}")

    def _restore_session(self) -> None:
        """Load what played before the restart, paused; content with its own position through its action."""
        session, self._session = self._session, {}
        try:
            files = [str(file) for file in session.get('files') or []]
            if not files or self._coordinator.playerstatus().get('state') != 'stop' \
                    or self._coordinator.playlistinfo():
                return
            context = PlaybackContext.model_validate(session['context']) if session.get('context') else None
            self._loading_thread = threading.get_ident()
            if context and context.kind in TRACKED_KINDS and context.action:
                self._ctx.actions.call(context.action, context.args)
            else:
                elapsed = 0.0 if context and context.kind == 'radio' else float(session.get('elapsed') or 0.0)
                self.play_files(files, int(session.get('index') or 0), elapsed, bool(session.get('ordered')),
                                context)
            logger.info(f"Loaded what played before: {context.title if context and context.title else files[0]}")
        except NotImplementedError:
            logger.debug('The player backend cannot load without playing')
        except Exception as error:
            logger.warning(f"Could not load what played before: {error.__class__.__name__}: {error}")
        finally:
            self._loading_thread = None
            with self._session_lock:
                self._session_restored = True

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
