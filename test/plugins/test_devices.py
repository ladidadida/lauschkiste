import subprocess
import time
from unittest.mock import Mock

import pytest

import lauschkiste.cfghandler
import lauschkiste_plugin_board_raspberry_pi as board_plugin
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract import CoreModule, action
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.hardware import Hardware
from lauschkiste.publishing.bus import EventBus
from lauschkiste_plugin_devices import battery, gpio_controls, power_button
from lauschkiste_plugin_devices.battery import BatteryMonitor, Max17048Reader, state_of_charge


class Recorder(CoreModule):
    name = 'recorder'
    calls = []

    @action()
    def hit(self, what: str = 'x') -> None:
        Recorder.calls.append(what)


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    Recorder.calls = []
    monkeypatch.setattr(subprocess, 'Popen', Mock())
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})
    yield
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})


PLUGINS = {
    'board_raspberry_pi': lambda: board_plugin.BoardRaspberryPi,
    'gpio_controls': lambda: gpio_controls.GpioControls,
    'battery': lambda: battery.Battery,
    'power_button': lambda: power_button.PowerButton,
}


def start(plugins):
    cfg = ConfigHandler('test')
    cfg.config_dict({'plugins': {'board_raspberry_pi': {'debug_mode': True}, **plugins}})
    bus = EventBus()
    events = []
    bus.register(lambda topic, payload: events.append((topic, payload)))
    manager = ModuleManager([Hardware, Recorder], cfg, bus, plugins=PLUGINS, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    assert manager.failed == {}
    return manager, events


@pytest.fixture
def mock_pins(monkeypatch):
    gpiozero = pytest.importorskip('gpiozero')
    from gpiozero.pins.mock import MockFactory
    factory = MockFactory()
    monkeypatch.setattr(gpio_controls.GpioControls, 'pin_factory', factory)
    monkeypatch.setattr(power_button.PowerButton, 'pin_factory', factory)
    yield factory
    gpiozero.Device.pin_factory = None


def wait(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not predicate():
        time.sleep(0.01)
    return predicate()


def test_gpio_buttons_run_actions_and_claim_their_pins(mock_pins):
    manager, _ = start({'gpio_controls': {'buttons': {
        'next': {'pin': 'GPIO5', 'on_press': {'action': 'recorder.hit', 'args': {'what': 'press'}}, 'bounce_time': None},
    }, 'status_led': 'pin22'}})
    pin = mock_pins.pin(5)
    pin.drive_low()
    pin.drive_high()
    assert wait(lambda: Recorder.calls == ['press'])
    assert mock_pins.pin(25).state == 1
    used = {p.id: [u.purpose for u in p.used_by] for p in manager.handle('hardware').invoke('get_state').pins}
    assert used['GPIO5'] == ['button next'] and used['GPIO25'] == ['status LED']
    manager.stop()


def test_power_button_shuts_down_with_the_onoff_shim_preset(mock_pins, monkeypatch):
    manager, _ = start({'power_button': {'hold_time': 0}})
    shutdown = Mock()
    monkeypatch.setattr(board_plugin.RaspberryPiBoard, 'shutdown', lambda self: shutdown())
    mock_pins.pin(17).drive_low()
    assert wait(lambda: shutdown.called)
    used = {p.id: [u.purpose for u in p.used_by] for p in manager.handle('hardware').invoke('get_state').pins}
    assert used['GPIO17'] == ['power button'] and used['GPIO4'] == ['power off']
    manager.stop()


def test_conflicting_pins_are_reported(mock_pins):
    manager, _ = start({'power_button': {}, 'gpio_controls': {'status_led': 'GPIO17'}})
    assert manager.handle('hardware').invoke('get_state').conflicts == ['GPIO17']
    manager.stop()


def test_battery_simulator_warns_and_claims_nothing():
    manager, events = start({'battery': {'driver': 'simulator', 'interval_sec': 1, 'warning_voltage': 4099,
                                         'warning_action': {'action': 'recorder.hit', 'args': {'what': 'low'}}}})
    assert wait(lambda: Recorder.calls[:1] == ['low'], 3)
    assert any(topic == 'battery.state' for topic, _ in events)
    assert manager.handle('battery').invoke('get_battery') is not None
    assert manager.handle('hardware').invoke('get_state').conflicts == []
    manager.stop()


def test_max17048_reads_voltage_and_charge():
    registers = {0x02: 0xB0C8, 0x04: 0x4F80}  # chip order: 0xC8B0 = 51376 -> 4013.75 mV; 0x804F -> 128.3 %

    class Bus:
        def read_word_data(self, address, register):
            assert address == 0x36
            return registers[register]

    reader = Max17048Reader(smbus=Bus())
    assert reader.voltage_mv() == 4014
    registers[0x04] = 0x0040  # 0x4000 -> 64 %
    assert reader.soc() == 64


def test_monitor_takes_the_gauge_charge():
    class Gauge:
        def voltage_mv(self):
            return 3700

        def soc(self):
            return 42

    states = []
    monitor = BatteryMonitor(Gauge(), empty_mv=3000, full_mv=4200, warning_mv=3300, shutdown_mv=3000,
                             interval_sec=1, on_state=states.append, on_warning=Mock(), on_shutdown=Mock())
    monitor.measure()
    assert states[0].soc == 42


def test_state_of_charge():
    assert state_of_charge(3000, 3000, 4200) == 0
    assert state_of_charge(3600, 3000, 4200) == 50
    assert state_of_charge(4500, 3000, 4200) == 100


def test_battery_monitor_warns_once_and_shuts_down():
    readings = iter([3500, 3000, 3000, 3000, 1000])
    reader = Mock(spec=['voltage_mv'], voltage_mv=lambda: next(readings))
    warning, shutdown = Mock(), Mock()
    monitor = BatteryMonitor(reader, empty_mv=3000, full_mv=4200, warning_mv=3300, shutdown_mv=3000,
                             interval_sec=1, on_state=lambda s: None, on_warning=warning, on_shutdown=shutdown)
    for _ in range(4):
        monitor.measure()
    warning.assert_called_once()
    shutdown.assert_not_called()
    monitor.measure()
    shutdown.assert_called_once()
