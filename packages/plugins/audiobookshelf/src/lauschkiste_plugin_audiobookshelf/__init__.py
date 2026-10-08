"""Audiobooks from an Audiobookshelf server.

Enable with::

    plugins:
      audiobookshelf:
        server_url: https://abs.example.org
        api_key: ...
"""

import logging

from pydantic import BaseModel, Field

from lauschkiste.contract import Plugin
from lauschkiste_plugin_audiobookshelf.source import COVER_ROUTE, SCHEME, AudiobookshelfSource

logger = logging.getLogger('lauschkiste.audiobookshelf')


class AudiobookshelfSettings(BaseModel):
    server_url: str = Field('', title='Server address', description='e.g. https://audiobookshelf.example.org')
    api_key: str = Field('', title='API key', json_schema_extra={'secret': True},
                         description='Audiobookshelf: Settings, API Keys. Leave empty to keep the current one.')
    refresh_minutes: int = Field(10, ge=1, le=1440, title='Refresh the book list every (minutes)')


class Audiobookshelf(Plugin):
    """Audiobooks from an Audiobookshelf server, played by streaming; the position is shared with its apps."""

    name = 'audiobookshelf'
    interface_version = '1.0'
    requires = {'audiobooks': '>=2.0,<3', 'player': '>=5.2,<6'}
    settings = AudiobookshelfSettings

    def __init__(self):
        self._source = AudiobookshelfSource()

    def start(self, ctx) -> None:
        self._ctx = ctx
        self._configure()
        ctx.modules.audiobooks.sources.register('audiobookshelf', self._source)
        ctx.modules.player.resolvers.register(SCHEME, self._source)

    def _configure(self) -> None:
        config = self._ctx.config
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
