import pytest

from lauschkiste.contract import OperationError
from lauschkiste.timers import Timers


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
