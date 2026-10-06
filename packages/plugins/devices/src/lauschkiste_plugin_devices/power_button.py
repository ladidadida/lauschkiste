"""A button that shuts the box down cleanly, and a pin that cuts the power once it is down.

The power-off pin is driven by the boot configuration (``gpio-poweroff`` on a Raspberry Pi,
written by ``lauschctl setup``) after the system has halted; Lauschkiste only watches the button
and shuts down through the ``hardware`` module. Preset ``onoff_shim``: Pimoroni OnOff SHIM, button
on GPIO17, power-off on GPIO4.
"""

import logging
from typing import Any, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from lauschkiste.contract import Plugin
from lauschkiste.hardware import Claim

from lauschkiste_plugin_devices.gpio import Pins, pin_field

logger = logging.getLogger('lauschkiste.power_button')

PRESETS = {'onoff_shim': ('GPIO17', 'GPIO4')}


class PowerButtonSettings(BaseModel):
    preset: Literal['onoff_shim', 'custom'] = Field('onoff_shim', title='Hardware',
                                                    description='OnOff SHIM: button GPIO17, power-off GPIO4')
    button_pin: Optional[str] = pin_field('Button pin', 'Custom only; pressed connects it to ground', default=None)
    poweroff_pin: Optional[str] = pin_field('Power-off pin', 'Custom only; pulled low once the system has halted',
                                            default=None)
    hold_time: float = Field(0.5, ge=0, le=10, title='Press for (seconds)',
                             description='How long the button must be pressed to shut down')

    @field_validator('button_pin', 'poweroff_pin', mode='before')
    @classmethod
    def _pin_text(cls, value):
        return None if value is None else str(value)


def pins_of(config) -> Tuple[Optional[str], Optional[str]]:
    """(button pin, power-off pin) of the preset or the custom settings."""
    preset = config.get('preset', 'onoff_shim')
    if preset in PRESETS:
        return PRESETS[preset]
    return config.get('button_pin'), config.get('poweroff_pin')


class PowerButtonClaims:
    def __init__(self, ctx):
        self._ctx = ctx

    def claims(self) -> List[Claim]:
        button, poweroff = pins_of(self._ctx.config.as_dict())
        result = []
        if button:
            result.append(Claim(resource=button, owner='power_button', purpose='power button'))
        if poweroff:
            result.append(Claim(resource=poweroff, owner='power_button', purpose='power off'))
        return result


class PowerButton(Plugin):
    """Power button: shut down cleanly on a press, cut the power afterwards (e.g. Pimoroni OnOff SHIM)."""

    name = 'power_button'
    interface_version = '1.0'
    requires = {'hardware': '>=1.0,<2'}
    extras = ('gpio',)
    settings = PowerButtonSettings
    pin_factory = None

    def __init__(self):
        self._ctx: Any = None
        self._button = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.modules.hardware.claims.register('power_button', PowerButtonClaims(ctx))

    def ready(self) -> None:
        config = self._ctx.config.as_dict()
        button, _ = pins_of(config)
        if not button:
            logger.warning('No button pin configured')
            return
        import gpiozero
        pins = Pins(self._ctx.modules.hardware, self.pin_factory)
        line = pins.line(button)
        hold = float(config.get('hold_time', 0.5))
        self._button = gpiozero.Button(line, pull_up=True, hold_time=max(hold, 0.01), **pins.kwargs())
        if hold > 0:
            self._button.when_held = self._shutdown
        else:
            self._button.when_pressed = self._shutdown
        logger.info(f"Power button on {button}")

    def stop(self):
        if self._button is not None:
            self._button.close()
        return []

    def _shutdown(self) -> None:
        logger.info('Power button pressed: shutting down')
        try:
            self._ctx.modules.hardware.shutdown()
        except Exception as error:
            logger.error(f"Could not shut down: {error}")
