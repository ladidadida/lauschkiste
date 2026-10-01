import time

import pytest

from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import CoreModule, action
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.player.module import Player
from lauschkiste.publishing.bus import EventBus


class FakeCoordinator:
    def __init__(self):
        self.volume = 50
        self.stopped = 0
        self.toggled = 0

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        return volume

    def stop(self):
        self.stopped += 1

    def toggle(self):
        self.toggled += 1


class FakePlayer(Player):
    requires = ()
    coordinator = None

    def start(self, ctx):
        self._ctx = ctx
        self._coordinator = type(self).coordinator

    def ready(self):
        pass

    def stop(self):
        return []


class Recorder(CoreModule):
    """Records calls of its actions, for modules that trigger actions."""

    name = 'recorder'
    calls = None

    @action()
    def beep(self, times: int = 1) -> None:
        type(self).calls.append(('beep', times))


def wait_for(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


@pytest.fixture
def start_modules():
    managers = []

    def _start(modules, config=None):
        cfg = ConfigHandler('test')
        cfg.config_dict(config or {})
        bus = EventBus()
        events = []
        bus.register(lambda topic, payload: events.append((topic, payload)))
        manager = ModuleManager(modules, cfg, bus, plugins={}, strict=True)
        manager.load()
        manager.start()
        manager.ready()
        managers.append(manager)
        return manager, events

    yield _start
    for manager in managers:
        for thread in manager.stop():
            thread.join(2)


@pytest.fixture
def coordinator():
    FakePlayer.coordinator = FakeCoordinator()
    return FakePlayer.coordinator


@pytest.fixture
def recorder_calls():
    Recorder.calls = []
    return Recorder.calls


@pytest.fixture
def fake_player(coordinator):
    return FakePlayer


@pytest.fixture
def recorder(recorder_calls):
    return Recorder


@pytest.fixture(name='wait_for')
def wait_for_fixture():
    return wait_for
