"""The books of an Audiobookshelf server as audiobook source ``audiobookshelf``.

The box keeps working without the server: the book list is kept on disk, downloaded books play from the
box, and positions are written to a ledger first and sent to the server when it is reachable again.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional

from lauschkiste.contract import OperationError
from lauschkiste_plugin_audiobookshelf.client import AudiobookshelfError, Client
from lauschkiste_plugin_audiobookshelf.downloads import DownloadCache
from lauschkiste_plugin_audiobookshelf.ledger import Ledger, winner

logger = logging.getLogger('lauschkiste.audiobookshelf')

SCHEME = 'abs'
COVER_ROUTE = '/api/v1/audiobookshelf/covers'
TRACKS_TTL_SEC = 600.0
#: After a failed request the server is not asked again for this long (each try would wait for the timeout)
RETRY_AFTER_SEC = 30.0


class Track(NamedTuple):
    url: str
    start: float
    duration: float


def track_url(book: str, ino: str) -> str:
    return f'{SCHEME}://{book}/{ino}'


def total_of(tracks: List[Track]) -> float:
    return tracks[-1].start + tracks[-1].duration


class BookPosition:
    """The position of one book: on the server, with the ledger of the box as fallback and backup."""

    def __init__(self, source: 'AudiobookshelfSource', book: str):
        self._source = source
        self._book = book

    def load(self) -> Dict[str, Any]:
        state = self._source.reconcile(self._book)
        if not state:
            return {}
        if state['finished']:
            return {'finished': True}
        try:
            tracks = self._source.tracks(self._book)
        except (OperationError, AudiobookshelfError):
            return {}
        position = float(state['position'])
        track = next((t for t in reversed(tracks) if t.start <= position), tracks[0])
        return {'file': track.url, 'elapsed': position - track.start, 'finished': False}

    def save(self, entry: Dict[str, Any]) -> None:
        tracks = self._source.tracks(self._book)
        total = total_of(tracks)
        if entry.get('finished'):
            position, finished = total, True
        else:
            track = next((t for t in tracks if t.url == entry.get('file')), None)
            if track is None:
                return
            position, finished = track.start + float(entry.get('elapsed') or 0), False
        self._source.record(self._book, position, total, finished)


class AudiobookshelfSource:
    def __init__(self):
        self._lock = threading.Lock()
        self._client: Optional[Client] = None
        self._refresh_sec = 600.0
        self._items: Optional[List[Dict[str, Any]]] = None
        self._items_at = 0.0
        self._tracks: Dict[str, tuple] = {}
        self._down_until = 0.0
        self.last_error: Optional[str] = None
        self.cache: Optional[DownloadCache] = None
        self.ledger: Optional[Ledger] = None
        self.prefer_downloaded = True

    def attach(self, cache: DownloadCache) -> None:
        self.cache = cache
        self.ledger = Ledger(cache.root / 'positions.json')

    # -- the server -----------------------------------------------------------------------------

    def credentials(self):
        client = self._client
        return (client.base, client.key) if client else ('', '')

    def configure(self, server_url: str, api_key: str, refresh_minutes: float) -> None:
        with self._lock:
            self._client = Client(server_url, api_key) if server_url and api_key else None
            self._refresh_sec = float(refresh_minutes) * 60
            self._items, self._tracks, self._down_until = None, {}, 0.0
            self.last_error = None

    def client(self) -> Client:
        client = self._client
        if client is None:
            raise OperationError(503, 'audiobookshelf_not_configured',
                                 'Audiobookshelf: enter the server address and an API key in the settings')
        return client

    def reachable(self) -> bool:
        """False for a while after the server did not answer."""
        return self._client is not None and time.monotonic() >= self._down_until

    def _failed(self, error: Exception) -> None:
        self._down_until = time.monotonic() + RETRY_AFTER_SEC
        self.last_error = str(error)

    def _ok(self) -> None:
        self._down_until, self.last_error = 0.0, None

    def book_size(self, book: str) -> int:
        """Bytes of the audio files of a book on the server."""
        item = self.client().item(book)
        if item is None:
            raise OperationError(404, 'unknown_audiobook', f"No audiobook '{book}' on the Audiobookshelf server")
        return sum(int(f['metadata'].get('size') or 0) for f in (item.get('media') or {}).get('audioFiles') or [])

    # -- positions ------------------------------------------------------------------------------

    def reconcile(self, book: str) -> Optional[Dict[str, Any]]:
        """The position to continue from: ``{'position', 'finished'}`` or None for a book never played.

        Sends what the box recorded offline once the server answers."""
        ledger = self.ledger
        local = ledger.get(book) if ledger else None
        remote: Optional[Dict[str, Any]] = None
        if self.reachable():
            try:
                remote = self.client().progress_of(book) or {}
                self._ok()
            except AudiobookshelfError as error:
                self._failed(error)
        if remote is None:
            return {'position': float(local.get('position') or 0), 'finished': bool(local.get('finished'))} \
                if local else None
        seen = {'position': float(remote.get('currentTime') or 0), 'finished': bool(remote.get('isFinished'))}
        state, waiting = dict(seen), False
        if local and local.get('pending'):
            state = winner(local, seen['position'], seen['finished'])
            if state != seen:
                if self._send(book, state['position'], float(local.get('duration') or 0), state['finished']):
                    seen = dict(state)
                else:
                    waiting = True
        if ledger is not None and (local or remote):
            ledger.update(book, **state, seen=seen, pending=waiting)
        return state if (local or remote) else None

    def _send(self, book: str, position: float, duration: float, finished: bool) -> bool:
        try:
            self.client().save_progress(book, duration if finished and duration else position, duration, finished)
        except AudiobookshelfError as error:
            self._failed(error)
            return False
        self._ok()
        return True

    def record(self, book: str, position: float, duration: float, finished: bool) -> None:
        """Remember a position on the box and send it to the server (or keep it for later)."""
        ledger = self.ledger
        if ledger is not None:
            ledger.update(book, position=position, duration=duration, finished=finished, pending=True)
        if self.reachable() and self._send(book, position, duration, finished):
            if ledger is not None:
                ledger.update(book, pending=False, seen={'position': position, 'finished': finished})

    def sync_pending(self) -> int:
        """Send the positions recorded offline; returns how many are still waiting."""
        if self.ledger is None or not self.reachable():
            return len(self.ledger.pending()) if self.ledger else 0
        for book in self.ledger.pending():
            if not self.reachable():
                break
            self.reconcile(book)
        return len(self.ledger.pending())

    def position(self, book: str) -> BookPosition:
        return BookPosition(self, book)

    def set_finished(self, book: str, finished: bool) -> None:
        total = total_of(self.tracks(book))
        self.record(book, total if finished else 0.0, total, finished)

    # -- the book list --------------------------------------------------------------------------

    @property
    def _list_file(self) -> Optional[Path]:
        return self.cache.root / 'books.json' if self.cache is not None else None

    def _remember_items(self, items: List[Dict[str, Any]]) -> None:
        path = self._list_file
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + '.tmp')
            tmp.write_text(json.dumps(items))
            os.replace(tmp, path)
        except OSError as error:
            logger.warning(f"Could not save the book list: {error}")

    def _known_items(self) -> List[Dict[str, Any]]:
        with self._lock:
            if self._items is not None:
                return self._items
        path = self._list_file
        try:
            items = json.loads(path.read_text()) if path else []
        except (OSError, ValueError):
            items = []
        return items if isinstance(items, list) else []

    def _all_items(self, client: Client) -> List[Dict[str, Any]]:
        with self._lock:
            if self._items is not None and time.monotonic() - self._items_at < self._refresh_sec:
                return self._items
        items: List[Dict[str, Any]] = []
        for library in client.libraries():
            items.extend(client.books(library['id']))
        with self._lock:
            self._items, self._items_at = items, time.monotonic()
        self._remember_items(items)
        return items

    def list_books(self) -> List[Dict[str, Any]]:
        if self._client is None:
            return []
        items, progress = self._known_items(), None
        if self.reachable():
            try:
                items, progress = self._all_items(self._client), self._client.progress()
                self._ok()
            except AudiobookshelfError as error:
                self._failed(error)
                items = self._known_items()
        books = [self._describe(item, progress) for item in items]
        books += self._only_downloaded({item['id'] for item in items})
        online = progress is not None
        return sorted(books, key=lambda b: (online is False and not b.get('downloaded'), str(b['title']).casefold()))

    def _describe(self, item: Dict[str, Any], progress: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        media = item.get('media') or {}
        book = item['id']
        duration = float(media.get('duration') or 0)
        local = self.ledger.get(book) if self.ledger else None
        if local and (local.get('pending') or progress is None):
            finished, position = bool(local.get('finished')), float(local.get('position') or 0)
        else:
            entry = (progress or {}).get(book, {})
            finished, position = bool(entry.get('isFinished')), float(entry.get('currentTime') or 0)
        listened = duration if finished else position
        chapter, elapsed = self._place(book, listened) if 0 < listened and not finished else (0, 0.0)
        return {'book': book, 'title': (media.get('metadata') or {}).get('title') or book,
                'chapters': int(media.get('numAudioFiles') or 0), 'duration': duration or None,
                'chapter': chapter, 'elapsed': elapsed, 'listened': listened, 'finished': finished,
                'cover_url': f'{COVER_ROUTE}/{book}',
                'downloaded': bool(self.cache and self.cache.complete(book))}

    def _only_downloaded(self, known: set) -> List[Dict[str, Any]]:
        """Downloaded books the list does not know (yet): they play without the server."""
        books = []
        for book in (self.cache.books() if self.cache else []):
            meta = self.cache.complete(book)
            if meta and book not in known:
                local = self.ledger.get(book) if self.ledger else None
                finished = bool(local and local.get('finished'))
                books.append({'book': book, 'title': meta.get('title') or book, 'chapters': len(meta['files']),
                              'duration': sum(float(f.get('duration') or 0) for f in meta['files']) or None,
                              'chapter': 0, 'elapsed': 0.0, 'listened': float(local.get('position') or 0) if local else 0.0,
                              'finished': finished, 'cover_url': None, 'downloaded': True})
        return books

    def update_available(self, book: str) -> bool:
        meta = self.cache.complete(book) if self.cache else None
        if not meta or meta.get('updatedAt') is None:
            return False
        item = next((i for i in self._known_items() if i.get('id') == book), None)
        return bool(item and item.get('updatedAt') and item['updatedAt'] != meta['updatedAt'])

    def status(self) -> Dict[str, Any]:
        """Whether the server is configured and answers (the answer to the last request, not a new one)."""
        configured = self._client is not None
        return {'configured': configured, 'reachable': configured and self.last_error is None,
                'error': self.last_error, 'waiting': len(self.ledger.pending()) if self.ledger else 0}

    # -- the files ------------------------------------------------------------------------------

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

    def _place(self, book: str, position: float):
        """(file index, seconds into it) of a position in the book; (0, position) if the files are unknown."""
        try:
            tracks = self._downloaded(book) or self._cached_tracks(book)
        except Exception as error:
            logger.debug(f"No tracks for '{book}': {error}")
            tracks = None
        if not tracks:
            tracks = self._fetch_tracks_online(book)
        if not tracks:
            return 0, position
        index = max((i for i, track in enumerate(tracks) if track.start <= position), default=0)
        return index, position - tracks[index].start

    def _cached_tracks(self, book: str) -> Optional[List[Track]]:
        with self._lock:
            cached = self._tracks.get(book)
        return cached[1] if cached and time.monotonic() - cached[0] < TRACKS_TTL_SEC else None

    def _fetch_tracks_online(self, book: str) -> Optional[List[Track]]:
        if not self.reachable():
            return None
        try:
            return self.tracks(book)
        except (OperationError, AudiobookshelfError) as error:
            logger.debug(f"No tracks for '{book}': {error}")
            return None

    def tracks(self, book: str) -> List[Track]:
        downloaded = self._downloaded(book)
        if downloaded:
            return downloaded
        cached = self._cached_tracks(book)
        if cached:
            return cached
        if not self.reachable():
            raise OperationError(503, 'audiobookshelf_unavailable',
                                 self.last_error or 'The server is not reachable and the book is not downloaded')
        try:
            item = self.client().item(book)
        except AudiobookshelfError as error:
            self._failed(error)
            raise OperationError(503, 'audiobookshelf_unavailable', str(error)) from None
        self._ok()
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
        return [track.url for track in self.tracks(book)]

    def title(self, book: str) -> str:
        for item in self._known_items():
            if item.get('id') == book:
                return (item.get('media', {}).get('metadata') or {}).get('title') or book
        meta = self.cache.meta(book) if self.cache else None
        return (meta or {}).get('title') or book

    # -- the resolver ---------------------------------------------------------------------------

    def resolve(self, url: str):
        """``abs://<book>/<file id>`` -> the file on the server and the header that authorises it."""
        book, _, ino = url[len(SCHEME) + 3:].partition('/')
        client = self.client()
        return f'{client.base}/api/items/{book}/file/{ino}/download', client.headers
