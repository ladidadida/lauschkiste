"""The audiobooks core module: audiobooks in ``library/audiobooks``, continued where they stopped.

Each folder directly below ``audiobooks`` is one audiobook, its files are the chapters in file name
order. The tags give title, author and cover; a ``book.json`` in the folder, written by the web app,
can set its own title, author, cover image and chapter order and names. The position is kept per
audiobook in ``audiobooks.state_file``; chapters play in order, regardless of shuffle and repeat.
"""

import asyncio
import json
import logging
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.requests import Request

import lauschkiste.common.paths
import lauschkiste.common.statefile as statefile
import lauschkiste.content.library
from lauschkiste.contract import CoreModule, OperationError, action, extension_point, query
from lauschkiste.content.dismissed import Dismissed
from lauschkiste.content.library.files import COVER_EXTENSIONS
from lauschkiste.content.resume import ResumeTracker

logger = logging.getLogger('lauschkiste.content.audiobooks')

LOCAL = 'local'

DEFAULT_STATE_FILE = 'settings/audiobooks.json'
DEFAULT_HIDDEN_FILE = 'settings/audiobooks_hidden.json'
BOOK_FILE = 'book.json'
COVER_STEM = 'book-cover'
MAX_COVER_SIZE = 10 * 1024 * 1024
FILE_MODE = 0o664


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
        """A ``lauschkiste.content.resume.PositionStore`` for the book."""

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
    #: 'local' (a folder of the library), 'cached' (downloaded from the source) or 'stream' (played over the network)
    availability: str = 'local'
    #: taken off the "continue" list; it comes back when the book is played on
    hidden: bool = False
    #: the title was set in the web app (``book.json``), not taken from the tags
    custom_title: bool = False
    author: Optional[str] = None


class Chapter(BaseModel):
    #: path of the file below the book's folder
    file: str
    title: str
    #: the title from the file's tags
    tag_title: Optional[str] = None
    duration: Optional[float] = None


class ChapterEdit(BaseModel):
    file: str
    #: empty: the title from the tags
    title: str = ''


class AudiobookDetails(BaseModel):
    book: str
    title: str
    tag_title: Optional[str] = None
    author: Optional[str] = None
    tag_author: Optional[str] = None
    cover_url: Optional[str] = None
    #: the cover was uploaded in the web app
    custom_cover: bool = False
    chapters: List[Chapter]


class CoverSaved(BaseModel):
    cover_url: Optional[str] = None


def natural_key(text: str):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r'(\d+)', text)]


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _text(value: Any) -> Optional[str]:
    return (value.strip() or None) if isinstance(value, str) else None


def _stem(file: str) -> str:
    return file.rsplit('/', 1)[-1].rsplit('.', 1)[0]


def _error(error: OperationError) -> JSONResponse:
    return JSONResponse(status_code=error.status, content={'error': {'code': error.code, 'message': error.message}})


class Audiobooks(CoreModule):
    """Audiobooks: play, continue, start over, mark as finished, edit title, author, cover and chapters."""

    name = 'audiobooks'
    interface_version = '5.0'
    concurrency = 'threadsafe'
    requires = ('library', 'player', 'cache')
    settings = AudiobookSettings
    sources = extension_point('sources', AudiobookSource)

    def __init__(self):
        self._ctx: Any = None
        self._resume: Any = None
        self._dismissed: Any = None
        self._edit_lock = threading.Lock()

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._resume = ResumeTracker(
            ctx, lauschkiste.common.paths.resolve(ctx.config.get('state_file', default=DEFAULT_STATE_FILE)),
            rewind_sec=float(ctx.config.get('rewind_sec', default=10)),
            save_interval_sec=float(ctx.config.get('save_interval_sec', default=10)))
        self._resume.start()
        self._dismissed = Dismissed(lauschkiste.common.paths.resolve(DEFAULT_HIDDEN_FILE))

    def stop(self):
        self._resume.stop()
        return []

    def settings_changed(self, changed):
        if 'rewind_sec' in changed:
            self._resume.configure(float(changed['rewind_sec']))
        return True

    # -- library --------------------------------------------------------------------------------

    def _songs(self, book: Optional[str] = None):
        folder = lauschkiste.common.paths.AUDIOBOOKS_DIR + (f'/{book}' if book else '')
        return self._ctx.modules.library.list_folder_songs(folder)

    @staticmethod
    def _prefix(book: str) -> str:
        return f'{lauschkiste.common.paths.AUDIOBOOKS_DIR}/{book}/'

    def _folder(self, book: str) -> Path:
        return Path(lauschkiste.content.library.root()).expanduser() / lauschkiste.common.paths.AUDIOBOOKS_DIR / book

    def _book_info(self, book: str) -> Dict[str, Any]:
        try:
            info = json.loads((self._folder(book) / BOOK_FILE).read_text(encoding='utf-8'))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as error:
            logger.warning(f"Ignoring {BOOK_FILE} of audiobook '{book}': {error}")
            return {}
        return info if isinstance(info, dict) else {}

    def _write_info(self, book: str, info: Dict[str, Any]) -> None:
        path = self._folder(book) / BOOK_FILE
        try:
            if not info:
                path.unlink(missing_ok=True)
                return
            statefile.write_text(path, json.dumps(info, indent=2) + '\n')
            path.chmod(FILE_MODE)
        except OSError as error:
            raise OperationError(500, 'write_failed', f"Cannot save the changes of '{book}': {error}") from error

    def _book_songs(self, book: str) -> list:
        if not book or '/' in book or book in ('.', '..'):
            raise OperationError(422, 'invalid_audiobook', f"Invalid audiobook name '{book}'")
        songs = self._songs(book)
        if not songs:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}' in the library")
        return songs

    def _ordered(self, book: str, songs: list, info: Dict[str, Any]) -> List[Tuple[Any, Optional[str]]]:
        """The chapters in playing order, each with its title from ``book.json`` (or None)."""
        prefix = self._prefix(book)
        by_name = {song.file[len(prefix):]: song for song in songs if song.file.startswith(prefix)}
        result, seen = [], set()
        for entry in info.get('chapters') or []:
            name = entry.get('file') if isinstance(entry, dict) else None
            if name in by_name and name not in seen:
                seen.add(name)
                result.append((by_name[name], _text(entry.get('title'))))
        result.extend((by_name[name], None) for name in sorted(by_name, key=natural_key) if name not in seen)
        return result

    def _chapter_files(self, book: str) -> List[str]:
        return [song.file for song, _title in self._ordered(book, self._book_songs(book), self._book_info(book))]

    def _cover(self, book: str, info: Dict[str, Any], first_file: str) -> Tuple[Optional[str], bool]:
        library = self._ctx.modules.library
        cover = _text(info.get('cover'))
        try:
            if cover and '/' not in cover:
                url = library.get_image_cover(self._prefix(book) + cover).cover_url
                if url:
                    return url, True
            return library.get_song_cover(first_file).cover_url, False
        except Exception:
            return None, False

    @staticmethod
    def _tag_title(songs: list) -> Optional[str]:
        return next((song.album for song in songs if song.album), None)

    @staticmethod
    def _tag_author(songs: list) -> Optional[str]:
        return next((song.albumartist or song.artist for song in songs if song.albumartist or song.artist), None)

    # -- operations -----------------------------------------------------------------------------

    @query(path='/')
    def list_books(self) -> List[Audiobook]:
        """All audiobooks with their progress."""
        books: Dict[str, list] = {}
        prefix = lauschkiste.common.paths.AUDIOBOOKS_DIR + '/'
        for song in self._songs():
            parts = song.file[len(prefix):].split('/', 1)
            if len(parts) == 2:
                books.setdefault(parts[0], []).append(song)
        positions = self._resume.entries()
        result = []
        for book in sorted(books, key=natural_key):
            info = self._book_info(book)
            songs = [song for song, _title in self._ordered(book, books[book], info)]
            files = [song.file for song in songs]
            durations = [song.duration or 0.0 for song in songs]
            total = sum(durations) if all(song.duration for song in songs) else None
            entry = positions.get(book, {})
            finished = bool(entry.get('finished'))
            chapter = files.index(entry['file']) if entry.get('file') in files else 0
            elapsed = _number(entry.get('elapsed')) if entry.get('file') in files else 0.0
            listened = total if finished and total else sum(durations[:chapter]) + elapsed
            custom_title = _text(info.get('title'))
            result.append(Audiobook(book=book, title=custom_title or self._tag_title(songs) or book, chapters=len(files),
                                    duration=total, chapter=chapter, elapsed=elapsed, listened=listened,
                                    finished=finished, cover_url=self._cover(book, info, files[0])[0],
                                    custom_title=custom_title is not None,
                                    author=_text(info.get('author')) or self._tag_author(songs)))
        for source, implementation in self.sources.items():
            try:
                cached = {entry.item for entry in self._ctx.modules.cache.cached(source)} \
                    if source in self._ctx.modules.cache.providers else set()
                result.extend(Audiobook(**{**entry, 'source': source,
                                           'availability': 'cached' if entry['book'] in cached else 'stream'})
                              for entry in implementation.list_books())
            except Exception as error:
                logger.warning(f"Audiobooks of source '{source}' are not available: {error}")
        for entry in result:
            entry.hidden = self._dismissed.is_hidden(f'{entry.source}/{entry.book}', round(entry.listened))
        return result

    @query(path='/book')
    def get_book(self, book: str) -> AudiobookDetails:
        """A local audiobook with its chapters, for editing."""
        songs = self._book_songs(book)
        info = self._book_info(book)
        ordered = self._ordered(book, songs, info)
        prefix = self._prefix(book)
        tag_title, tag_author = self._tag_title(songs), self._tag_author(songs)
        cover_url, custom_cover = self._cover(book, info, ordered[0][0].file)
        return AudiobookDetails(
            book=book, title=_text(info.get('title')) or tag_title or book, tag_title=tag_title,
            author=_text(info.get('author')) or tag_author, tag_author=tag_author, cover_url=cover_url,
            custom_cover=custom_cover,
            chapters=[Chapter(file=song.file[len(prefix):], title=title or song.title or _stem(song.file),
                              tag_title=song.title, duration=song.duration) for song, title in ordered])

    def _context(self, book: str, source: str = LOCAL) -> Dict[str, Any]:
        args = {'book': book} if source == LOCAL else {'book': book, 'source': source}
        if source != LOCAL:
            implementation = self._source(source)
            return {'kind': 'audiobook', 'title': implementation.title(book), 'action': 'audiobooks.play',
                    'args': args, 'image': getattr(implementation, 'cover_url', lambda _book: None)(book)}
        songs = self._songs(book)
        info = self._book_info(book)
        ordered = self._ordered(book, songs, info)
        cover, custom_cover = self._cover(book, info, ordered[0][0].file) if ordered else (None, False)
        return {'kind': 'audiobook', 'title': _text(info.get('title')) or self._tag_title(songs) or book,
                'action': 'audiobooks.play', 'args': args, 'image': None,
                'cover': cover if custom_cover else None,
                'titles': {song.file: title for song, title in ordered if title}}

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
    def hide_from_continue(self, book: str, source: str = LOCAL) -> None:
        """Take an audiobook off the "continue" list until it is played on."""
        entry = next((b for b in self.list_books() if b.book == book and b.source == source), None)
        if entry is None:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}'")
        self._dismissed.hide(f'{source}/{book}', round(entry.listened))

    @action()
    def restart(self, book: str, source: str = LOCAL) -> None:
        """Play an audiobook from the beginning."""
        self._play(book, source, False)

    @action()
    def set_finished(self, book: str, finished: bool = True, source: str = LOCAL) -> None:
        """Mark an audiobook as finished (or not); either way it starts from the beginning next time."""
        if source == LOCAL:
            self._book_songs(book)
            self._resume.set_finished(book, finished)
        else:
            self._source(source).set_finished(book, finished)

    # -- editing --------------------------------------------------------------------------------

    @staticmethod
    def _set(info: Dict[str, Any], key: str, value: str, default: Optional[str]) -> None:
        value = value.strip()
        if value and value != default:
            info[key] = value
        else:
            info.pop(key, None)

    @action()
    def set_title(self, book: str, title: str = '') -> None:
        """Give a local audiobook its own title; an empty title goes back to the one from the tags."""
        songs = self._book_songs(book)
        with self._edit_lock:
            info = self._book_info(book)
            self._set(info, 'title', title, self._tag_title(songs))
            self._write_info(book, info)

    @action()
    def edit_book(self, book: str, title: str = '', author: str = '',
                  chapters: Optional[List[ChapterEdit]] = None) -> AudiobookDetails:
        """Change title, author and chapters (order and titles) of a local audiobook; empty values go back to
        the tags. ``chapters`` lists the files below the book's folder in playing order; files left out follow
        in file name order. Without ``chapters`` they stay as they are. Files and folder are not changed."""
        songs = self._book_songs(book)
        prefix = self._prefix(book)
        by_name = {song.file[len(prefix):]: song for song in songs}
        with self._edit_lock:
            info = self._book_info(book)
            self._set(info, 'title', title, self._tag_title(songs))
            self._set(info, 'author', author, self._tag_author(songs))
            if chapters is not None:
                chapters = [ChapterEdit.model_validate(chapter) for chapter in chapters]
                listed = [chapter.file for chapter in chapters]
                unknown = [name for name in listed if name not in by_name]
                if unknown or len(set(listed)) != len(listed):
                    raise OperationError(422, 'invalid_chapters',
                                         f"Unknown or repeated chapters: {', '.join(unknown) or 'repeated'}")
                titles = {chapter.file: chapter.title.strip() for chapter in chapters}
                natural = sorted(by_name, key=natural_key)
                order = listed + [name for name in natural if name not in titles]
                entries = []
                for name in order:
                    entry = {'file': name}
                    if titles.get(name) and titles[name] != by_name[name].title:
                        entry['title'] = titles[name]
                    entries.append(entry)
                if order == natural and not any('title' in entry for entry in entries):
                    info.pop('chapters', None)
                else:
                    info['chapters'] = entries
            self._write_info(book, info)
        return self.get_book(book)

    def _save_cover(self, book: str, name: str, data: bytes) -> CoverSaved:
        self._book_songs(book)
        suffix = Path(name).suffix.lower()
        if suffix not in COVER_EXTENSIONS:
            raise OperationError(415, 'unsupported_file_type', f"'{name}' is not a supported image.")
        if not data:
            raise OperationError(422, 'empty_file', 'The image is empty.')
        folder = self._folder(book)
        target = folder / f'{COVER_STEM}{suffix}'
        with self._edit_lock:
            try:
                for old in folder.glob(f'{COVER_STEM}.*'):
                    if old != target:
                        old.unlink()
                temporary = folder / f'.{COVER_STEM}.part'
                temporary.write_bytes(data)
                temporary.chmod(FILE_MODE)
                os.replace(temporary, target)
            except OSError as error:
                raise OperationError(500, 'write_failed', f"Cannot save the cover of '{book}': {error}") from error
            info = self._book_info(book)
            info['cover'] = target.name
            self._write_info(book, info)
        return CoverSaved(cover_url=self.get_book(book).cover_url)

    def extra_routes(self, router) -> None:
        @router.put('/api/v1/audiobooks/cover', tags=['audiobooks'])
        async def upload_cover(request: Request, book: str, name: str):
            """Upload a cover image (raw request body, ``name`` gives the file type) for a local audiobook."""
            length = request.headers.get('content-length')
            if length is not None and length.isdigit() and int(length) > MAX_COVER_SIZE:
                return _error(OperationError(413, 'file_too_large', 'Covers are limited to 10 MiB.'))
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > MAX_COVER_SIZE:
                    return _error(OperationError(413, 'file_too_large', 'Covers are limited to 10 MiB.'))
            try:
                saved = await asyncio.get_running_loop().run_in_executor(None, self._save_cover, book, name, bytes(data))
            except OperationError as error:
                return _error(error)
            return saved.model_dump()

    @action()
    def remove_cover(self, book: str) -> None:
        """Go back to the cover from the files."""
        self._book_songs(book)
        with self._edit_lock:
            info = self._book_info(book)
            cover = _text(info.pop('cover', None))
            if cover and '/' not in cover:
                (self._folder(book) / cover).unlink(missing_ok=True)
            self._write_info(book, info)
