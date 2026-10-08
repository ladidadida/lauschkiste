"""The books of an Audiobookshelf server as audiobook source ``audiobookshelf``."""

import logging
import threading
import time
from typing import Any, Dict, List, NamedTuple, Optional

from lauschkiste.contract import OperationError
from lauschkiste_plugin_audiobookshelf.client import AudiobookshelfError, Client

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
            books.append({
                'book': item['id'],
                'title': (media.get('metadata') or {}).get('title') or item['id'],
                'chapters': int(media.get('numAudioFiles') or 0),
                'duration': duration or None,
                'listened': duration if finished else float(entry.get('currentTime') or 0),
                'finished': finished,
                'cover_url': f'{COVER_ROUTE}/{item["id"]}'})
        return sorted(books, key=lambda book: str(book['title']).casefold())

    def tracks(self, book: str) -> List[Track]:
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
