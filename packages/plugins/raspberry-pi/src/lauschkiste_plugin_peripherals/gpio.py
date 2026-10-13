"""GPIO access for device plugins: pins named by the board, opened through gpiozero on the board's GPIO chip."""

from typing import Any, Dict, Optional, Tuple

from pydantic import Field

#: Pin fields in settings offer the board's GPIO pins and name their current users
PIN_OPTIONS = {'options': '/api/v1/hardware/pin-options'}


def pin_field(title: str, description: Optional[str] = None, default: Any = ...):
    return Field(default, title=title, description=description, json_schema_extra=PIN_OPTIONS)


class Pins:
    """Turns board pin names into GPIO lines of one chip and creates gpiozero devices on it."""

    def __init__(self, hardware, pin_factory=None):
        self._hardware = hardware
        self._factory = pin_factory
        self._chip: Optional[int] = None

    def line(self, pin: Any) -> int:
        result = self._hardware.gpio_line(str(pin))
        chip, line = (result.chip, result.line) if hasattr(result, 'chip') else result
        if self._chip is None:
            self._chip = chip
        return line

    @property
    def chip(self) -> int:
        return self._chip or 0

    def factory(self):
        if self._factory is None:
            from gpiozero.pins.lgpio import LGPIOFactory
            self._factory = LGPIOFactory(chip=self._chip or 0)
        return self._factory

    def kwargs(self) -> Dict[str, Any]:
        return {'pin_factory': self.factory()}


def lines(pins: Pins, *values: Any) -> Tuple[int, ...]:
    return tuple(pins.line(value) for value in values)
