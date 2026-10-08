"""Audiobooks from an Audiobookshelf server.

Enable with::

    plugins:
      audiobookshelf:
        server_url: https://abs.example.org
        api_key: ...
"""

import logging
import threading
from typing import List, Optional

from pydantic import BaseModel, Field

import lauschkiste.paths
from lauschkiste.contract import OperationError, Plugin, action, query
from lauschkiste_plugin_audiobookshelf.client import AudiobookshelfError
from lauschkiste_plugin_audiobookshelf.downloads import RESERVE_BYTES, DownloadCache, DownloadManager
from lauschkiste_plugin_audiobookshelf.source import COVER_ROUTE, SCHEME, AudiobookshelfSource

logger = logging.getLogger('lauschkiste.audiobookshelf')

SYNC_EVERY_SEC = 60.0


class AudiobookshelfSettings(BaseModel):
    server_url: str = Field('', title='Server address', description='e.g. https://audiobookshelf.example.org')
    api_key: str = Field('', title='API key', json_schema_extra={'secret': True},
                         description='Audiobookshelf: Settings, API Keys. Leave empty to keep the current one.')
    refresh_minutes: int = Field(10, ge=1, le=1440, title='Refresh the book list every (minutes)')
    prefer_downloaded: bool = Field(True, title='Play downloaded books from the box',
                                    description='Even when the server is reachable')
    cache_limit_gb: float = Field(8, ge=0.1, le=2000, title='Space for downloaded books (GB)')
    remove_old_downloads: bool = Field(False, title='Make room by removing old downloads',
                                       description='Removes the oldest finished books when the space is full')
    download_rate_kbps_playing: int = Field(1000, ge=0, le=100000, title='Download speed while playing (kB/s)',
                                            description='0 pauses downloads while something plays')


class DownloadState(BaseModel):
    book: str
    state: str
    done: int = 0
    total: int = 0
    error: Optional[str] = None
    update_available: bool = False


class ServerStatus(BaseModel):
    configured: bool
    reachable: bool
    error: Optional[str] = None
    waiting: int = 0


class Downloads(BaseModel):
    items: List[DownloadState]
    used_bytes: int
    limit_bytes: int
    free_bytes: int


class Audiobookshelf(Plugin):
    """Audiobooks from an Audiobookshelf server, played by streaming; the position is shared with its apps."""

    name = 'audiobookshelf'
    interface_version = '1.0'
    requires = {'audiobooks': '>=2.0,<3', 'player': '>=5.2,<6'}
    settings = AudiobookshelfSettings

    def __init__(self):
        self._source = AudiobookshelfSource()
        self._cache = DownloadCache(lauschkiste.paths.resolve('cache/audiobookshelf'))
        self._downloads = DownloadManager(self._cache, self._source.credentials)
        self._playing: Optional[bool] = None
        self._stopped = threading.Event()
        self._sync: Optional[threading.Thread] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._configure()
        ctx.modules.audiobooks.sources.register('audiobookshelf', self._source)
        ctx.modules.player.resolvers.register(SCHEME, self._source)
        self._source.attach(self._cache)
        ctx.subscribe('player.status', self._on_status)
        self._sync = threading.Thread(target=self._sync_loop, name='abs-sync', daemon=True)
        self._sync.start()

    def stop(self):
        self._stopped.set()
        self._downloads.close()
        return []

    def _sync_loop(self) -> None:
        """Send the positions recorded without the server once it answers again."""
        while not self._stopped.wait(SYNC_EVERY_SEC):
            try:
                self._source.sync_pending()
            except Exception:
                logger.exception("Could not send the recorded positions")

    def _limit_bytes(self) -> int:
        return int(float(self._ctx.config.get('cache_limit_gb', default=8)) * (1 << 30))

    def _on_status(self, _topic, status) -> None:
        playing = bool(status) and status.get('state') == 'play'
        if playing != self._playing:
            self._playing = playing
            rate = int(self._ctx.config.get('download_rate_kbps_playing', default=1000)) if playing else 0
            self._cache.set_rate((rate or -1) if playing else 0)

    # -- downloads --------------------------------------------------------------------------

    @query(path='/status')
    def status(self) -> ServerStatus:
        """Whether the server is set up and answered the last request."""
        return ServerStatus(**self._source.status())

    @query(path='/downloads')
    def downloads(self) -> Downloads:
        """Downloaded and downloading books and the space they use."""
        return Downloads(items=[DownloadState(**entry, update_available=self._source.update_available(entry['book']))
                                for entry in self._downloads.states()],
                         used_bytes=self._cache.used_bytes(), limit_bytes=self._limit_bytes(),
                         free_bytes=self._cache.free_bytes())

    @action()
    def download(self, book: str) -> None:
        """Download a book to the box so that it plays without the server."""
        if self._cache.complete(book):
            return
        try:
            needed = self._source.book_size(book) - sum(
                path.stat().st_size for path in self._cache.directory(book).glob('*.part'))
        except AudiobookshelfError as error:
            raise OperationError(503, 'audiobookshelf_unavailable', str(error)) from None
        if self._ctx.config.get('remove_old_downloads', default=False):
            self._make_room(needed)
        used, limit, free = self._cache.used_bytes(), self._limit_bytes(), self._cache.free_bytes()
        mb = 1 << 20
        if used + needed > limit:
            raise OperationError(409, 'download_cache_full',
                                 f"The book needs {needed // mb} MB, {max(0, limit - used) // mb} MB of the "
                                 f"{limit // mb} MB for downloads are free. Remove a download or raise the limit.")
        if free - needed < RESERVE_BYTES:
            raise OperationError(409, 'download_disk_full',
                                 f"The book needs {needed // mb} MB, only {free // mb} MB are free on the disk")
        self._downloads.start(book)

    def _make_room(self, needed: int) -> None:
        """Remove the oldest finished downloads until ``needed`` bytes fit under the limit."""
        finished = [book for book in self._cache.books() if self._cache.complete(book)
                    and (self._source.ledger.get(book) or {}).get('finished')]
        finished.sort(key=lambda book: (self._cache.directory(book) / 'meta.json').stat().st_mtime)
        for book in finished:
            if self._cache.used_bytes() + needed <= self._limit_bytes():
                return
            logger.info(f"Removing the finished download '{book}' to make room")
            self._downloads.remove(book)

    @action()
    def cancel_download(self, book: str) -> None:
        """Stop a download; what was loaded is kept and continued next time."""
        self._downloads.cancel(book)

    @action()
    def remove_download(self, book: str) -> None:
        """Delete the downloaded files of a book (it streams again)."""
        self._downloads.remove(book)

    def _configure(self) -> None:
        config = self._ctx.config
        self._source.prefer_downloaded = bool(config.get('prefer_downloaded', default=True))
        self._source.configure(config.get('server_url', default=''), config.get('api_key', default=''),
                               config.get('refresh_minutes', default=10))

    def settings_changed(self, changed) -> bool:
        self._configure()
        return True

    def extra_routes(self, router) -> None:
        from fastapi.concurrency import run_in_threadpool
        from fastapi.responses import JSONResponse, Response

        @router.get(COVER_ROUTE + '/{book}', tags=['audiobookshelf'])
        async def cover(book: str):
            def fetch():
                try:
                    return self._source.client().cover(book, 400)
                except Exception:
                    return None

            upstream = await run_in_threadpool(fetch) if '/' not in book else None
            if upstream is None:
                return JSONResponse(status_code=404, content={'error': {'code': 'unknown_cover', 'message': book}})
            body = await run_in_threadpool(lambda: upstream.content)
            return Response(body, media_type=upstream.headers.get('content-type', 'image/jpeg'),
                            headers={'Cache-Control': 'public, max-age=86400'})
