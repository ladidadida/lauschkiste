"""GPIO devices via gpiozero: buttons and rotary encoders run actions, a status LED shows the jukebox runs.

::

    gpio:
      enabled: true
      buttons:
        next: {pin: 5, action: player.next}
        play: {pin: 6, action: player.toggle, hold_action: {action: raspberry_pi.shutdown}, hold_time: 3}
      rotary_encoders:
        volume:
          pin_a: 17
          pin_b: 27
          clockwise: {action: volume.change_volume, args: {step: 2}}
          counter_clockwise: {action: volume.change_volume, args: {step: -2}}
      status_led: 25
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger('jb.raspberry_pi.gpio')

ActionRunner = Callable[[Dict[str, Any]], Optional[Callable[[], None]]]


class GpioDevices:
    def __init__(self, config: Dict[str, Any], resolve_action: ActionRunner, pin_factory=None):
        """
        :param resolve_action: turns an action entry into a callable, or None if it is invalid
        :param pin_factory: gpiozero pin factory (tests use gpiozero's MockFactory)
        """
        import gpiozero
        self._gpiozero = gpiozero
        self._resolve = resolve_action
        self._factory = pin_factory
        self._devices: List[Any] = []
        self._setup(config)

    def _kwargs(self):
        return {'pin_factory': self._factory} if self._factory is not None else {}

    def _setup(self, config: Dict[str, Any]) -> None:
        gpiozero = self._gpiozero
        for name, button in (config.get('buttons') or {}).items():
            press = self._resolve(button)
            hold = self._resolve(button['hold_action']) if button.get('hold_action') else None
            if press is None and hold is None:
                logger.error(f"GPIO button '{name}': no valid action")
                continue
            device = gpiozero.Button(button['pin'], pull_up=button.get('pull_up', True),
                                     bounce_time=button.get('bounce_time', 0.05),
                                     hold_time=button.get('hold_time', 1.0), **self._kwargs())
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
            logger.info(f"GPIO button '{name}' on pin {button['pin']}")

        for name, encoder in (config.get('rotary_encoders') or {}).items():
            clockwise = self._resolve(encoder.get('clockwise') or {})
            counter = self._resolve(encoder.get('counter_clockwise') or {})
            device = gpiozero.RotaryEncoder(encoder['pin_a'], encoder['pin_b'], **self._kwargs())
            device.when_rotated_clockwise = clockwise
            device.when_rotated_counter_clockwise = counter
            self._devices.append(device)
            logger.info(f"GPIO rotary encoder '{name}' on pins {encoder['pin_a']}/{encoder['pin_b']}")

        led_pin = config.get('status_led')
        if led_pin is not None:
            led = gpiozero.LED(led_pin, **self._kwargs())
            led.on()
            self._devices.append(led)

    def close(self) -> None:
        for device in self._devices:
            try:
                device.close()
            except Exception as error:
                logger.debug(f"Closing a GPIO device failed: {error}")
        self._devices = []
