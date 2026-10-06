import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Protocol

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError
from starlette.testclient import TestClient

from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import (
    ActionError, ContractError, CoreModule, OperationError, Plugin, action, event, extension_point, query,
)
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.contract.routes import build_router
from lauschkiste.publishing.bus import EventBus


class Level(BaseModel):
    volume: int


class Speaker(Protocol):
    def play(self, path: str) -> None: ...


class Volume(CoreModule):
    name = 'volume'
    level = event('level', Level)
    speakers = extension_point('speakers', Speaker)

    def __init__(self):
        self.value = 30
        self.ctx = None

    def start(self, ctx):
        self.ctx = ctx
        self.value = ctx.config.setdefault('startup', value=30)

    @action(method='PUT', path='/level')
    def set_volume(self, volume: int) -> None:
        """Set the volume."""
        if volume < 0:
            raise OperationError(400, 'invalid_volume', 'Volume must not be negative')
        self.value = volume
        self.ctx.publish(self.level, Level(volume=volume))

    @action()
    def mute(self) -> None:
        self.value = 0

    @query(path='/level')
    def get_volume(self) -> int:
        return self.value

    @query()
    def unsupported(self) -> int:
        raise NotImplementedError('not here')


class Player(CoreModule):
    name = 'player'
    requires = {'volume': '>=1.0,<2'}

    def start(self, ctx):
        self.ctx = ctx

    @action()
    def play_folder(self, folder: str, recursive: bool = False) -> None:
        self.played = (folder, recursive)

    @query(path='/items/{kind}')
    def items(self, kind: str, tags: Optional[List[str]] = None) -> dict:
        return {'kind': kind, 'tags': tags}


def make_manager(core, plugins=None, enabled=None, strict=True):
    cfg = ConfigHandler('test')
    cfg.config_dict({'plugins': enabled or {}})
    bus = EventBus()
    manager = ModuleManager(core, cfg, bus, plugins=plugins or {}, strict=strict)
    manager.load()
    manager.start()
    manager.ready()
    return manager, bus, cfg


def test_start_order_follows_requires():
    started = []

    class A(CoreModule):
        name = 'a'
        requires = ('b',)

        def start(self, ctx):
            started.append('a')

    class B(CoreModule):
        name = 'b'

        def start(self, ctx):
            started.append('b')

    manager, _, _ = make_manager([A, B])
    assert started == ['b', 'a']
    assert [h.name for h in manager.handles()] == ['b', 'a']


def test_cycle_is_an_error():
    class A(CoreModule):
        name = 'a'
        requires = ('b',)

    class B(CoreModule):
        name = 'b'
        requires = ('a',)

    with pytest.raises(ContractError, match='cycle'):
        make_manager([A, B])


def test_core_missing_dependency_is_fatal():
    class A(CoreModule):
        name = 'a'
        requires = ('nope',)

    with pytest.raises(ContractError, match="requires 'nope'"):
        make_manager([A])


def test_declaration_needs_annotations():
    class Bad(CoreModule):
        name = 'bad'

        @action()
        def run(self, value):
            pass

    with pytest.raises(ContractError, match='type annotation'):
        make_manager([Bad])


def test_plugins_are_opt_in():
    loaded = []

    class Extra(Plugin):
        name = 'extra'

    def load():
        loaded.append('extra')
        return Extra

    manager, _, _ = make_manager([Volume], plugins={'extra': load})
    assert loaded == []
    assert 'extra' not in manager

    manager, _, _ = make_manager([Volume], plugins={'extra': load}, enabled={'extra': {}})
    assert 'extra' in manager


def test_only_one_board_and_needs_must_be_provided():
    class BoardA(Plugin):
        name = 'board_a'
        provides = ('board', 'gpio')

    class BoardB(Plugin):
        name = 'board_b'
        provides = ('board', 'gpio', 'i2c')

    class Button(Plugin):
        name = 'button'
        needs = ('gpio',)

    class Sensor(Plugin):
        name = 'sensor'
        needs = ('i2c',)

    found = {cls.name: (lambda cls=cls: cls) for cls in (BoardA, BoardB, Button, Sensor)}
    enabled = {'board_a': {}, 'board_b': {}, 'button': {}, 'sensor': {}}
    manager, _, _ = make_manager([Volume], plugins=found, enabled=enabled)
    assert 'board_a' in manager and 'button' in manager
    assert 'board_b' not in manager and "'board_a'" in manager.failed['board_b']
    assert 'sensor' not in manager and 'i2c' in manager.failed['sensor']

    manager, _, _ = make_manager([Volume], plugins=found, enabled={'button': {}})
    assert 'button' not in manager and 'gpio' in manager.failed['button']


def test_plugin_problems_skip_only_the_plugin_and_its_dependents():
    class Broken(Plugin):
        name = 'broken'

        def start(self, ctx):
            raise RuntimeError('boom')

    class Dependent(Plugin):
        name = 'dependent'
        requires = ('broken',)

    class Future(Plugin):
        name = 'future'
        contract = '>=9'

    class TooNew(Plugin):
        name = 'toonew'
        requires = {'volume': '>=2'}

    plugins = {c.name: (lambda c=c: c) for c in (Broken, Dependent, Future, TooNew)}
    enabled = {'broken': {}, 'dependent': {}, 'future': {}, 'toonew': {}, 'missing': {}}
    manager, _, _ = make_manager([Volume], plugins=plugins, enabled=enabled)

    assert [h.name for h in manager.handles()] == ['volume']
    assert set(manager.failed) == {'broken', 'dependent', 'future', 'toonew', 'missing'}
    assert 'boom' in manager.failed['broken']
    assert 'contract' in manager.failed['future']
    assert '>=2' in manager.failed['toonew']
    assert 'not installed' in manager.failed['missing']


def test_core_start_failure_is_fatal():
    class Broken(CoreModule):
        name = 'broken'

        def start(self, ctx):
            raise RuntimeError('boom')

    with pytest.raises(RuntimeError, match='boom'):
        make_manager([Broken])


def test_plugin_config_section_and_core_must_not_require_plugins():
    seen = {}

    class Extra(Plugin):
        name = 'extra'

        def start(self, ctx):
            seen['host'] = ctx.config.get('host')

    make_manager([Volume], plugins={'extra': lambda: Extra}, enabled={'extra': {'host': 'box'}})
    assert seen == {'host': 'box'}

    class NeedsPlugin(CoreModule):
        name = 'needs'
        requires = ('extra',)

    with pytest.raises(ContractError, match='must not require plugin'):
        make_manager([NeedsPlugin], plugins={'extra': lambda: Extra}, enabled={'extra': {}})


def test_modules_view_is_restricted_to_requires():
    manager, _, _ = make_manager([Volume, Player])
    ctx = manager.handle('player').context
    ctx.modules.volume.set_volume(12)
    assert ctx.modules.volume.get_volume() == 12
    with pytest.raises(ContractError, match='requires'):
        manager.handle('volume').context.modules.player


def test_events_are_typed():
    manager, bus, _ = make_manager([Volume])
    received = []
    bus.register(lambda topic, payload: received.append((topic, payload)))
    ctx = manager.handle('volume').context
    ctx.publish(Volume.level, {'volume': 5})
    assert received == [('volume.level', {'volume': 5})]

    with pytest.raises(ValidationError):
        ctx.publish(Volume.level, {'volume': 'loud'})

    with pytest.raises(ContractError, match='did not declare'):
        ctx.publish(event('other', Level), {'volume': 1})


def test_invalid_events_are_dropped_outside_strict_mode():
    manager, bus, _ = make_manager([Volume], strict=False)
    received = []
    bus.register(lambda topic, payload: received.append(topic))
    manager.handle('volume').context.publish(Volume.level, {'volume': 'loud'})
    assert received == []


def test_serialized_module_runs_one_operation_at_a_time():
    active = []
    overlap = []

    class Slow(CoreModule):
        name = 'slow'

        @action()
        def work(self) -> None:
            active.append(1)
            if len(active) > 1:
                overlap.append(True)
            time.sleep(0.05)
            active.pop()

    manager, _, _ = make_manager([Slow])
    handle = manager.handle('slow')
    threads = [threading.Thread(target=handle.invoke, args=('work',)) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert overlap == []


def test_extension_point_checks_protocol():
    manager, _, _ = make_manager([Volume])
    speakers = manager.instance('volume').speakers

    class Good:
        def play(self, path):
            pass

    speakers.register('good', Good())
    assert speakers.names() == ['good']
    with pytest.raises(ContractError, match='missing'):
        speakers.register('bad', object())


def test_action_catalog_validates_arguments():
    manager, _, _ = make_manager([Volume, Player])
    assert 'player.play_folder' in manager.catalog
    assert 'volume.get_volume' not in manager.catalog
    manager.catalog.call('player.play_folder', {'folder': 'Rock'})
    assert manager.instance('player').played == ('Rock', False)

    with pytest.raises(ActionError, match='folder'):
        manager.catalog.validate('player.play_folder', {})
    with pytest.raises(ActionError, match='extra'):
        manager.catalog.validate('player.play_folder', {'folder': 'x', 'extra': 1})
    with pytest.raises(ActionError, match='Unknown action'):
        manager.catalog.validate('player.nope', {})


@pytest.fixture
def client():
    manager, _, _ = make_manager([Volume, Player])
    executor = ThreadPoolExecutor(max_workers=2)
    app = FastAPI()
    app.include_router(build_router(manager, executor))
    with TestClient(app) as test_client:
        yield test_client, manager
    executor.shutdown(wait=False)


def test_generated_routes(client):
    http, manager = client
    assert http.put('/api/v1/volume/level', json={'volume': 20}).status_code == 204
    assert http.get('/api/v1/volume/level').json() == 20
    assert http.post('/api/v1/volume/mute').status_code == 204
    assert manager.instance('volume').value == 0

    response = http.post('/api/v1/player/play_folder', json={'folder': 'Jazz', 'recursive': True})
    assert response.status_code == 204
    assert manager.instance('player').played == ('Jazz', True)

    response = http.get('/api/v1/player/items/album', params=[('tags', 'a'), ('tags', 'b')])
    assert response.json() == {'kind': 'album', 'tags': ['a', 'b']}


def test_generated_route_errors(client):
    http, _ = client
    assert http.put('/api/v1/volume/level', json={'volume': 'x'}).status_code == 422
    assert http.post('/api/v1/player/play_folder', json={}).status_code == 422
    response = http.put('/api/v1/volume/level', json={'volume': -1})
    assert response.status_code == 400
    assert response.json() == {'error': {'code': 'invalid_volume', 'message': 'Volume must not be negative'}}
    assert http.get('/api/v1/volume/unsupported').status_code == 501


def test_modules_endpoint(client):
    http, _ = client
    body = http.get('/api/v1/modules').json()
    modules = {m['name']: m for m in body['modules']}
    assert set(modules) == {'volume', 'player'}
    assert modules['volume']['events']['level']['topic'] == 'volume.level'
    assert {'name': 'set_volume', 'kind': 'action', 'id': 'volume.set_volume', 'method': 'PUT',
            'path': '/api/v1/volume/level'} in modules['volume']['operations']
    assert modules['volume']['extension_points'] == ['speakers']
    actions = {a['id'] for a in http.get('/api/v1/actions').json()}
    assert actions == {'volume.set_volume', 'volume.mute', 'player.play_folder'}


def test_ready_runs_after_all_modules_started():
    calls = []

    class A(CoreModule):
        name = 'a'

        def start(self, ctx):
            calls.append('start a')

        def ready(self):
            calls.append('ready a')

    class B(CoreModule):
        name = 'b'
        requires = ('a',)

        def start(self, ctx):
            calls.append('start b')

        def ready(self):
            calls.append('ready b')

    make_manager([B, A])
    assert calls == ['start a', 'start b', 'ready a', 'ready b']


def test_extension_point_listeners_see_past_and_future_registrations():
    manager, _, _ = make_manager([Volume])
    speakers = manager.instance('volume').speakers

    class Good:
        def play(self, path):
            pass

    speakers.register('first', Good())
    seen = []
    speakers.on_register(lambda key, impl: seen.append(key))
    speakers.register('second', Good())
    assert seen == ['first', 'second']


def test_operation_name_can_differ_from_method_name():
    class Deck(CoreModule):
        name = 'deck'

        @action(name='stop')
        def stop_playback(self) -> None:
            self.stopped = True

    manager, _, _ = make_manager([Deck])
    manager.catalog.call('deck.stop')
    assert manager.instance('deck').stopped
