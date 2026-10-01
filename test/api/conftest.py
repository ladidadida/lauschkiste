import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest
from starlette.testclient import TestClient

from lauschkiste.api.events import EventBroker
from lauschkiste.api.fastapi_server import create_app
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.library.module import Library
from lauschkiste.player.module import Player
from lauschkiste.publishing.bus import EventBus


def _mocked_player(ctrl):
    """A player module whose coordinator is ``ctrl`` (no real backends)."""
    class MockedPlayer(Player):
        def start(self, ctx):
            self._ctx = ctx
            self._coordinator = ctrl

        def ready(self):
            pass

        def stop(self):
            return []

    return MockedPlayer


@contextmanager
def _api_client(core_modules, config=None):
    """A test client for ``core_modules``; a library with temporary storage is added if missing."""
    tmp = tempfile.mkdtemp()
    config = dict(config or {})
    config.setdefault('library', {'index': f'{tmp}/library.sqlite', 'cover_cache': f'{tmp}/covers',
                                  'scan_on_startup': False})
    if not any(issubclass(m, Library) for m in core_modules):
        core_modules = [Library, *core_modules]
    cfg = ConfigHandler('test')
    cfg.config_dict(config)
    manager = ModuleManager(core_modules, cfg, EventBus(), plugins={}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    executor = ThreadPoolExecutor(max_workers=1)
    app = create_app(EventBroker(), executor, modules=manager)
    try:
        with TestClient(app) as client:
            client.modules = manager
            yield client
    finally:
        manager.stop()
        executor.shutdown(wait=False, cancel_futures=True)
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def mocked_player():
    return _mocked_player


@pytest.fixture
def api_client():
    return _api_client
