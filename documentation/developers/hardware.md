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

## Boards

Exactly one board plugin registers at `hardware.boards`. It describes the board (`describe()`:
model, pins with header position and functions, interfaces), maps a pin to a GPIO line
(`gpio_line(pin) -> (chip, line)`, used with `lgpio`/`gpiozero` on any Linux GPIO chip), powers the
board off or reboots it, and claims what its own settings use (e.g. the I²S pins of a sound card).
Without a board plugin (e.g. on a desktop) there are no pins, and shutdown/reboot are not
available.

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
