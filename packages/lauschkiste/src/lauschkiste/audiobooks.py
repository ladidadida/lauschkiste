"""The audiobooks core module: audiobooks in ``library/audiobooks``, continued where they stopped.

Each folder directly below ``audiobooks`` is one audiobook, its files are the chapters in file name
order. The position is kept per audiobook in ``audiobooks.state_file``; chapters play in order,
regardless of shuffle and repeat.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field

import lauschkiste.paths
from lauschkiste.contract import CoreModule, OperationError, action, extension_point, query
from lauschkiste.resume import ResumeTracker

logger = logging.getLogger('lauschkiste.audiobooks')

LOCAL = 'local'

DEFAULT_STATE_FILE = 'settings/audiobooks.json'


class AudiobookSource(Protocol):
    """Audiobooks from somewhere else (e.g. a server), registered at ``audiobooks.sources`` under the
    source id. Their position is kept by the source, not in ``audiobooks.state_file``."""

    def list_books(self) -> List[Dict[str, Any]]:
        """The books as mappings with the fields of :class:`Audiobook` (``source`` is added)."""

    def files(self, book: str) -> List[str]:
        """The track URLs to play, in order; raises :class:`OperationError` if there is no such book."""

    def title(self, book: str) -> str:
        """The title shown while it plays."""

    def position(self, book: str) -> Any:
        """A ``lauschkiste.resume.PositionStore`` for the book."""

    def set_finished(self, book: str, finished: bool) -> None:
        """Mark the book finished or not (either way it starts from the beginning next time)."""


class AudiobookSettings(BaseModel):
    rewind_sec: float = Field(10, ge=0, le=120, title='Go back when continuing (seconds)')


class Audiobook(BaseModel):
    book: str
    title: str
    chapters: int
    duration: Optional[float] = None
    chapter: int = 0
    elapsed: float = 0.0
    listened: float = 0.0
    finished: bool = False
    cover_url: Optional[str] = None
    source: str = LOCAL


def natural_key(text: str):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r'(\d+)', text)]


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class Audiobooks(CoreModule):
    """Audiobooks: play, continue, start over, mark as finished."""

    name = 'audiobooks'
    interface_version = '2.0'
    concurrency = 'threadsafe'
    requires = ('library', 'player')
    settings = AudiobookSettings
    sources = extension_point('sources', AudiobookSource)

    def __init__(self):
        self._ctx: Any = None
        self._resume: Any = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._resume = ResumeTracker(
            ctx, lauschkiste.paths.resolve(ctx.config.get('state_file', default=DEFAULT_STATE_FILE)),
            rewind_sec=float(ctx.config.get('rewind_sec', default=10)),
            save_interval_sec=float(ctx.config.get('save_interval_sec', default=10)))
        self._resume.start()

    def stop(self):
        self._resume.stop()
        return []

    def settings_changed(self, changed):
        if 'rewind_sec' in changed:
            self._resume.configure(float(changed['rewind_sec']))
        return True

    # -- library --------------------------------------------------------------------------------

    def _songs(self, book: Optional[str] = None):
        folder = lauschkiste.paths.AUDIOBOOKS_DIR + (f'/{book}' if book else '')
        return self._ctx.modules.library.list_folder_songs(folder)

    def _chapter_files(self, book: str) -> List[str]:
        if not book or '/' in book or book in ('.', '..'):
            raise OperationError(422, 'invalid_audiobook', f"Invalid audiobook name '{book}'")
        files = sorted((song.file for song in self._songs(book)), key=natural_key)
        if not files:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}' in the library")
        return files

    # -- operations -----------------------------------------------------------------------------

    @query(path='/')
    def list_books(self) -> List[Audiobook]:
        """All audiobooks with their progress."""
        books: Dict[str, list] = {}
        prefix = lauschkiste.paths.AUDIOBOOKS_DIR + '/'
        for song in self._songs():
            parts = song.file[len(prefix):].split('/', 1)
            if len(parts) == 2:
                books.setdefault(parts[0], []).append(song)
        positions = self._resume.entries()
        result = []
        for book in sorted(books, key=natural_key):
            songs = sorted(books[book], key=lambda song: natural_key(song.file))
            files = [song.file for song in songs]
            durations = [song.duration or 0.0 for song in songs]
            total = sum(durations) if all(song.duration for song in songs) else None
            entry = positions.get(book, {})
            finished = bool(entry.get('finished'))
            chapter = files.index(entry['file']) if entry.get('file') in files else 0
            elapsed = _number(entry.get('elapsed')) if entry.get('file') in files else 0.0
            listened = total if finished and total else sum(durations[:chapter]) + elapsed
            try:
                cover_url = self._ctx.modules.library.get_song_cover(files[0]).cover_url
            except Exception:
                cover_url = None
            result.append(Audiobook(book=book, title=songs[0].album or book, chapters=len(files), duration=total,
                                    chapter=chapter, elapsed=elapsed, listened=listened, finished=finished,
                                    cover_url=cover_url))
        for source, implementation in self.sources.items():
            try:
                result.extend(Audiobook(**{**entry, 'source': source}) for entry in implementation.list_books())
            except Exception as error:
                logger.warning(f"Audiobooks of source '{source}' are not available: {error}")
        return result

    def _context(self, book: str, source: str = LOCAL) -> Dict[str, Any]:
        args = {'book': book} if source == LOCAL else {'book': book, 'source': source}
        if source != LOCAL:
            title = self._source(source).title(book)
        else:
            songs = self._songs(book)
            title = next((song.album for song in songs if song.album), None) or book
        return {'kind': 'audiobook', 'title': title, 'action': 'audiobooks.play', 'args': args}

    def _source(self, source: str):
        if source not in self.sources:
            raise OperationError(404, 'unknown_source', f"No audiobook source '{source}'")
        return self.sources.get(source)

    def _play(self, book: str, source: str, resume: bool) -> None:
        if source == LOCAL:
            self._resume.play(book, self._chapter_files(book), resume=resume, context=self._context(book))
            return
        implementation = self._source(source)
        self._resume.play(f'{source}/{book}', implementation.files(book), resume=resume,
                          context=self._context(book, source), store=implementation.position(book))

    @action()
    def play(self, book: str, source: str = LOCAL) -> None:
        """Play an audiobook where it stopped (from the beginning when it is new or finished)."""
        self._play(book, source, True)

    @action()
    def restart(self, book: str, source: str = LOCAL) -> None:
        """Play an audiobook from the beginning."""
        self._play(book, source, False)

    @action()
    def set_finished(self, book: str, finished: bool = True, source: str = LOCAL) -> None:
        """Mark an audiobook as finished (or not); either way it starts from the beginning next time."""
        if source == LOCAL:
            self._chapter_files(book)
            self._resume.set_finished(book, finished)
        else:
            self._source(source).set_finished(book, finished)
