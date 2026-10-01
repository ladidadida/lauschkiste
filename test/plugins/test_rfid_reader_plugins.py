import importlib.util

import pytest

pytest.importorskip('lauschkiste_plugin_rfid_readers', reason="the rfid-readers plugin package is not installed")

import lauschkiste.cfghandler
import lauschkiste_plugin_rfid_readers
from lauschkiste.cfghandler import ConfigHandler
from lauschkiste.contract.manager import ModuleManager, discover_plugins
from lauschkiste.publishing.bus import EventBus
from lauschkiste.rfid.cards import Cards
from lauschkiste.rfid.reader import Rfid


@pytest.fixture
def start(tmp_path):
    main = lauschkiste.cfghandler.get_handler('jukebox')
    main.config_dict({})
    (tmp_path / 'rfid.yaml').write_text("rfid:\n  readers: {}\n")
    managers = []

    def _start(enabled):
        cfg = ConfigHandler('test')
        cfg.config_dict({
            'plugins': {name: {} for name in enabled},
            'cards': {'database': str(tmp_path / 'cards.yaml')},
            'rfid': {'reader_config': str(tmp_path / 'rfid.yaml')},
        })
        manager = ModuleManager([Cards, Rfid], cfg, EventBus(), plugins=discover_plugins(), strict=True)
        manager.load()
        manager.start()
        manager.ready()
        managers.append(manager)
        return manager

    yield _start
    for manager in managers:
        manager.stop()
    main.config_dict({})


def test_every_bundled_driver_is_an_installed_plugin():
    installed = discover_plugins()
    for name in ('generic_usb', 'fake_reader_gui', 'rdm6300_serial', 'rc522_spi', 'mfrc522_i2c',
                 'pn532_i2c_py532', 'generic_nfcpy'):
        assert f'rfid_{name}' in installed


def test_enabled_driver_plugin_registers_its_driver(start):
    manager = start(['rfid_generic_usb'])
    assert manager.failed == {}
    readers = manager.instance('rfid').readers
    assert readers.names() == ['generic_usb']
    assert isinstance(readers.get('generic_usb'), lauschkiste_plugin_rfid_readers.ReaderDriver)


def test_only_enabled_drivers_are_registered(start):
    manager = start([])
    assert manager.instance('rfid').readers.names() == []


@pytest.mark.skipif(importlib.util.find_spec('nfc') is not None, reason="nfcpy is installed")
def test_driver_with_missing_dependency_is_skipped(start):
    manager = start(['rfid_generic_usb', 'rfid_generic_nfcpy'])
    assert 'nfc' in manager.failed['rfid_generic_nfcpy']
    assert manager.instance('rfid').readers.names() == ['generic_usb']
