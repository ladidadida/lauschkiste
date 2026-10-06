# GPIO Recipes

GPIO buttons, rotary encoders and a status LED are the `gpio_controls` plugin. It works on any board
with a board support plugin (e.g. `board_raspberry_pi`) and needs the plugin's `gpio` extra; the
web app installs it from the plugins page.

Set them up in the web app (Settings → Plugins → Buttons, encoders, LED): pins are chosen from the
board's free pins, and Settings → Hardware shows which pins are used by what. In the config file
they look like this:

```yaml
plugins:
  gpio_controls:
    buttons:
      next:
        pin: GPIO5                 # as the board names it; on a Pi also 5 or pin29
        on_press: {action: player.next}
      play:
        pin: GPIO6
        on_press: {action: player.toggle}
        on_hold: {action: hardware.shutdown}
        hold_time: 3               # seconds for on_hold
        bounce_time: 0.05
        pull_up: true              # button connects the pin to GND
    rotary_encoders:
      volume:
        pin_a: GPIO17
        pin_b: GPIO27
        clockwise: {action: volume.change_volume, args: {step: 2}}
        counter_clockwise: {action: volume.change_volume, args: {step: -2}}
    status_led: GPIO25             # on while Lauschkiste runs
```

Any [action](actions.md) can be used. With `on_hold`, a short press runs `on_press` when the
button is released and a long press runs only `on_hold`. A device whose pin is already in use
is skipped (logged), the others keep working.
