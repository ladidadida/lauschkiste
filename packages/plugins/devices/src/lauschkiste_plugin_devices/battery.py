"""The battery plugin: voltage and state of charge from a sensor, warning and shutdown levels.

Drivers: INA219 (voltage), MAX17048 (fuel gauge with its own state of charge), simulator. Both
sensors are on I²C; ``i2c_bus`` is the Linux bus number (``/dev/i2c-1`` on a Raspberry Pi).
"""

import logging
import threading
from typing import Any, Callable, List, Literal, Optional, Protocol

from pydantic import BaseModel, Field

from lauschkiste.contract import ActionEntry, Plugin, event, query
from lauschkiste.hardware import Claim

logger = logging.getLogger('lauschkiste.battery')


class BatteryState(BaseModel):
    voltage_mv: int
    soc: int
    warning: bool


class VoltageReader(Protocol):
    def voltage_mv(self) -> int: ...


class Ina219Reader:
    """INA219 current/voltage sensor."""

    def __init__(self, shunt_ohms: float, bus: int = 1):
        from ina219 import INA219
        self._adc = INA219(shunt_ohms, busnum=bus)
        self._adc.configure(self._adc.RANGE_16V, self._adc.GAIN_AUTO, self._adc.ADC_32SAMP, self._adc.ADC_32SAMP)

    def voltage_mv(self) -> int:
        return int(self._adc.supply_voltage() * 1000)


class Max17048Reader:
    """MAX17048 fuel gauge: cell voltage and its own state of charge (ModelGauge)."""

    ADDRESS = 0x36
    VCELL = 0x02
    SOC = 0x04

    def __init__(self, bus: int = 1, address: int = ADDRESS, smbus=None):
        if smbus is None:
            from smbus2 import SMBus
            smbus = SMBus(bus)
        self._bus = smbus
        self._address = address

    def _word(self, register: int) -> int:
        value = self._bus.read_word_data(self._address, register)
        return ((value & 0xFF) << 8) | (value >> 8)

    def voltage_mv(self) -> int:
        return int(round(self._word(self.VCELL) * 78.125 / 1000))

    def soc(self) -> int:
        return int(max(0, min(100, round(self._word(self.SOC) / 256))))


class SimulatedReader:
    """Discharges from ``start_mv`` by ``step_mv`` per reading; for trying things out without hardware."""

    def __init__(self, start_mv: int = 4100, step_mv: int = 5):
        self._value = start_mv
        self._step = step_mv

    def voltage_mv(self) -> int:
        value = self._value
        self._value = max(0, self._value - self._step)
        return value


def state_of_charge(voltage_mv: float, empty_mv: int, full_mv: int) -> int:
    if full_mv <= empty_mv:
        return 0
    return int(max(0, min(100, round((voltage_mv - empty_mv) * 100 / (full_mv - empty_mv)))))


class BatteryMonitor:
    """Reads the voltage periodically, smooths it and reports; below the thresholds warns or shuts down."""

    def __init__(self, reader: VoltageReader, *, empty_mv: int, full_mv: int, warning_mv: int, shutdown_mv: int,
                 interval_sec: float, on_state: Callable[[BatteryState], None], on_warning: Callable[[], None],
                 on_shutdown: Callable[[], None]):
        self._reader = reader
        self._empty = empty_mv
        self._full = full_mv
        self._warning_mv = warning_mv
        self._shutdown_mv = shutdown_mv
        self._interval = interval_sec
        self._on_state = on_state
        self._on_warning = on_warning
        self._on_shutdown = on_shutdown
        self._filtered: Optional[float] = None
        self._warned = False
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.state: Optional[BatteryState] = None

    def measure(self) -> BatteryState:
        raw = self._reader.voltage_mv()
        self._filtered = raw if self._filtered is None else 0.7 * self._filtered + 0.3 * raw
        voltage = int(round(self._filtered))
        gauge = getattr(self._reader, 'soc', None)
        soc = gauge() if callable(gauge) else state_of_charge(voltage, self._empty, self._full)
        self.state = BatteryState(voltage_mv=voltage, soc=soc, warning=voltage < self._warning_mv)
        self._on_state(self.state)
        if voltage < self._shutdown_mv:
            logger.warning(f"Battery at {voltage} mV, below {self._shutdown_mv} mV: shutting down")
            self._on_shutdown()
        elif voltage < self._warning_mv and not self._warned:
            self._warned = True
            logger.warning(f"Battery low: {voltage} mV")
            self._on_warning()
        elif voltage >= self._warning_mv:
            self._warned = False
        return self.state

    def _run(self):
        while not self._stop.is_set():
            try:
                self.measure()
            except Exception as error:
                logger.error(f"Reading the battery failed: {error}")
            self._stop.wait(self._interval)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name='battery.monitor', daemon=True)
        self._thread.start()

    def stop(self) -> Optional[threading.Thread]:
        self._stop.set()
        return self._thread


class BatterySettings(BaseModel):
    driver: Literal['ina219', 'max17048', 'simulator'] = Field('max17048', title='Sensor')
    i2c_bus: int = Field(1, ge=0, le=20, title='I²C bus', description='Linux bus number (/dev/i2c-1 is 1)')
    shunt_ohms: float = Field(0.1, gt=0, title='Shunt resistor (ohms)', description='INA219 only')
    empty_voltage: int = Field(3000, ge=0, title='Empty at (mV)', description='Not used by the MAX17048')
    full_voltage: int = Field(4200, ge=0, title='Full at (mV)', description='Not used by the MAX17048')
    warning_voltage: int = Field(3300, ge=0, title='Warn below (mV)')
    shutdown_voltage: int = Field(3000, ge=0, title='Shut down below (mV)')
    interval_sec: float = Field(10, ge=1, le=600, title='Measure every (seconds)')
    warning_action: Optional[ActionEntry] = Field(None, title='When the battery runs low')


class BatteryClaims:
    def __init__(self, ctx):
        self._ctx = ctx

    def claims(self) -> List[Claim]:
        driver = self._ctx.config.get('driver', default='max17048')
        if driver == 'simulator':
            return []
        return [Claim(resource=f"i2c{self._ctx.config.get('i2c_bus', default=1)}", owner='battery',
                      purpose=f'{driver} battery sensor', shared=True)]


class Battery(Plugin):
    """Battery monitor: state of charge, warning action and clean shutdown when it runs empty."""

    name = 'battery'
    interface_version = '1.0'
    needs = ('i2c',)
    requires = {'hardware': '>=1.0,<2'}
    extras = ('battery',)
    settings = BatterySettings

    state = event('state', BatteryState)

    def __init__(self):
        self._ctx: Any = None
        self._monitor: Optional[BatteryMonitor] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.modules.hardware.claims.register('battery', BatteryClaims(ctx))

    def ready(self) -> None:
        self._monitor = self._create_monitor(self._ctx.config.as_dict())
        self._monitor.start()

    def stop(self):
        thread = self._monitor.stop() if self._monitor is not None else None
        return [thread] if thread is not None else []

    def _reader(self, config) -> VoltageReader:
        driver = config.get('driver', 'max17048')
        bus = int(config.get('i2c_bus', 1))
        if driver == 'ina219':
            return Ina219Reader(float(config.get('shunt_ohms', 0.1)), bus)
        if driver == 'max17048':
            return Max17048Reader(bus)
        if driver == 'simulator':
            return SimulatedReader()
        raise ValueError(f"Unknown battery driver '{driver}' (known: ina219, max17048, simulator)")

    def _create_monitor(self, config) -> BatteryMonitor:
        warning = config.get('warning_action')
        warning_action = self._ctx.actions.bind(warning, 'battery.warning_action', logger) if warning else None
        return BatteryMonitor(
            self._reader(config),
            empty_mv=int(config.get('empty_voltage', 3000)), full_mv=int(config.get('full_voltage', 4200)),
            warning_mv=int(config.get('warning_voltage', 3300)), shutdown_mv=int(config.get('shutdown_voltage', 3000)),
            interval_sec=float(config.get('interval_sec', 10)),
            on_state=lambda state: self._ctx.publish(self.state, state),
            on_warning=warning_action or (lambda: None),
            on_shutdown=self._shutdown)

    def _shutdown(self) -> None:
        try:
            self._ctx.modules.hardware.shutdown()
        except Exception as error:
            logger.error(f"Could not shut down: {error}")

    @query(path='/')
    def get_battery(self) -> Optional[BatteryState]:
        """Last battery reading, or null before the first one."""
        return self._monitor.state if self._monitor is not None else None
