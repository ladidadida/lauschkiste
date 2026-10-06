# Hardware: boards, devices and pins

Lauschkiste runs on different single-board computers. Hardware support is split so that nothing
except one plugin knows which board it runs on.

| Layer | What | Examples |
| --- | --- | --- |
| Core module `hardware` | board-neutral: registry of used resources, conflicts, the active board, shutdown/reboot | `hardware.shutdown`, `GET /api/v1/hardware` |
| Board support plugins | one per board family: pin map, interfaces, how to switch them on, power, board health | `board_raspberry_pi` |
| Device plugins | board-independent devices that use pins or buses through the core | `gpio_controls`, `battery`, `power_button`, RFID readers |

## Resources and claims

A resource is a pin (named by the board, e.g. `GPIO17` on a Raspberry Pi) or a bus/interface
(`i2c1`, `spi0`, `i2s`). Modules that use resources register a claim provider at the extension
point `hardware.claims`; it is asked whenever the claims are needed, so changed settings show up
right away:

```python
class Claims:
    def claims(self) -> List[Claim]:  # Claim(resource='GPIO5', owner='gpio_controls', purpose='button next')
        ...
```

`GET /api/v1/hardware` lists the board's pins with their functions and who uses them; a
resource claimed twice is a conflict. Pin fields in settings use
`json_schema_extra={'options': '/api/v1/hardware/pin-options'}`, which offers the board's GPIO pins
and names their current users.

## Capabilities

Plugins declare what they offer and need as class attributes, so this is checked before a plugin is
started:

```python
class BoardRaspberryPi(Plugin):
    provides = ('board', 'gpio', 'i2c', 'spi', 'i2s', 'uart', 'poweroff')

class Battery(Plugin):
    needs = ('i2c',)
```

A device plugin can only be enabled while a board plugin provides what it needs, and only one
plugin may provide `board`. The web app greys out the switch and says what is missing; the API
answers 409 and `lauschctl plugin enable` refuses. If the config enables it anyway, it is skipped at
startup and listed with a problem. Whether a specific pin or bus really exists on the board model
and is free is checked through the claims at runtime.

## Boards

Exactly one board plugin registers at `hardware.boards`. It describes the board (`describe()`:
model, pins with header position and functions, interfaces), maps a pin to a GPIO line
(`gpio_line(pin) -> (chip, line)`, used with `lgpio`/`gpiozero` on any Linux GPIO chip), powers the
board off or reboots it, and claims what its own settings use (e.g. the I²S pins of a sound card).
Without a board plugin (e.g. on a desktop) there are no pins, and shutdown/reboot are not
available.

A board plugin recognises its board with `detect(read)` (the Raspberry Pi plugin reads
`/proc/device-tree/model`). Detection only suggests: the installer enables the detected board's
plugin, and the web app offers to switch it on (Settings → Hardware, "Detected" on the plugins
page). A board plugin is never enabled silently at runtime.

Switching interfaces and overlays on needs root and a reboot: the board's settings say what is
wanted (sound card, I²C, SPI, power-off pin), `lauschctl setup` writes the boot configuration, and
the board plugin reports whether the running boot configuration matches.

## Devices

Device plugins name what they need, not which board: a battery gauge needs an I²C bus, a power
button two GPIO pins. Through the core they get the GPIO line of a pin and register their claims.

| Plugin | Devices |
| --- | --- |
| `gpio_controls` | buttons, rotary encoders, status LED |
| `battery` | battery monitor with drivers INA219, MAX17048, simulator |
| `power_button` | button that shuts down cleanly, pin that cuts the power afterwards (OnOff SHIM preset) |

Sound cards are only boot configuration, so they are a setting of the board plugin.
