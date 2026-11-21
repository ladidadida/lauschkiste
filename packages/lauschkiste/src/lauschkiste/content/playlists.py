"""The playlists core module: own lists of songs from the music library, made in the web app.

Each playlist is an extended M3U file in ``playlists.folder`` (``playlists`` in the home): its name is the
playlist id, ``#PLAYLIST:`` holds the title, every other line a song (a path in the library or a stream URL).
Renaming a playlist keeps its id, so cards keep playing it.
"""

import logging
import re
import threading
import unicodedata
from pathlib import Path
from typing import Any, List, Optional, Tuple

from pydantic import BaseModel

import lauschkiste.common.paths
import lauschkiste.common.statefile as statefile
import lauschkiste.content.library
from lauschkiste.contract import CoreModule, OperationError, action, event, query
from lauschkiste.content.library.files import AUDIO_EXTENSIONS, LibraryError, resolve_library_path

logger = logging.getLogger('lauschkiste.content.playlists')

DEFAULT_FOLDER = 'playlists'
SUFFIX = '.m3u'
ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]*$')
MAX_ENTRIES = 5000


class PlaylistSummary(BaseModel):
    id: str
    title: str
    tracks: int
    #: None when the duration of a song is not known
    duration: Optional[float] = None
    cover_url: Optional[str] = None


class PlaylistEntry(BaseModel):
    #: path in the library or stream URL
    file: str
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: Optional[float] = None
    #: no longer in the library; skipped when the playlist plays
    missing: bool = False


class Playlist(BaseModel):
    id: str
    title: str
    entries: List[PlaylistEntry]


class PlaylistsChanged(BaseModel):
    playlists: List[PlaylistSummary]


def _slug(title: str) -> str:
    text = unicodedata.normalize('NFKD', title.replace('ß', 'ss')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'playlist'


def _is_url(entry: str) -> bool:
    return entry.startswith(('http://', 'https://'))


def parse_m3u(text: str, fallback_title: str) -> Tuple[str, List[str]]:
    """Title and entries of an M3U playlist."""
    title, entries = None, []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('#PLAYLIST:'):
            title = line[len('#PLAYLIST:'):].strip() or None
        elif line and not line.startswith('#'):
            entries.append(line)
    return title or fallback_title, entries


def render_m3u(title: str, entries: List[str]) -> str:
    return '\n'.join(['#EXTM3U', f'#PLAYLIST:{title}', *entries]) + '\n'


class Playlists(CoreModule):
    """Playlists: own lists of songs from the library; create, change, play, put on a card."""

    name = 'playlists'
    interface_version = '1.0'
    concurrency = 'threadsafe'
    requires = ('library', 'player')

    changed = event('changed', PlaylistsChanged)

    def __init__(self):
        self._ctx: Any = None
        self._folder = Path(DEFAULT_FOLDER)
        self._lock = threading.Lock()

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._folder = lauschkiste.common.paths.resolve(ctx.config.get('folder', default=DEFAULT_FOLDER))
        self._folder.mkdir(parents=True, exist_ok=True)

    def ready(self) -> None:
        self._publish()

    def stop(self):
        return []

    # -- files ----------------------------------------------------------------------------------

    def _path(self, playlist: str) -> Path:
        if not ID_RE.match(playlist or ''):
            raise OperationError(422, 'invalid_playlist', f"Invalid playlist id '{playlist}'")
        return self._folder / f'{playlist}{SUFFIX}'

    def _read(self, playlist: str) -> Tuple[str, List[str]]:
        path = self._path(playlist)
        try:
            return parse_m3u(path.read_text(encoding='utf-8', errors='replace'), playlist)
        except FileNotFoundError:
            raise OperationError(404, 'unknown_playlist', f"No playlist '{playlist}'") from None

    def _write(self, playlist: str, title: str, entries: List[str]) -> None:
        try:
            statefile.write_text(self._path(playlist), render_m3u(title, entries))
        except OSError as error:
            raise OperationError(500, 'not_saved', f"Could not save the playlist: {error}") from None
        self._publish()

    def _ids(self) -> List[str]:
        try:
            return sorted(path.stem for path in self._folder.glob(f'*{SUFFIX}') if ID_RE.match(path.stem))
        except OSError:
            return []

    def _check_entries(self, files: List[str]) -> List[str]:
        if len(files) > MAX_ENTRIES:
            raise OperationError(422, 'too_many_entries', f"A playlist holds at most {MAX_ENTRIES} songs")
        root = lauschkiste.content.library.root()
        result = []
        for file in files:
            file = file.strip()
            if _is_url(file):
                result.append(file)
                continue
            try:
                path = resolve_library_path(root, file, allow_root=False)
            except (LibraryError, OSError):
                raise OperationError(422, 'invalid_entry', f"'{file}' is not in the library") from None
            if path.suffix.lower() not in AUDIO_EXTENSIONS:
                raise OperationError(422, 'invalid_entry', f"'{file}' is not an audio file")
            result.append(path.relative_to(Path(root).expanduser().resolve()).as_posix())
        return result

    # -- metadata -------------------------------------------------------------------------------

    def _entry(self, file: str) -> PlaylistEntry:
        if _is_url(file):
            return PlaylistEntry(file=file, title=file)
        song = None
        try:
            song = self._ctx.modules.library.get_song(file)
        except Exception as error:
            logger.debug(f"No library metadata for '{file}': {error}")
        name = file.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        if song is None:
            return PlaylistEntry(file=file, title=name, missing=True)
        return PlaylistEntry(file=file, title=song.title or name, artist=song.artist, album=song.album,
                             duration=song.duration)

    def _cover(self, entries: List[PlaylistEntry]) -> Optional[str]:
        first = next((entry.file for entry in entries if not entry.missing and not _is_url(entry.file)), None)
        if first is None:
            return None
        try:
            return self._ctx.modules.library.get_song_cover(first).cover_url
        except Exception:
            return None

    def _summary(self, playlist: str) -> PlaylistSummary:
        title, files = self._read(playlist)
        entries = [self._entry(file) for file in files]
        durations = [entry.duration for entry in entries]
        duration = None if any(value is None for value in durations) else sum(value or 0.0 for value in durations)
        return PlaylistSummary(id=playlist, title=title, tracks=len(entries), duration=duration,
                               cover_url=self._cover(entries))

    def _list(self) -> List[PlaylistSummary]:
        result = []
        for playlist in self._ids():
            try:
                result.append(self._summary(playlist))
            except OperationError as error:
                logger.warning(f"Skipping playlist '{playlist}': {error.message}")
        return sorted(result, key=lambda entry: entry.title.casefold())

    def _publish(self) -> None:
        self._ctx.publish(self.changed, PlaylistsChanged(playlists=self._list()))

    # -- operations -----------------------------------------------------------------------------

    @query(path='/')
    def list_playlists(self) -> List[PlaylistSummary]:
        """All playlists, by title."""
        return self._list()

    @query(path='/playlist')
    def get_playlist(self, playlist: str) -> Playlist:
        """A playlist with its songs."""
        title, files = self._read(playlist)
        return Playlist(id=playlist, title=title, entries=[self._entry(file) for file in files])

    @action(path='/', status_code=201)
    def create(self, title: str, files: Optional[List[str]] = None) -> Playlist:
        """Create a playlist; its id is derived from the title."""
        title = title.strip()
        if not title:
            raise OperationError(422, 'invalid_title', 'A playlist needs a title')
        entries = self._check_entries(files or [])
        with self._lock:
            base = _slug(title)
            playlist, number = base, 2
            while self._path(playlist).exists():
                playlist, number = f'{base}-{number}', number + 1
            self._write(playlist, title, entries)
        return self.get_playlist(playlist)

    @action(method='PUT', path='/{playlist}')
    def save(self, playlist: str, title: Optional[str] = None, files: Optional[List[str]] = None) -> Playlist:
        """Change title and songs (in order) of a playlist; what is left out stays as it is."""
        with self._lock:
            old_title, old_files = self._read(playlist)
            if title is not None and not title.strip():
                raise OperationError(422, 'invalid_title', 'A playlist needs a title')
            entries = self._check_entries(files) if files is not None else old_files
            self._write(playlist, title.strip() if title is not None else old_title, entries)
        return self.get_playlist(playlist)

    @action()
    def add(self, playlist: str, files: List[str]) -> Playlist:
        """Add songs to the end of a playlist."""
        with self._lock:
            title, old_files = self._read(playlist)
            self._write(playlist, title, old_files + self._check_entries(files))
        return self.get_playlist(playlist)

    @action(method='DELETE', path='/{playlist}')
    def delete(self, playlist: str) -> None:
        """Delete a playlist. Cards playing it stop working."""
        with self._lock:
            path = self._path(playlist)
            if not path.exists():
                raise OperationError(404, 'unknown_playlist', f"No playlist '{playlist}'")
            path.unlink()
        self._publish()

    @action()
    def play(self, playlist: str, start: int = 0) -> None:
        """Play a playlist from song ``start`` on (shuffle and repeat as set in the player); songs no longer in
        the library are skipped."""
        title, files = self._read(playlist)
        library = self._ctx.modules.library
        playable = [(index, file) for index, file in enumerate(files)
                    if _is_url(file) or library.get_song(file) is not None]
        if not playable:
            raise OperationError(422, 'empty_playlist', f"The playlist '{title}' has no songs to play")
        first = next((number for number, (index, _file) in enumerate(playable) if index >= start), 0)
        self._ctx.modules.player.play_files([file for _index, file in playable], start=first, context={
            'kind': 'music', 'title': title, 'action': 'playlists.play', 'args': {'playlist': playlist}})
