# Buttons and knobs

Buttons, knobs and an LED make the box work without the web page: volume, next, pause. Everything a button does is an
*action*, the same actions that cards use ([Cards](../using/cards.md)).

## Buttons on the pins (GPIO)

Buttons, rotary encoders (knobs) and a status LED on the pins of the Pi are the plugin *Buttons, encoders, LED*
(`gpio_controls`). Switch it on under Settings → Plugins; the web page installs what it needs. Then set up the buttons
there. You choose pins from the list of free pins, and Settings → Hardware shows which pin is used by what.

In the settings file it looks like this:

```yaml
plugins:
  gpio_controls:
    buttons:
      next:
        pin: GPIO5                  # as the board names it; on a Pi also 5 or pin29
        on_press: {action: player.next}
      play:
        pin: GPIO6
        on_press: {action: player.toggle}
        on_hold: {action: hardware.shutdown}
        hold_time: 3                # seconds for on_hold
        pull_up: true               # the button connects the pin to ground
    rotary_encoders:
      volume:
        pin_a: GPIO17
        pin_b: GPIO27
        clockwise: {action: volume.change_volume, args: {step: 2}}
        counter_clockwise: {action: volume.change_volume, args: {step: -2}}
    status_led: GPIO25              # on while Lauschkiste runs
```

With `on_hold`, a short press runs `on_press` when the button is released and a long press runs only `on_hold`. A button
whose pin is already used by something else is skipped (the log says so), the others keep working.

## USB buttons, joysticks and keyboards

Any device that Linux sees as an input device can trigger actions: USB buttons, a joystick, a keyboard, even a game
controller. Map the keys in the settings:

```yaml
input:
  devices:
    joystick:
      device_name: DragonRise Inc.   Generic   USB
      exact: false                 # false: the name only has to be contained
      keys:
        BTN_TRIGGER: {action: player.toggle}
        BTN_THUMB: {action: player.next}
        BTN_TOP: {action: volume.change_volume, args: {step: 5}}
```

To find the name of the device and its keys, run `python -m evdev.evtest` on the box and press the buttons. Names are
`KEY_*` or `BTN_*`; numbers work too. The user running Lauschkiste needs to be in the group `input`. A device that is
plugged in later is found by itself.

The buttons of Bluetooth headphones work through `input.media_keys: true`, see [Sound and Bluetooth](../using/sound.md).
