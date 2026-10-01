"""Battery monitoring: voltage from an ADC driver, state of charge, warning and shutdown levels."""

import logging
import threading
from typing import Callable, Optional, Protocol

from pydantic import BaseModel

logger = logging.getLogger('jb.raspberry_pi.battery')


class BatteryState(BaseModel):
    voltage_mv: int
    soc: int
    warning: bool


class VoltageReader(Protocol):
    def voltage_mv(self) -> int: ...


class Ina219Reader:
    """INA219 current/voltage sensor on I2C bus 1."""

    def __init__(self, shunt_ohms: float):
        from ina219 import INA219
        self._adc = INA219(shunt_ohms, busnum=1)
        self._adc.configure(self._adc.RANGE_16V, self._adc.GAIN_AUTO, self._adc.ADC_32SAMP, self._adc.ADC_32SAMP)

    def voltage_mv(self) -> int:
        return int(self._adc.supply_voltage() * 1000)


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
        self.state = BatteryState(voltage_mv=voltage, soc=state_of_charge(voltage, self._empty, self._full),
                                  warning=voltage < self._warning_mv)
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
        self._thread = threading.Thread(target=self._run, name='raspberry_pi.battery', daemon=True)
        self._thread.start()

    def stop(self) -> Optional[threading.Thread]:
        self._stop.set()
        return self._thread
