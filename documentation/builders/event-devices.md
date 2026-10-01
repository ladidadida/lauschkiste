# Event devices (USB and other buttons)

USB buttons, joysticks, keyboards and similar input devices trigger [actions](actions.md) through
the core `input` module. Devices are found by name and re-attached when they are plugged in again.

```yaml
input:
  devices:
    joystick:
      device_name: DragonRise Inc.   Generic   USB
      exact: false          # true: the name must match exactly, false: contained in the name
      keys:
        BTN_TRIGGER: {action: player.toggle}
        BTN_THUMB: {action: player.next}
        297: {action: player.prev}           # numeric key codes work too
        BTN_TOP: {action: volume.change_volume, args: {step: 5}}
```

Key names are evdev names (`KEY_*`, `BTN_*`). To find a device's name and its key codes, run
`python -m evdev.evtest` and press the buttons.

The connected devices are listed at `GET /api/v1/input/devices`; every press of a mapped key is
published as `input.key_pressed`.

The user running Lauschkiste needs read access to `/dev/input/event*` (usually membership in the
`input` group).
