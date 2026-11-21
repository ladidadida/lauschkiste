import pytest

from lauschkiste.contract import OperationError
from lauschkiste.box.timers import Timers


@pytest.fixture
def timers(start_modules, recorder):
    config = {'timers': {'beep': {'action': 'recorder.beep', 'args': {'times': 2}, 'default_timeout_sec': 0.1}}}
    manager, events = start_modules([recorder, Timers], config)
    return manager.handle('timers'), events


def test_timer_runs_its_action_when_it_expires(timers, recorder_calls, wait_for):
    handle, events = timers
    state = handle.invoke('start', 'beep')
    assert state.enabled and state.remaining_seconds > 0
    assert wait_for(lambda: recorder_calls == [('beep', 2)])
    last = [p for t, p in events if t == 'timers.changed' and p['name'] == 'beep'][-1]
    assert last['enabled'] is False


def test_cancelled_timer_does_not_fire(timers, recorder_calls):
    handle, _ = timers
    handle.invoke('start', 'beep', 0.3)
    assert handle.invoke('cancel', 'beep').enabled is False
    import time
    time.sleep(0.4)
    assert recorder_calls == []


def test_toggle(timers):
    handle, _ = timers
    assert handle.invoke('toggle', 'beep', 5).enabled is True
    assert handle.invoke('toggle', 'beep').enabled is False


def test_default_timers_and_availability(timers):
    handle, _ = timers
    states = {t.name: t for t in handle.invoke('list_timers')}
    assert set(states) == {'stop_player', 'fade_volume', 'shutdown', 'beep'}
    assert states['beep'].available is True
    assert states['shutdown'].available is False
    with pytest.raises(OperationError) as error:
        handle.invoke('start', 'shutdown')
    assert error.value.code == 'timer_unavailable'


def test_unknown_timer_and_invalid_timeout(timers):
    handle, _ = timers
    with pytest.raises(OperationError) as error:
        handle.invoke('start', 'nope')
    assert error.value.status == 404
    with pytest.raises(OperationError):
        handle.invoke('start', 'beep', -1)


@pytest.fixture
def every_start(start_modules, recorder):
    def _start(minutes, fade=True):
        config = {'timers': {'every_start_minutes': minutes, 'every_start_fade': fade,
                             'fade_volume': {'action': 'recorder.beep', 'args': {}},
                             'stop_player': {'action': 'recorder.beep', 'args': {}}}}
        manager, _events = start_modules([recorder, Timers], config)
        return manager._bus, manager.handle('timers')
    return _start


def _states(handle):
    return {t.name: t for t in handle.invoke('list_timers')}


def test_every_start_starts_the_sleep_timer_when_playback_starts(every_start, wait_for):
    bus, handle = every_start(30)
    bus.publish('player.status', {'state': 'play'})
    assert wait_for(lambda: _states(handle)['fade_volume'].enabled)
    assert _states(handle)['fade_volume'].wait_seconds == 1800
    assert not _states(handle)['stop_player'].enabled


def test_every_start_starts_again_after_a_stop_but_not_while_running(every_start, wait_for):
    bus, handle = every_start(10, fade=False)
    bus.publish('player.status', {'state': 'play'})
    assert wait_for(lambda: _states(handle)['stop_player'].enabled)
    handle.invoke('start', 'stop_player', 100)
    bus.publish('player.status', {'state': 'pause'})
    bus.publish('player.status', {'state': 'play'})
    import time
    time.sleep(0.1)
    assert _states(handle)['stop_player'].wait_seconds == 100
    handle.invoke('cancel', 'stop_player')
    bus.publish('player.status', {'state': 'stop'})
    bus.publish('player.status', {'state': 'play'})
    assert wait_for(lambda: _states(handle)['stop_player'].enabled)
    assert _states(handle)['stop_player'].wait_seconds == 600


def test_every_start_off_by_default(every_start):
    bus, handle = every_start(0)
    bus.publish('player.status', {'state': 'play'})
    import time
    time.sleep(0.1)
    assert not any(state.enabled for state in _states(handle).values())
