import subprocess
from unittest.mock import Mock

import pytest

import lauschkiste.cfghandler
import lauschkiste_plugin_board_raspberry_pi as board_plugin
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract.manager import ModuleManager
from lauschkiste.hardware import Hardware
from lauschkiste.publishing.bus import EventBus
from lauschkiste_plugin_board_raspberry_pi import bootconfig, pins
from lauschkiste_plugin_board_raspberry_pi.health import parse_throttled


@pytest.fixture(autouse=True)
def clean():
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})
    yield
    lauschkiste.cfghandler.get_handler('lauschkiste').config_dict({})


def start(settings):
    cfg = ConfigHandler('test')
    cfg.config_dict({'plugins': {'board_raspberry_pi': settings}})
    manager = ModuleManager([Hardware], cfg, EventBus(),
                            plugins={'board_raspberry_pi': lambda: board_plugin.BoardRaspberryPi}, strict=True)
    manager.load()
    manager.start()
    manager.ready()
    assert manager.failed == {}
    return manager


def test_pin_names():
    assert pins.pin_id(17) == pins.pin_id('17') == pins.pin_id('GPIO17') == pins.pin_id('bcm17') == 'GPIO17'
    assert pins.pin_id('pin11') == 'GPIO17'
    assert pins.pin_id('pin1') is None and pins.pin_id(28) is None and pins.pin_id('x') is None
    header = pins.pins()
    assert len(header) == 40 and header[10]['id'] == 'GPIO17'
    assert 'i2c1.sda' in header[2]['functions'] and header[0]['functions'] == ['power']


def test_board_in_the_hardware_module(monkeypatch):
    popen = Mock()
    monkeypatch.setattr(subprocess, 'Popen', popen)
    manager = start({'sound_card': 'max98357a'})
    hardware = manager.handle('hardware')
    state = hardware.invoke('get_state')
    pins_by_id = {pin.id: pin for pin in state.pins}
    assert state.board == 'raspberry_pi'
    assert [u.purpose for u in pins_by_id['GPIO18'].used_by] == ['sound card max98357a']
    assert hardware.invoke('gpio_line', 'pin11').line == 17
    hardware.invoke('shutdown')
    popen.assert_called_once_with(['sudo', 'shutdown', '-h', 'now'])
    manager.stop()


def test_debug_mode_does_not_shut_down(monkeypatch):
    popen = Mock()
    monkeypatch.setattr(subprocess, 'Popen', popen)
    manager = start({'debug_mode': True})
    manager.handle('hardware').invoke('shutdown')
    manager.handle('hardware').invoke('reboot')
    popen.assert_not_called()
    manager.stop()


def test_parse_throttled():
    state = parse_throttled('throttled=0x50005\n')
    assert state.under_voltage_now and state.throttled_now
    assert state.under_voltage_occurred and state.throttled_occurred
    assert not state.frequency_capped_now


CONFIG = 'dtparam=audio=on\n[all]\n'


def test_boot_config_from_the_settings():
    want = bootconfig.wanted(
        {'plugins': {'board_raspberry_pi': {'sound_card': 'max98357a'},
                     'battery': {'driver': 'max17048'},
                     'power_button': {'preset': 'onoff_shim'}}},
        {'rfid': {'readers': {'read_00': {'module': 'rc522_spi'}}}})
    assert (want.sound_card, want.onboard_audio, want.i2c, want.spi) == ('max98357a', False, True, True)
    assert want.poweroff_line() is None
    assert sorted(bootconfig.pending(CONFIG, want)) == sorted(
        ['sound card max98357a', 'on-chip audio off', 'I²C on', 'SPI on'])
    text = bootconfig.render(CONFIG, want)
    assert 'dtparam=audio=off' in text and 'dtoverlay=max98357a' in text
    assert 'dtparam=i2c_arm=on' in text and 'dtparam=spi=on' in text
    assert bootconfig.pending(text, want) == []
    assert bootconfig.render(text, want) == text


def test_power_off_pin_and_replaced_sound_card():
    want = bootconfig.wanted({'plugins': {'board_raspberry_pi': {'sound_card': 'hifiberry-dac'},
                                          'power_button': {'preset': 'custom', 'poweroff_pin': 'GPIO4'}}})
    text = bootconfig.render('dtoverlay=max98357a\ndtoverlay=gpio-poweroff,gpiopin=26\n', want)
    assert 'max98357a' not in text and text.count('dtoverlay=hifiberry-dac') == 1
    assert 'dtoverlay=gpio-poweroff,gpiopin=4,active_low=1' in text and 'gpiopin=26' not in text


def test_nothing_wanted_changes_nothing():
    want = bootconfig.wanted({'plugins': {'board_raspberry_pi': {}}})
    assert bootconfig.pending(CONFIG, want) == [] and bootconfig.render(CONFIG, want) == CONFIG
