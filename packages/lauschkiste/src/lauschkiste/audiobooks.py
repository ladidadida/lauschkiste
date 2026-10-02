"""The audiobooks core module: audiobooks in ``library/audiobooks``, continued where they stopped.

Each folder directly below ``audiobooks`` is one audiobook, its files are the chapters in file name
order. The position is kept per audiobook in ``audiobooks.state_file``; chapters play in order,
regardless of shuffle and repeat.
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

import lauschkiste.paths
from lauschkiste.contract import CoreModule, OperationError, action, query
from lauschkiste.resume import ResumeTracker

DEFAULT_STATE_FILE = 'settings/audiobooks.json'


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
    interface_version = '1.0'
    concurrency = 'threadsafe'
    requires = ('library', 'player')

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
        return result

    @action()
    def play(self, book: str) -> None:
        """Play an audiobook where it stopped (from the beginning when it is new or finished)."""
        self._resume.play(book, self._chapter_files(book))

    @action()
    def restart(self, book: str) -> None:
        """Play an audiobook from the beginning."""
        self._resume.play(book, self._chapter_files(book), resume=False)

    @action()
    def set_finished(self, book: str, finished: bool = True) -> None:
        """Mark an audiobook as finished (or not); either way it starts from the beginning next time."""
        self._chapter_files(book)
        self._resume.set_finished(book, finished)
