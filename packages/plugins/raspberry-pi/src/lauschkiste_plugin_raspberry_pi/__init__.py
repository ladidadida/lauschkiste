"""Raspberry Pi hardware control: shutdown/reboot, GPIO, battery monitor, firmware health.

Enable with::

    plugins:
      raspberry_pi:
        debug_mode: false            # log shutdown/reboot instead of doing them
        hdmi_power_down: false
        wlan_power_save: true        # false disables WLAN power saving (better reachability)
        wlan_interface: wlan0
        gpio: {enabled: false, ...}  # see gpio.py
        battery:
          enabled: false
          driver: ina219             # or 'simulator'
          shunt_ohms: 0.1
          empty_voltage: 3000
          full_voltage: 4200
          warning_voltage: 3300
          shutdown_voltage: 3000
          interval_sec: 10
          warning_action: {action: jingle.play, args: {sound: resources/audio/battery_low.wav}}

GPIO needs ``uv sync --inexact --extra gpio``, the INA219 battery sensor ``--extra battery-ina219``.
"""

import logging
import subprocess
import threading
from typing import List, Optional

import lauschkiste.cfghandler
import lauschkiste.legacy_actions as legacy_actions
from lauschkiste.contract import OperationError, Plugin, action, event, query

from lauschkiste_plugin_raspberry_pi import health
from lauschkiste_plugin_raspberry_pi.battery import (
    BatteryMonitor, BatteryState, Ina219Reader, SimulatedReader,
)

logger = logging.getLogger('jb.raspberry_pi')
cfg_main = lauschkiste.cfghandler.get_handler('jukebox')


class RaspberryPi(Plugin):
    """Shutdown and reboot, GPIO buttons/encoders/LED, battery monitor and firmware health of a Raspberry Pi."""

    name = 'raspberry_pi'
    interface_version = '1.0'
    extras = ('gpio',)

    battery = event('battery', BatteryState)

    def __init__(self):
        self._ctx = None
        self._gpio = None
        self._battery: Optional[BatteryMonitor] = None

    def _setting(self, key, legacy_keys=(), default=None):
        """Own setting first, then the pre-plugin ``host`` section, then the default."""
        missing = object()
        value = self._ctx.config.get(key, default=missing)
        if value is missing and legacy_keys:
            value = cfg_main.getn('host', *legacy_keys, default=missing)
        return default if value is missing else value

    # -- lifecycle ------------------------------------------------------------------------------

    def start(self, ctx) -> None:
        self._ctx = ctx
        if self._setting('hdmi_power_down', ('rpi', 'hdmi_power_down'), False):
            health.hdmi_power_down()
        legacy_disable = cfg_main.getn('host', 'wlan_power', 'disable_power_down', default=None)
        power_save = self._setting('wlan_power_save', default=None if legacy_disable is None else not legacy_disable)
        if power_save is False:
            health.disable_wlan_power_save(self._setting('wlan_interface', ('wlan_power', 'card'), 'wlan0'))

    def ready(self) -> None:
        gpio_config = self._ctx.config.get('gpio', default=None) or {}
        if gpio_config.get('enabled', False):
            from lauschkiste_plugin_raspberry_pi.gpio import GpioDevices
            self._gpio = GpioDevices(gpio_config, self._bind)
        battery_config = self._ctx.config.get('battery', default=None) or {}
        if battery_config.get('enabled', False):
            self._battery = self._create_battery_monitor(battery_config)
            self._battery.start()

    def stop(self) -> List[threading.Thread]:
        if self._gpio is not None:
            self._gpio.close()
        thread = self._battery.stop() if self._battery is not None else None
        return [thread] if thread is not None else []

    def _bind(self, entry):
        return legacy_actions.bind_action(self._ctx.actions, entry, 'raspberry_pi.gpio', logger)

    def _create_battery_monitor(self, config) -> BatteryMonitor:
        driver = config.get('driver', 'ina219')
        if driver == 'ina219':
            reader = Ina219Reader(float(config.get('shunt_ohms', 0.1)))
        elif driver == 'simulator':
            reader = SimulatedReader()
        else:
            raise ValueError(f"Unknown battery driver '{driver}' (known: ina219, simulator)")
        warning = config.get('warning_action')
        warning_action = self._bind(warning) if warning else None
        return BatteryMonitor(
            reader,
            empty_mv=int(config.get('empty_voltage', 3000)), full_mv=int(config.get('full_voltage', 4200)),
            warning_mv=int(config.get('warning_voltage', 3300)), shutdown_mv=int(config.get('shutdown_voltage', 3000)),
            interval_sec=float(config.get('interval_sec', 10)),
            on_state=lambda state: self._ctx.publish(self.battery, state),
            on_warning=warning_action or (lambda: None),
            on_shutdown=self.shutdown)

    def _power(self, command: List[str], what: str) -> None:
        if self._setting('debug_mode', ('debug_mode',), False):
            logger.info(f"debug_mode: not running '{' '.join(command)}' ({what})")
            return
        logger.info(what)
        try:
            subprocess.Popen(command)
        except OSError as error:
            raise OperationError(501, 'not_supported', f"{what} failed: {error}") from None

    # -- operations -----------------------------------------------------------------------------

    @action()
    def shutdown(self) -> None:
        """Shut the Raspberry Pi down."""
        self._power(['sudo', 'shutdown', '-h', 'now'], 'Shutting down')

    @action()
    def reboot(self) -> None:
        """Reboot the Raspberry Pi."""
        self._power(['sudo', 'reboot'], 'Rebooting')

    @query(path='/throttled')
    def get_throttled(self) -> health.Throttled:
        """Under-voltage and throttling flags of the firmware (``vcgencmd get_throttled``)."""
        state = health.read_throttled()
        if state is None:
            raise OperationError(501, 'not_supported', 'vcgencmd is not available')
        return state

    @query(path='/battery')
    def get_battery(self) -> Optional[BatteryState]:
        """Last battery reading, or null when the battery monitor is off or hasn't read yet."""
        return self._battery.state if self._battery is not None else None
