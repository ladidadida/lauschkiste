"""The kiosk core module: what the screen on the box shows.

The browser on the box always opens ``/kiosk/``. When the kiosk is on, that serves the chosen kiosk app, a reduced
view a child can use; otherwise it forwards to the normal web app. Kiosk apps are modules that register at
``kiosk.apps`` (the key is the module's name, which is also where the app's settings live)::

    class MyKioskApp:
        title = 'My kiosk'               # shown in the choice, optional
        entry = 'index.html'             # the page served at /kiosk/, optional

        def directory(self) -> Path:     # the folder with the built web files
            ...

Files are served below ``/kiosk/`` relative to that folder, so a build with relative paths works as it is.
An app learns about changes of the kiosk from the event ``kiosk.state``.
"""

import logging
from pathlib import Path
from typing import List, Optional, Protocol

from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field

from lauschkiste.contract import CoreModule, event, extension_point, query

logger = logging.getLogger('lauschkiste.kiosk')

BUILT_IN_APP = 'kiosk_standard'
NORMAL_WEBAPP = '/?kiosk'
#: Build tools put content-hashed files here; a new build gives them new names.
HASHED_ASSETS_DIR = 'assets'


class KioskApp(Protocol):
    """A frontend for the screen on the box, registered at ``kiosk.apps``."""

    def directory(self) -> Path:
        """The folder with the app's built web files."""


class Choice(BaseModel):
    value: str
    label: str


class KioskSettings(BaseModel):
    enabled: bool = Field(False, title='Show the kiosk app on the screen',
                          description='On: the screen on the box shows the reduced view of the app below. '
                                      'Off: it shows the normal web app. The browser itself is set up with '
                                      '`lauschctl setup kiosk`.')
    app: str = Field(BUILT_IN_APP, title='Kiosk app', json_schema_extra={'options': '/api/v1/kiosk/apps'},
                     description='Which of the installed kiosk apps the screen shows; its own settings follow.')


class KioskState(BaseModel):
    enabled: bool
    app: str
    apps: List[Choice]


class Kiosk(CoreModule):
    """The reduced view for the screen on the box."""

    name = 'kiosk'
    interface_version = '1.0'
    concurrency = 'threadsafe'
    settings = KioskSettings

    state = event('state', KioskState)
    apps = extension_point('apps', KioskApp)

    def __init__(self):
        self._ctx = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        self.apps.on_register(lambda key, app: self._publish())

    def ready(self) -> None:
        self._publish()

    def settings_changed(self, changed) -> bool:
        self._publish()
        return True

    def _choices(self) -> List[Choice]:
        return [Choice(value=key, label=getattr(app, 'title', '') or key) for key, app in self.apps.items()]

    def _app_key(self) -> Optional[str]:
        """The chosen app, else the built-in one when the chosen is gone; None if there is none."""
        chosen = self._ctx.config.get('app', default=BUILT_IN_APP)
        for key in (chosen, BUILT_IN_APP):
            if key in self.apps:
                return key
        return None

    def _state(self) -> KioskState:
        enabled = bool(self._ctx.config.get('enabled', default=False))
        return KioskState(enabled=enabled, app=self._app_key() or '', apps=self._choices())

    def _publish(self) -> None:
        if self._ctx is not None:
            self._ctx.publish(self.state, self._state())

    @query(path='/state')
    def get_state(self) -> KioskState:
        """Whether the kiosk is on, which app the screen shows and which apps are installed."""
        return self._state()

    @query(path='/apps')
    def list_apps(self) -> List[Choice]:
        """The installed kiosk apps."""
        return self._choices()

    def extra_routes(self, router) -> None:
        @router.get('/kiosk', include_in_schema=False)
        async def kiosk_without_slash():
            return RedirectResponse('/kiosk/', status_code=307)

        @router.get('/kiosk/', include_in_schema=False)
        async def kiosk_index():
            return self._serve('')

        @router.get('/kiosk/{path:path}', include_in_schema=False)
        async def kiosk_file(path: str):
            return self._serve(path)

    def _serve(self, path: str):
        state = self._state()
        if not state.enabled or not state.app:
            return RedirectResponse(NORMAL_WEBAPP, status_code=307)
        app = self.apps.get(state.app)
        root = Path(app.directory()).resolve()
        relative = path or getattr(app, 'entry', 'index.html')
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            return PlainTextResponse('Not found', status_code=404)
        hashed = relative.split('/', 1)[0] == HASHED_ASSETS_DIR
        return FileResponse(candidate, headers={'Cache-Control': 'public, max-age=31536000, immutable' if hashed
                                                else 'no-store'})
