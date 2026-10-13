# Hardware: devices, peripherals and pins

Lauschkiste runs on different machines: single-board computers, laptops, mini PCs. The **device plugin** describes the
machine (see [Device plugins](device-plugins.md)); hardware attached to it is handled by **peripheral plugins**.
Hardware support is split so that nothing except the device plugin knows which machine it runs on.

| Layer | What | Examples |
| --- | --- | --- |
| Core module `hardware` | device-neutral: registry of used resources, conflicts, the active device, shutdown/reboot | `hardware.shutdown`, `GET /api/v1/hardware` |
| Device plugins | one per kind of machine: what it provides, pin map and interfaces if it has them, how to switch them on, power, health, setup steps | `device_raspberry_pi`, `device_pc_test` |
| Peripheral plugins | devices attached to the machine, independent of which machine; they use pins or buses through the core | `gpio_controls`, `battery`, `power_button`, RFID readers |

## Resources and claims

A resource is a pin (named by the device, e.g. `GPIO17` on a Raspberry Pi) or a bus/interface
(`i2c1`, `spi0`, `i2s`). Modules that use resources register a claim provider at the extension
point `hardware.claims`; it is asked whenever the claims are needed, so changed settings show up
right away:

```python
class Claims:
    def claims(self) -> List[Claim]:  # Claim(resource='GPIO5', owner='gpio_controls', purpose='button next')
        ...
```

`GET /api/v1/hardware` lists the device's pins with their functions and who uses them; a
resource claimed twice is a conflict, unless the claim is marked `shared` (an I²C or SPI bus used by several devices). Pin fields in settings use
`json_schema_extra={'options': '/api/v1/hardware/pin-options'}`, which offers the device's GPIO pins
and names their current users.

## Capabilities

Plugins declare what they offer and need as class attributes, so this is checked before a plugin is
started:

```python
class DeviceRaspberryPi(Plugin):
    provides = ('device', 'gpio', 'i2c', 'spi', 'i2s', 'uart', 'poweroff', 'boot_config', 'system_setup', 'autologin', 'screen')

class Battery(Plugin):
    needs = ('i2c',)
```

A peripheral plugin can only be enabled while the device plugin provides what it needs, and only one
plugin may provide `device`. The web app greys out the switch and says what is missing; the API
answers 409 and `lauschctl plugin enable` refuses. If the config enables it anyway, it is skipped at
startup and listed with a problem. Whether a specific pin or bus really exists on the device model
and is free is checked through the claims at runtime.

## Devices

Exactly one device plugin registers at `hardware.devices`. It describes the machine (`describe()`:
model, pins with header position and functions, interfaces), maps a pin to a GPIO line
(`gpio_line(pin) -> (chip, line)`, used with `lgpio`/`gpiozero` on any Linux GPIO chip), accepts pins the way
users write them (`pin_id`: `17` or `GPIO17`), powers the machine off or reboots it, reports which boot settings
are pending (`boot_pending`) and claims what its own settings use (e.g. the I²S pins of a sound card).
Without a device plugin, or with one that provides no pins (`device_pc_test`), there are no pins, and shutdown/reboot are
not available.

A device plugin recognises its machine with `detect(read)` (the Raspberry Pi plugin reads
`/proc/device-tree/model`). Detection only suggests: `lauschctl setup` preselects the detected device's
plugin, and the web app offers to switch it on (Settings → Hardware, "Detected" on the plugins
page). A device plugin is never enabled silently at runtime.

Switching interfaces and overlays on needs root and a reboot: the device's settings say what is
wanted (sound card, I²C, SPI, power-off pin), `lauschctl setup` writes the boot configuration, and
the device plugin reports whether the running boot configuration matches.

## What is set up, and what to check

A device can offer `notes()`: a list of `{id, level, text, hint}` with the level `ok`, `todo` or `info`. The hardware
module returns them as `notes` in `GET /api/v1/hardware` and logs the `todo` ones when Lauschkiste starts. The web
app shows the `todo` notes as a small notice on the start page and the settings overview (the user can hide one;
the choice is kept in the browser) and all notes at the top of Settings → Hardware.

The Raspberry Pi plugin reads the HAT EEPROM (`/proc/device-tree/hat/vendor` and `product`): a known HiFiBerry board
(DAC+, DAC2 HD, ADC variants, Digi+, Amp2) that is attached but not set up gives a `todo` note
("lauschctl setup hardware"), and `lauschctl setup hardware` preselects its sound card. Boards without an EEPROM (for
example the MAX98357A or a HiFiBerry Amp+) cannot be detected and are chosen by hand. A pending boot configuration is
reported as a `todo` note as well.

## Peripherals

Peripheral plugins name what they need, not which device: a battery gauge needs an I²C bus, a power
button two GPIO pins. Through the core they get the GPIO line of a pin and register their claims.

| Plugin | Devices |
| --- | --- |
| `gpio_controls` | buttons, rotary encoders, status LED |
| `battery` | battery monitor with drivers INA219, MAX17048, simulator |
| `power_button` | button that shuts down cleanly, pin that cuts the power afterwards (OnOff SHIM preset) |
| `phat_beat` | Pimoroni pHAT BEAT: six buttons, two LED bars (volume, cards, level meter); its DAC is a sound card of the device |

A device plugin that shows the output level registers at the player's extension point
`level_meters` (`level(left, right, delay)`, RMS 0..1 per channel about ten times a second, audible
in `delay` seconds). Backends that can measure it (`local_audio`) only do so while a meter is
registered.

Sound cards are only boot configuration, so they are a setting of the device plugin.
