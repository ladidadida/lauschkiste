# GPIO Recipes

GPIO buttons, rotary encoders and a status LED on a Raspberry Pi are part of the `raspberry_pi`
plugin (enabled by the installer). They need the plugin's `gpio` extra, which the installer
installs (`uv sync --inexact --extra gpio`). The web app edits them under Settings → Plugins →
Raspberry Pi; in the config file they look like this:

```yaml
plugins:
  raspberry_pi:
    gpio:
      enabled: true
      buttons:
        next:
          pin: 5                   # BCM numbering
          on_press: {action: player.next}
        play:
          pin: 6
          on_press: {action: player.toggle}
          on_hold: {action: raspberry_pi.shutdown}
          hold_time: 3             # seconds for on_hold
          bounce_time: 0.05
          pull_up: true            # button connects the pin to GND
      rotary_encoders:
        volume:
          pin_a: 17
          pin_b: 27
          clockwise: {action: volume.change_volume, args: {step: 2}}
          counter_clockwise: {action: volume.change_volume, args: {step: -2}}
      status_led: 25               # on while Lauschkiste runs
```

Any [action](actions.md) can be used. With `on_hold`, a short press runs `on_press` when the
button is released and a long press runs only `on_hold`.

The old `gpio.yaml` format (`gpioz`) is not read anymore.
