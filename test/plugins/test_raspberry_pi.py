import subprocess
import time
from unittest.mock import Mock

import pytest

pytest.importorskip('lauschkiste_plugin_raspberry_pi', reason="the raspberry-pi plugin package is not installed")

import lauschkiste.cfghandler
import lauschkiste_plugin_raspberry_pi as pi
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import CoreModule, action
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.publishing.bus import EventBus
from lauschkiste_plugin_raspberry_pi.battery import BatteryMonitor, state_of_charge
from lauschkiste_plugin_raspberry_pi.health import parse_throttled


class Recorder(CoreModule):
    name = 'recorder'
    calls = []

    @action()
    def hit(self, what: str = 'x') -> None:
        Recorder.calls.append(what)


@pytest.fixture(autouse=True)
def clean():
    Recorder.calls = []
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})
    yield
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})


def start(settings):
    cfg = ConfigHandler('test')
    cfg.config_dict({'plugins': {'raspberry_pi': settings}})
    bus = EventBus()
    events = []
    bus.register(lambda topic, payload: events.append((topic, payload)))
    manager = ModuleManager([Recorder], cfg, bus, plugins={'raspberry_pi': lambda: pi.RaspberryPi}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    assert manager.failed == {}
    return manager, events


def test_parse_throttled():
    state = parse_throttled('throttled=0x50005\n')
    assert state.under_voltage_now and state.throttled_now
    assert state.under_voltage_occurred and state.throttled_occurred
    assert not state.frequency_capped_now
    assert parse_throttled('throttled=0x0').model_dump(exclude={'raw'}) == dict.fromkeys(
        ['under_voltage_now', 'frequency_capped_now', 'throttled_now', 'under_voltage_occurred',
         'frequency_capped_occurred', 'throttled_occurred'], False)


def test_debug_mode_does_not_shut_down(monkeypatch):
    popen = Mock()
    monkeypatch.setattr(subprocess, 'Popen', popen)
    manager, _ = start({'debug_mode': True})
    manager.catalog.call('raspberry_pi.shutdown')
    manager.catalog.call('raspberry_pi.reboot')
    popen.assert_not_called()
    manager.stop()


def test_shutdown_runs_the_system_command(monkeypatch):
    popen = Mock()
    monkeypatch.setattr(subprocess, 'Popen', popen)
    manager, _ = start({})
    manager.catalog.call('raspberry_pi.shutdown')
    popen.assert_called_once_with(['sudo', 'shutdown', '-h', 'now'])
    manager.stop()


def test_state_of_charge():
    assert state_of_charge(3000, 3000, 4200) == 0
    assert state_of_charge(3600, 3000, 4200) == 50
    assert state_of_charge(4500, 3000, 4200) == 100


def test_battery_monitor_warns_once_and_shuts_down():
    # Readings are smoothed: 3500, 3350, 3245 (below warning), 3171.5, 2520 (below shutdown)
    readings = iter([3500, 3000, 3000, 3000, 1000])
    reader = Mock(voltage_mv=lambda: next(readings))
    warning, shutdown, states = Mock(), Mock(), []
    monitor = BatteryMonitor(reader, empty_mv=3000, full_mv=4200, warning_mv=3300, shutdown_mv=3000,
                             interval_sec=1, on_state=states.append, on_warning=warning, on_shutdown=shutdown)
    monitor.measure()
    monitor.measure()
    warning.assert_not_called()
    monitor.measure()
    monitor.measure()
    warning.assert_called_once()
    shutdown.assert_not_called()
    monitor.measure()
    shutdown.assert_called_once()
    assert states[0].soc == 42


def test_battery_events_and_warning_action(monkeypatch):
    monkeypatch.setattr(subprocess, 'Popen', Mock())
    manager, events = start({'debug_mode': True, 'battery': {
        'enabled': True, 'driver': 'simulator', 'interval_sec': 0.01, 'warning_voltage': 4099,
        'warning_action': {'action': 'recorder.hit', 'args': {'what': 'low'}}}})
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and not Recorder.calls:
        time.sleep(0.01)
    assert Recorder.calls[:1] == ['low']
    assert any(topic == 'raspberry_pi.battery' for topic, _ in events)
    assert manager.handle('raspberry_pi').invoke('get_battery') is not None
    manager.stop()


def test_gpio_buttons_run_actions():
    gpiozero = pytest.importorskip('gpiozero')
    from gpiozero.pins.mock import MockFactory

    factory = MockFactory()
    gpiozero.Device.pin_factory = factory
    try:
        manager, _ = start({'gpio': {'enabled': True, 'buttons': {
            'next': {'pin': 5, 'on_press': {'action': 'recorder.hit', 'args': {'what': 'press'}}, 'bounce_time': None},
        }}})
        pin = factory.pin(5)
        pin.drive_low()
        pin.drive_high()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not Recorder.calls:
            time.sleep(0.01)
        assert Recorder.calls == ['press']
        manager.stop()
    finally:
        gpiozero.Device.pin_factory = None
