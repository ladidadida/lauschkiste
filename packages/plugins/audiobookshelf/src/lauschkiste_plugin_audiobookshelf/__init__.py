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
from lauschkiste.contract import Plugin, query
from lauschkiste_plugin_audiobookshelf.provider import AudiobookshelfProvider
from lauschkiste_plugin_audiobookshelf.source import COVER_ROUTE, SCHEME, AudiobookshelfSource

logger = logging.getLogger('lauschkiste.audiobookshelf')

SYNC_EVERY_SEC = 60.0


class AudiobookshelfSettings(BaseModel):
    server_url: str = Field('', title='Server address',
                            description='e.g. https://audiobookshelf.example.org or http://nas:13378')
    api_key: str = Field('', title='API key', json_schema_extra={'secret': True},
                         description='Create one in Audiobookshelf under Settings, API Keys, for the user the box '
                                     'should use. Leave empty to keep the current one.')
    refresh_minutes: int = Field(10, ge=1, le=1440, title='Ask for new books every (minutes)',
                                 description='The position is always read fresh')
    prefer_downloaded: bool = Field(True, title='Play downloaded books from the box',
                                    description='Even when the server is reachable')


class ServerStatus(BaseModel):
    configured: bool
    reachable: bool
    error: Optional[str] = None
    waiting: int = 0


class Audiobookshelf(Plugin):
    """Audiobooks from an Audiobookshelf server, streamed or downloaded; the position is shared with its apps."""

    name = 'audiobookshelf'
    title = 'Audiobookshelf'
    interface_version = '1.1'
    requires = {'audiobooks': '>=4.0,<5', 'player': '>=6.0,<7', 'cache': '>=1.0,<2'}
    settings = AudiobookshelfSettings

    def __init__(self):
        self._source = AudiobookshelfSource()
        self._stopped = threading.Event()
        self._sync: Optional[threading.Thread] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._configure()
        cache = ctx.modules.cache
        self._source.local_files = lambda book: cache.files('audiobookshelf', book)
        self._source.cached_books = lambda: cache.cached('audiobookshelf')
        self._source.attach(lauschkiste.paths.resolve('settings/audiobookshelf_positions.json'),
                            lauschkiste.paths.resolve('cache/audiobookshelf_books.json'))
        ctx.modules.audiobooks.sources.register('audiobookshelf', self._source)
        ctx.modules.player.resolvers.register(SCHEME, self._source)
        cache.providers.register('audiobookshelf', AudiobookshelfProvider(self._source))
        self._sync = threading.Thread(target=self._sync_loop, name='abs-sync', daemon=True)
        self._sync.start()

    def stop(self):
        self._stopped.set()
        return []

    def _sync_loop(self) -> None:
        """Send the positions recorded without the server once it answers again."""
        while not self._stopped.wait(SYNC_EVERY_SEC):
            try:
                self._source.sync_pending()
            except Exception:
                logger.exception("Could not send the recorded positions")

    @query(path='/status')
    def status(self) -> ServerStatus:
        """Whether the server is set up and answered the last request."""
        return ServerStatus(**self._source.status())

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
