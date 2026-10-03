"""Player backend using an external MPD server.

Enable with ``player.backend: mpd`` and::

    plugins:
      mpd:
        host: localhost
        status_file: settings/music_player_status.json
        library:
          update_on_startup: true
          check_user_rights: true
"""

import logging

from pydantic import BaseModel, Field

import lauschkiste.cfghandler
import lauschkiste.misc as misc
import lauschkiste.paths
import lauschkiste.library
from lauschkiste.contract import Plugin

logger = logging.getLogger('lauschkiste.mpd')

DEFAULTS = {
    'host': 'localhost',
    'status_file': 'settings/music_player_status.json',
    'library': {'update_on_startup': True, 'check_user_rights': True},
}


def _setting(ctx, *keys):
    """Own config section, else the default."""
    missing = object()
    value = ctx.config.get(*keys, default=missing)
    if value is missing:
        value = DEFAULTS
        for key in keys:
            value = value[key]
    return value


COVER_ROUTE = '/api/v1/mpd/covers'


class MpdLibrarySettings(BaseModel):
    update_on_startup: bool = Field(True, title='Update the mpd database on start')
    check_user_rights: bool = Field(True, title='Fix file permissions of the library on start')


class MpdSettings(BaseModel):
    host: str = Field(DEFAULTS['host'], title='mpd host')
    status_file: str = Field(DEFAULTS['status_file'], title='Status file')
    library: MpdLibrarySettings = Field(default_factory=MpdLibrarySettings, title='Library')


class MpdLibrarySource:
    """The mpd database as library source ``mpd``."""

    def __init__(self, backend):
        self._backend = backend

    def describe(self):
        return {'id': 'mpd', 'label': 'MPD', 'views': [
            {'id': 'albums', 'label': 'Albums', 'kind': 'items', 'content_types': ['album']},
        ]}

    def list_items(self, content_types):
        return self._backend.list_library_items(content_types)

    def list_songs(self, albumartist, album, content_uri):
        return self._backend.list_songs_by_artist_and_album(albumartist, album)

    def get_song(self, song_url):
        songs = self._backend.get_song_by_url(song_url)
        return songs[0] if songs else None

    def cover(self, song_url):
        name = self._backend.get_single_coverart(song_url)
        return f'{COVER_ROUTE}/{name}' if name and name != 'CACHE_PENDING' else None

    def refresh(self):
        self._backend.update()


class Mpd(Plugin):
    """Registers the ``mpd`` player backend and its database as library source."""

    name = 'mpd'
    interface_version = '1.4'
    requires = {'player': '>=5.0,<6', 'library': '>=1.0,<2'}
    settings = MpdSettings

    def start(self, ctx) -> None:
        from lauschkiste_plugin_mpd.backend import PlayerMPD

        backend = PlayerMPD(host=_setting(ctx, 'host'),
                            status_file=str(lauschkiste.paths.resolve(_setting(ctx, 'status_file'))))
        if _setting(ctx, 'library', 'update_on_startup'):
            backend.update()
        if _setting(ctx, 'library', 'check_user_rights'):
            music_library_path = lauschkiste.library.root()
            if music_library_path is not None:
                logger.info(f"Change user rights for {music_library_path}")
                misc.recursive_chmod(music_library_path, mode_files=0o664, mode_dirs=0o775)
        ctx.modules.player.backends.register('mpd', backend)
        ctx.modules.library.sources.register('mpd', MpdLibrarySource(backend))
        self._backend = backend

    def extra_routes(self, router) -> None:
        from fastapi.responses import FileResponse, JSONResponse

        @router.get(COVER_ROUTE + '/{name}', tags=['mpd'])
        async def mpd_cover(name: str):
            path = self._backend.coverart_cache_manager.cache_folder_path / name
            if '/' in name or name.startswith('.') or not path.is_file():
                return JSONResponse(status_code=404, content={'error': {'code': 'unknown_cover', 'message': name}})
            return FileResponse(path)
