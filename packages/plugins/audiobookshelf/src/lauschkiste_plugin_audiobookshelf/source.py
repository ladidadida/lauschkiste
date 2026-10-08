"""The books of an Audiobookshelf server as audiobook source ``audiobookshelf``."""

import logging
import threading
import time
from typing import Any, Dict, List, NamedTuple, Optional

from lauschkiste.contract import OperationError
from lauschkiste_plugin_audiobookshelf.client import AudiobookshelfError, Client
from lauschkiste_plugin_audiobookshelf.downloads import DownloadCache

logger = logging.getLogger('lauschkiste.audiobookshelf')

SCHEME = 'abs'
COVER_ROUTE = '/api/v1/audiobookshelf/covers'
TRACKS_TTL_SEC = 600.0


class Track(NamedTuple):
    url: str
    start: float
    duration: float


def track_url(book: str, ino: str) -> str:
    return f'{SCHEME}://{book}/{ino}'


class BookPosition:
    """The position of one book, kept on the server."""

    def __init__(self, source: 'AudiobookshelfSource', book: str):
        self._source = source
        self._book = book

    def load(self) -> Dict[str, Any]:
        entry = self._source.client().progress_of(self._book)
        if not entry:
            return {}
        if entry.get('isFinished'):
            return {'finished': True}
        position = float(entry.get('currentTime') or 0)
        tracks = self._source.tracks(self._book)
        track = next((t for t in reversed(tracks) if t.start <= position), tracks[0])
        return {'file': track.url, 'elapsed': position - track.start, 'finished': False}

    def save(self, entry: Dict[str, Any]) -> None:
        tracks = self._source.tracks(self._book)
        total = tracks[-1].start + tracks[-1].duration
        if entry.get('finished'):
            self._source.client().save_progress(self._book, total, total, True)
        else:
            track = next((t for t in tracks if t.url == entry.get('file')), None)
            if track is None:
                return
            self._source.client().save_progress(self._book, track.start + float(entry.get('elapsed') or 0), total, False)
        self._source.forget_progress()


class AudiobookshelfSource:
    def __init__(self):
        self._lock = threading.Lock()
        self._client: Optional[Client] = None
        self._refresh_sec = 600.0
        self._items: Optional[List[Dict[str, Any]]] = None
        self._items_at = 0.0
        self._tracks: Dict[str, tuple] = {}
        self.cache: Optional[DownloadCache] = None
        self.prefer_downloaded = True

    def credentials(self):
        client = self._client
        return (client.base, client.key) if client else ('', '')

    def book_size(self, book: str) -> int:
        """Bytes of the audio files of a book on the server."""
        item = self.client().item(book)
        if item is None:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}' on the Audiobookshelf server")
        return sum(int(f['metadata'].get('size') or 0) for f in (item.get('media') or {}).get('audioFiles') or [])

    def _downloaded(self, book: str) -> Optional[List[Track]]:
        meta = self.cache.complete(book) if self.cache is not None and self.prefer_downloaded else None
        if not meta:
            return None
        tracks, start = [], 0.0
        for entry in meta['files']:
            duration = float(entry.get('duration') or 0)
            tracks.append(Track(str(self.cache.directory(book) / entry['name']), start, duration))
            start += duration
        return tracks or None

    def configure(self, server_url: str, api_key: str, refresh_minutes: float) -> None:
        with self._lock:
            self._client = Client(server_url, api_key) if server_url and api_key else None
            self._refresh_sec = float(refresh_minutes) * 60
            self._items, self._tracks = None, {}

    def client(self) -> Client:
        client = self._client
        if client is None:
            raise OperationError(503, 'audiobookshelf_not_configured',
                                 'Audiobookshelf: enter the server address and an API key in the settings')
        return client

    def forget_progress(self) -> None:
        """Nothing is cached about the progress; kept for the day it is."""

    # -- the source -----------------------------------------------------------------------------

    def _all_items(self, client: Client) -> List[Dict[str, Any]]:
        with self._lock:
            if self._items is not None and time.monotonic() - self._items_at < self._refresh_sec:
                return self._items
        items: List[Dict[str, Any]] = []
        for library in client.libraries():
            items.extend(client.books(library['id']))
        with self._lock:
            self._items, self._items_at = items, time.monotonic()
        return items

    def list_books(self) -> List[Dict[str, Any]]:
        if self._client is None:
            return []
        client = self._client
        items, progress = self._all_items(client), client.progress()
        books = []
        for item in items:
            media = item.get('media') or {}
            duration = float(media.get('duration') or 0)
            entry = progress.get(item['id'], {})
            finished = bool(entry.get('isFinished'))
            listened = duration if finished else float(entry.get('currentTime') or 0)
            chapter, elapsed = self._place(client, item['id'], listened) if 0 < listened and not finished else (0, 0.0)
            books.append({
                'book': item['id'],
                'title': (media.get('metadata') or {}).get('title') or item['id'],
                'chapters': int(media.get('numAudioFiles') or 0),
                'duration': duration or None,
                'chapter': chapter,
                'elapsed': elapsed,
                'listened': listened,
                'finished': finished,
                'cover_url': f'{COVER_ROUTE}/{item["id"]}'})
        return sorted(books, key=lambda book: str(book['title']).casefold())

    def _place(self, client: Client, book: str, position: float):
        """(file index, seconds into it) of a position in the book; (0, position) if the files are unknown."""
        try:
            tracks = self.tracks(book)
        except Exception as error:
            logger.debug(f"No tracks for '{book}': {error}")
            return 0, position
        index = max((i for i, track in enumerate(tracks) if track.start <= position), default=0)
        return index, position - tracks[index].start

    def tracks(self, book: str) -> List[Track]:
        downloaded = self._downloaded(book)
        if downloaded:
            return downloaded
        with self._lock:
            cached = self._tracks.get(book)
        if cached and time.monotonic() - cached[0] < TRACKS_TTL_SEC:
            return cached[1]
        item = self.client().item(book)
        if item is None:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}' on the Audiobookshelf server")
        files = sorted((item.get('media') or {}).get('audioFiles') or [], key=lambda f: f.get('index', 0))
        tracks, start = [], 0.0
        for audio in files:
            duration = float(audio.get('duration') or 0)
            tracks.append(Track(track_url(book, str(audio['ino'])), start, duration))
            start += duration
        if not tracks:
            raise OperationError(404, 'unknown_audiobook', f"The audiobook '{book}' has no audio files")
        with self._lock:
            self._tracks[book] = (time.monotonic(), tracks, (item.get('media') or {}).get('metadata', {}).get('title'))
        return tracks

    def files(self, book: str) -> List[str]:
        try:
            return [track.url for track in self.tracks(book)]
        except AudiobookshelfError as error:
            raise OperationError(503, 'audiobookshelf_unavailable', str(error)) from None

    def title(self, book: str) -> str:
        for item in self._items or []:
            if item.get('id') == book:
                return (item.get('media', {}).get('metadata') or {}).get('title') or book
        return book

    def position(self, book: str) -> BookPosition:
        return BookPosition(self, book)

    def set_finished(self, book: str, finished: bool) -> None:
        tracks = self.tracks(book)
        total = tracks[-1].start + tracks[-1].duration
        try:
            self.client().save_progress(book, total if finished else 0.0, total, finished)
        except AudiobookshelfError as error:
            raise OperationError(503, 'audiobookshelf_unavailable', str(error)) from None

    # -- the resolver ---------------------------------------------------------------------------

    def resolve(self, url: str):
        """``abs://<book>/<file id>`` -> the file on the server and the header that authorises it."""
        book, _, ino = url[len(SCHEME) + 3:].partition('/')
        client = self.client()
        return f'{client.base}/api/items/{book}/file/{ino}/download', client.headers
