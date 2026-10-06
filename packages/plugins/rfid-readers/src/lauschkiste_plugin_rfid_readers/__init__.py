"""RFID reader drivers, one plugin per driver.

Enable the driver of each reader configured in the reader config (``module: <driver>``), e.g.::

    plugins:
      rfid_generic_usb: {}
"""

import importlib
from typing import Any, ClassVar, Dict, List

from lauschkiste.contract import Plugin


class ReaderDriver:
    """Creates readers from a driver module that defines ``ReaderClass(reader_cfg_key)``."""

    def __init__(self, module):
        self._module = module

    def create_reader(self, reader_cfg_key: str) -> Any:
        return self._module.ReaderClass(reader_cfg_key)

    def claims(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Pins and buses a reader with this ``config`` uses (``claims(config)`` of the driver module)."""
        claims = getattr(self._module, 'claims', None)
        return claims(config or {}) if callable(claims) else []


class ReaderDriverPlugin(Plugin):
    driver: ClassVar[str]
    interface_version = '1.0'
    requires = {'rfid': '>=1.0,<2'}

    def start(self, ctx) -> None:
        module = importlib.import_module(f'lauschkiste_plugin_rfid_readers.{self.driver}.{self.driver}')
        ctx.modules.rfid.readers.register(self.driver, ReaderDriver(module))


def _driver_plugin(class_name: str, driver: str, extras=()) -> type:
    return type(class_name, (ReaderDriverPlugin,), {
        'name': f'rfid_{driver}',
        'driver': driver,
        'extras': tuple(extras),
        '__module__': __name__,
        '__doc__': f"RFID reader driver '{driver}'.",
    })


GenericUsb = _driver_plugin('GenericUsb', 'generic_usb')
FakeReaderGui = _driver_plugin('FakeReaderGui', 'fake_reader_gui', ['fake-reader-gui'])
Rdm6300Serial = _driver_plugin('Rdm6300Serial', 'rdm6300_serial', ['rdm6300-serial'])
Rc522Spi = _driver_plugin('Rc522Spi', 'rc522_spi', ['rc522-spi'])
Mfrc522I2c = _driver_plugin('Mfrc522I2c', 'mfrc522_i2c', ['mfrc522-i2c'])
Pn532I2cPy532 = _driver_plugin('Pn532I2cPy532', 'pn532_i2c_py532', ['pn532-i2c-py532'])
GenericNfcpy = _driver_plugin('GenericNfcpy', 'generic_nfcpy', ['generic-nfcpy'])
