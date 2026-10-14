"""The kiosk app that ships with Lauschkiste: the player and the library as big tiles, without settings.

Its themes are CSS files of variables (see ``resources/kiosk-themes/``). More of them can be put in
``kiosk-themes/`` in the data directory; a file there replaces a built-in theme of the same name.
"""

import re
from pathlib import Path
from typing import List, Literal

from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

import lauschkiste.common.paths
from lauschkiste.box.kiosk.module import BUILT_IN_APP, Choice
from lauschkiste.contract import CoreModule, event, query

THEME_FOLDER = 'kiosk-themes'
THEME_NAME = re.compile(r'^[a-z0-9][a-z0-9_-]*$')


class KioskStandardSettings(BaseModel):
    theme: str = Field('night', title='Theme', json_schema_extra={'options': f'/api/v1/{BUILT_IN_APP}/themes'},
                       description=f'Looks of the screen. Your own are CSS files in "{THEME_FOLDER}" of the '
                                   'data directory.')
    text_size: Literal['normal', 'large', 'huge'] = Field('large', title='Text size')
    start_page: Literal['player', 'library'] = Field('player', title='Start page',
                                                     description='What the screen shows first and returns to.')
    show_continue: bool = Field(True, title='Offer "Continue"')
    show_music: bool = Field(True, title='Offer music')
    show_audiobooks: bool = Field(True, title='Offer audiobooks')
    show_radio: bool = Field(True, title='Offer radio')
    show_podcasts: bool = Field(True, title='Offer podcasts')
    show_volume: bool = Field(True, title='Show the volume control')


class KioskStandard(CoreModule):
    """The standard kiosk app."""

    name = BUILT_IN_APP
    interface_version = '1.0'
    concurrency = 'threadsafe'
    requires = ('kiosk',)
    settings = KioskStandardSettings

    changed = event('settings', KioskStandardSettings)

    title = 'Standard'
    entry = 'kiosk.html'

    def __init__(self):
        self._ctx = None

    def directory(self) -> Path:
        from lauschkiste.api.fastapi_server import default_webapp_build_dir
        return default_webapp_build_dir()

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.modules.kiosk.apps.register(self.name, self)

    def ready(self) -> None:
        self._publish()

    def settings_changed(self, changed) -> bool:
        self._publish()
        return True

    def _publish(self) -> None:
        values = {key: self._ctx.config.get(key, default=field.default)
                  for key, field in KioskStandardSettings.model_fields.items()}
        self._ctx.publish(self.changed, KioskStandardSettings.model_validate(values))

    # -- themes ---------------------------------------------------------------------------------

    @staticmethod
    def _theme_files() -> dict:
        folders = [lauschkiste.common.paths.resource('kiosk-themes'), lauschkiste.common.paths.home() / THEME_FOLDER]
        found = {}
        for folder in folders:
            if folder.is_dir():
                found.update({path.stem: path for path in sorted(folder.glob('*.css')) if THEME_NAME.match(path.stem)})
        return found

    @query(path='/themes')
    def list_themes(self) -> List[Choice]:
        """The themes to choose from."""
        return [Choice(value=name, label=name.replace('-', ' ').replace('_', ' ').capitalize())
                for name in sorted(self._theme_files())]

    def extra_routes(self, router) -> None:
        @router.get(f'/api/v1/{BUILT_IN_APP}/themes/{{filename}}', include_in_schema=False)
        async def theme_file(filename: str):
            path = self._theme_files().get(filename.removesuffix('.css')) if filename.endswith('.css') else None
            if path is None:
                return PlainTextResponse('Not found', status_code=404)
            return FileResponse(path, media_type='text/css', headers={'Cache-Control': 'no-store'})
