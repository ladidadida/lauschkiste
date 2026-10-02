import sys
import types

import pytest

from lauschkiste.contract import OperationError
from lauschkiste.volume import Volume


def levels(events):
    return [payload for topic, payload in events if topic == 'volume.level']


@pytest.fixture
def volume(start_modules, coordinator, fake_player):
    manager, events = start_modules([fake_player, Volume], {'volume': {'mixer': 'player', 'soft_max_volume': 80}})
    return manager.handle('volume'), coordinator, events


def test_set_volume_is_limited_to_soft_max(volume):
    handle, coordinator, events = volume
    assert handle.invoke('set_volume', 90).volume == 80
    assert coordinator.volume == 80
    assert levels(events)[-1] == {'volume': 80, 'mute': False, 'soft_max_volume': 80}


def test_change_volume(volume):
    handle, coordinator, _ = volume
    handle.invoke('set_volume', 30)
    assert handle.invoke('change_volume', -10).volume == 20
    assert handle.invoke('change_volume', -50).volume == 0


def test_mute_toggles_and_restores(volume):
    handle, coordinator, _ = volume
    handle.invoke('set_volume', 40)
    state = handle.invoke('mute')
    assert (state.mute, state.volume, coordinator.volume) == (True, 0, 0)
    state = handle.invoke('mute')
    assert (state.mute, state.volume, coordinator.volume) == (False, 40, 40)


def test_lowering_soft_max_lowers_volume(volume):
    handle, coordinator, _ = volume
    handle.invoke('set_volume', 70)
    assert handle.invoke('set_soft_max_volume', 50).volume == 50
    assert handle.invoke('set_volume', 60).volume == 50


def test_player_mixer_has_one_output(volume):
    handle, _, _ = volume
    assert handle.invoke('get_outputs').active == 'player'
    with pytest.raises(OperationError):
        handle.invoke('set_output', 'speaker')


def test_fade_out_stops_playback_and_restores_volume(volume, wait_for):
    handle, coordinator, _ = volume
    handle.invoke('set_volume', 60)
    seen = []
    original = coordinator.set_volume
    coordinator.set_volume = lambda v: seen.append(v) or original(v)
    handle.invoke('fade_out', 0.2)
    assert wait_for(lambda: coordinator.stopped == 1)
    assert wait_for(lambda: coordinator.volume == 60)
    assert min(seen) == 0


def test_startup_volume(start_modules, coordinator, fake_player):
    start_modules([fake_player, Volume], {'volume': {'mixer': 'player', 'startup_volume': 33}})
    assert coordinator.volume == 33


class FakeSink:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.mute = 0
        self.volume = 0.5


class FakePulse:
    sinks = {}
    default = None
    moved = []

    def __init__(self, client_name):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def server_info(self):
        return types.SimpleNamespace(default_sink_name=FakePulse.default)

    def get_sink_by_name(self, name):
        if name not in FakePulse.sinks:
            raise KeyError(name)
        return FakePulse.sinks[name]

    def volume_get_all_chans(self, sink):
        return sink.volume

    def volume_set_all_chans(self, sink, value):
        sink.volume = value

    def mute(self, sink, mute=True):
        sink.mute = int(mute)

    def sink_list(self):
        return list(FakePulse.sinks.values())

    def default_set(self, sink):
        FakePulse.default = sink.name

    def sink_input_list(self):
        return [types.SimpleNamespace(index=7)]

    def sink_input_move(self, index, sink_index):
        FakePulse.moved.append((index, sink_index))


@pytest.fixture
def pulse(monkeypatch):
    FakePulse.sinks = {'speakers': FakeSink('speakers', 0), 'headset': FakeSink('headset', 1)}
    FakePulse.default = 'speakers'
    FakePulse.moved = []
    monkeypatch.setitem(sys.modules, 'pulsectl', types.SimpleNamespace(Pulse=FakePulse))
    return FakePulse


def test_pulse_mixer_scales_by_volume_limit_and_switches_outputs(start_modules, coordinator, pulse, fake_player):
    config = {'volume': {'outputs': {
        'primary': {'alias': 'Speakers', 'pulse_sink_name': 'speakers', 'volume_limit': 50},
        'secondary': {'alias': 'Headset', 'pulse_sink_name': 'headset'},
    }}}
    manager, _ = start_modules([fake_player, Volume], config)
    handle = manager.handle('volume')

    handle.invoke('set_volume', 80)
    assert pulse.sinks['speakers'].volume == pytest.approx(0.4)
    assert handle.invoke('get_volume').volume == 80

    outputs = handle.invoke('toggle_output')
    assert outputs.active == 'secondary'
    assert pulse.default == 'headset'
    assert pulse.moved == [(7, 1)]
