"""Board support for the Raspberry Pi: 40-pin header, I²C/SPI/I²S, sound cards, power, firmware health.

Registers the board at the core ``hardware`` module. Changes of the boot configuration (sound card,
I²C, SPI, power-off pin) are written by ``lauschctl setup raspi``; the plugin reports them as pending
until then. See documentation/developers/hardware.md.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, List, Optional

import lauschkiste.cfghandler
from lauschkiste.contract import OperationError, Plugin, query
from lauschkiste.hardware import Claim

from lauschkiste_plugin_board_raspberry_pi import bootconfig, health, pins
from lauschkiste_plugin_board_raspberry_pi.settings import BoardSettings

logger = logging.getLogger('lauschkiste.board_raspberry_pi')

BOOT_CONFIG = ('/boot/firmware/config.txt', '/boot/config.txt')


class RaspberryPiBoard:
    """What the hardware module asks a board."""

    def __init__(self, plugin: 'BoardRaspberryPi'):
        self._plugin = plugin
        self._model = pins.model()
        self._chip = pins.gpio_chip(self._model)

    def describe(self):
        return {'name': 'raspberry_pi', 'model': self._model or 'Raspberry Pi', 'pins': pins.pins(),
                'interfaces': pins.INTERFACES}

    def pin_id(self, value) -> Optional[str]:
        return pins.pin_id(value)

    def gpio_line(self, pin: str):
        return self._chip, int(pin[4:])

    def shutdown(self) -> None:
        self._plugin.power(['sudo', 'shutdown', '-h', 'now'], 'Shutting down')

    def reboot(self) -> None:
        self._plugin.power(['sudo', 'reboot'], 'Rebooting')

    def boot_pending(self) -> List[str]:
        return self._plugin.boot_pending()


class BoardClaims:
    def __init__(self, plugin: 'BoardRaspberryPi'):
        self._plugin = plugin

    def claims(self) -> List[Claim]:
        card = self._plugin.setting('sound_card', 'none')
        return [Claim(resource='i2s', owner='board_raspberry_pi', purpose=f'sound card {card}')] \
            if card != 'none' else []


class BoardRaspberryPi(Plugin):
    """Raspberry Pi board support: pins, interfaces, sound cards, shutdown/reboot and firmware health."""

    name = 'board_raspberry_pi'
    title = 'Raspberry Pi'
    interface_version = '1.0'
    requires = {'hardware': '>=1.0,<2'}
    provides = ('board', 'gpio', 'i2c', 'spi', 'i2s', 'uart', 'poweroff')
    settings = BoardSettings

    @classmethod
    def detect(cls, read):
        model = (read('/proc/device-tree/model') or '').strip('\x00\n ')
        return model if 'Raspberry Pi' in model else None

    def __init__(self):
        self._ctx: Any = None

    def setting(self, key, default=None):
        return self._ctx.config.get(key, default=default)

    def start(self, ctx) -> None:
        self._ctx = ctx
        if self.setting('hdmi_power_down', False):
            health.hdmi_power_down()
        if self.setting('wlan_power_save', None) is False:
            health.disable_wlan_power_save(self.setting('wlan_interface', 'wlan0'))
        hardware = ctx.modules.hardware
        hardware.boards.register('raspberry_pi', RaspberryPiBoard(self))
        hardware.claims.register('board_raspberry_pi', BoardClaims(self))

    def settings_changed(self, changed):
        return set(changed) <= {'debug_mode', 'sound_card', 'onboard_audio', 'i2c', 'spi'}

    def power(self, command: List[str], what: str) -> None:
        if self.setting('debug_mode', False):
            logger.info(f"debug_mode: not running '{' '.join(command)}' ({what})")
            return
        logger.info(what)
        try:
            subprocess.Popen(command)
        except OSError as error:
            raise OperationError(501, 'not_supported', f"{what} failed: {error}") from None

    def boot_pending(self) -> List[str]:
        path = next((Path(p) for p in BOOT_CONFIG if Path(p).exists()), None)
        if path is None:
            return []
        main = lauschkiste.cfghandler.get_handler('lauschkiste')
        rfid = lauschkiste.cfghandler.get_handler('rfid')
        want = bootconfig.wanted({'plugins': main.getn('plugins', default=None) or {}},
                                 {'rfid': rfid.getn('rfid', default=None) or {}})
        return bootconfig.pending(path.read_text(), want)

    @query(path='/throttled')
    def get_throttled(self) -> health.Throttled:
        """Under-voltage and throttling flags of the firmware (``vcgencmd get_throttled``)."""
        state = health.read_throttled()
        if state is None:
            raise OperationError(501, 'not_supported', 'vcgencmd is not available')
        return state
