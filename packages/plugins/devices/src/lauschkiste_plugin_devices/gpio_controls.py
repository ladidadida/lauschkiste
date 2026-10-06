"""GPIO buttons and rotary encoders run actions, a status LED shows Lauschkiste runs.

::

    plugins:
      gpio_controls:
        buttons:
          next: {pin: GPIO5, on_press: {action: player.next}}
          play: {pin: GPIO6, on_press: {action: player.toggle}, on_hold: {action: hardware.shutdown}, hold_time: 3}
        rotary_encoders:
          volume:
            pin_a: GPIO17
            pin_b: GPIO27
            clockwise: {action: volume.change_volume, args: {step: 2}}
            counter_clockwise: {action: volume.change_volume, args: {step: -2}}
        status_led: GPIO25

Pins are named as the board does (Raspberry Pi: GPIO17, 17 or pin11).
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from lauschkiste.contract import ActionEntry, Plugin
from lauschkiste.hardware import Claim

from lauschkiste_plugin_devices.gpio import Pins, pin_field

logger = logging.getLogger('lauschkiste.gpio_controls')

ActionRunner = Callable[[Dict[str, Any]], Optional[Callable[[], None]]]


def _text(value):
    return None if value is None else str(value)


class GpioButton(BaseModel):
    pin: str = pin_field('Pin')
    on_press: Optional[ActionEntry] = Field(None, title='When pressed')
    on_hold: Optional[ActionEntry] = Field(None, title='When held')
    hold_time: float = Field(1.0, ge=0.1, le=10, title='Hold for (seconds)')
    pull_up: bool = Field(True, title='Internal pull-up', description='Off for buttons wired to 3.3 V')
    bounce_time: Optional[float] = Field(0.05, ge=0, le=1, title='Debounce (seconds)')

    @field_validator('pin', mode='before')
    @classmethod
    def _pin_text(cls, value):
        return _text(value)


class RotaryEncoder(BaseModel):
    pin_a: str = pin_field('Pin A')
    pin_b: str = pin_field('Pin B')
    clockwise: Optional[ActionEntry] = Field(None, title='Turned clockwise')
    counter_clockwise: Optional[ActionEntry] = Field(None, title='Turned counter-clockwise')

    @field_validator('pin_a', 'pin_b', mode='before')
    @classmethod
    def _pin_text(cls, value):
        return _text(value)


class GpioControlsSettings(BaseModel):
    buttons: Dict[str, GpioButton] = Field(default_factory=dict, title='Buttons')
    rotary_encoders: Dict[str, RotaryEncoder] = Field(default_factory=dict, title='Rotary encoders')
    status_led: Optional[str] = pin_field('Status LED', 'Lights up while Lauschkiste runs', default=None)

    @field_validator('status_led', mode='before')
    @classmethod
    def _pin_text(cls, value):
        return _text(value)


class GpioDevices:
    def __init__(self, config: Dict[str, Any], resolve_action: ActionRunner, pins: Pins):
        """
        :param resolve_action: turns an action entry into a callable, or None if it is invalid
        :param pins: maps the board's pin names to GPIO lines (tests use gpiozero's MockFactory)
        """
        import gpiozero
        self._gpiozero = gpiozero
        self._resolve = resolve_action
        self._pins = pins
        self._devices: List[Any] = []
        self._setup(config)

    def _setup(self, config: Dict[str, Any]) -> None:
        for name, button in (config.get('buttons') or {}).items():
            self._try(f"button '{name}'", self._button, name, button)
        for name, encoder in (config.get('rotary_encoders') or {}).items():
            self._try(f"rotary encoder '{name}'", self._encoder, name, encoder)
        if config.get('status_led') is not None:
            self._try('status LED', self._led, config['status_led'])

    def _try(self, what: str, create, *args) -> None:
        """Set one device up; a problem (e.g. a pin in use) leaves the others working."""
        try:
            create(*args)
        except Exception as error:
            logger.error(f"GPIO {what}: {error.__class__.__name__}: {error}")

    def _button(self, name: str, button: Dict[str, Any]) -> None:
        gpiozero = self._gpiozero
        press = self._resolve(button['on_press']) if button.get('on_press') else None
        hold = self._resolve(button['on_hold']) if button.get('on_hold') else None
        if press is None and hold is None:
            logger.error(f"GPIO button '{name}': no valid action")
            return
        line = self._pins.line(button['pin'])
        device = gpiozero.Button(line, pull_up=button.get('pull_up', True),
                                 bounce_time=button.get('bounce_time', 0.05),
                                 hold_time=button.get('hold_time', 1.0), **self._pins.kwargs())
        if hold is not None:
            held = {'value': False}

            def on_held(held=held, hold=hold):
                held['value'] = True
                hold()

            def on_released(held=held, press=press):
                if not held['value'] and press is not None:
                    press()
                held['value'] = False

            device.when_held = on_held
            device.when_released = on_released
        else:
            device.when_pressed = press
        self._devices.append(device)
        logger.info(f"GPIO button '{name}' on {button['pin']}")

    def _encoder(self, name: str, encoder: Dict[str, Any]) -> None:
        gpiozero = self._gpiozero
        clockwise = self._resolve(encoder.get('clockwise') or {})
        counter = self._resolve(encoder.get('counter_clockwise') or {})
        device = gpiozero.RotaryEncoder(self._pins.line(encoder['pin_a']), self._pins.line(encoder['pin_b']),
                                        **self._pins.kwargs())
        device.when_rotated_clockwise = clockwise
        device.when_rotated_counter_clockwise = counter
        self._devices.append(device)
        logger.info(f"GPIO rotary encoder '{name}' on {encoder['pin_a']}/{encoder['pin_b']}")

    def _led(self, pin: Any) -> None:
        led = self._gpiozero.LED(self._pins.line(pin), **self._pins.kwargs())
        led.on()
        self._devices.append(led)

    def close(self) -> None:
        for device in self._devices:
            try:
                device.close()
            except Exception as error:
                logger.debug(f"Closing a GPIO device failed: {error}")
        self._devices = []


class GpioClaims:
    def __init__(self, ctx):
        self._ctx = ctx

    def claims(self) -> List[Claim]:
        config = self._ctx.config.as_dict()
        result = [Claim(resource=str(b['pin']), owner='gpio_controls', purpose=f'button {name}')
                  for name, b in (config.get('buttons') or {}).items() if isinstance(b, dict) and 'pin' in b]
        for name, encoder in (config.get('rotary_encoders') or {}).items():
            for key in ('pin_a', 'pin_b'):
                if isinstance(encoder, dict) and key in encoder:
                    result.append(Claim(resource=str(encoder[key]), owner='gpio_controls', purpose=f'encoder {name}'))
        if config.get('status_led') is not None:
            result.append(Claim(resource=str(config['status_led']), owner='gpio_controls', purpose='status LED'))
        return result


class GpioControls(Plugin):
    """GPIO buttons, rotary encoders and a status LED (any board with GPIO)."""

    name = 'gpio_controls'
    interface_version = '1.0'
    needs = ('gpio',)
    requires = {'hardware': '>=1.0,<2'}
    extras = ('gpio',)
    settings = GpioControlsSettings
    pin_factory = None

    def __init__(self):
        self._ctx: Any = None
        self._devices: Optional[GpioDevices] = None

    def start(self, ctx) -> None:
        self._ctx = ctx
        ctx.modules.hardware.claims.register('gpio_controls', GpioClaims(ctx))

    def ready(self) -> None:
        config = self._ctx.config.as_dict()
        if config.get('buttons') or config.get('rotary_encoders') or config.get('status_led') is not None:
            pins = Pins(self._ctx.modules.hardware, self.pin_factory)
            self._devices = GpioDevices(config, self._bind, pins)

    def stop(self):
        if self._devices is not None:
            self._devices.close()
        return []

    def _bind(self, entry):
        return self._ctx.actions.bind(entry, 'gpio_controls', logger)
