# Power button and battery

> Both pages below describe hardware that is **not yet tested on real hardware** in this project.

## Power button (Pimoroni OnOff SHIM)

The OnOff SHIM switches the Pi on with a button press, shuts it down cleanly with the next press and then cuts the
power. In Lauschkiste it is the plugin *Power button* with the preset *Pimoroni OnOff SHIM* (button on GPIO17, power
off on GPIO4). No Pimoroni script is needed.

1. Answer *yes* to "Is a power button attached" in `lauschctl setup` (or switch on the plugin under Settings → Plugins
   and restart).
2. `lauschctl setup raspi`, then restart. This adds `dtoverlay=gpio-poweroff,gpiopin=4,active_low=1` to the boot
   configuration, which cuts the power once the system has halted.

A press shuts Lauschkiste down like a shutdown card: playback stops, positions are saved, the shutdown sound plays, then
the Pi halts and the SHIM switches it off. Other power buttons work the same way with the hardware *Own pins*.

### Wiring the SHIM separately

The SHIM has a 12-pin header that needs soldering. To save pins for other things you can wire it separately:

| Board pin name | Board pin | Raspberry Pi pin | Name |
| --- | --- | --- | --- |
| 3.3V | 1 | 1, 17 | 3V3 |
| 5V | 2 | 2 | 5V |
| 5V | 4 | 4 | 5V |
| GND | 6 | 6, 9, 20, 25 | ground |
| GPLCLK0 | 7 | 7 | GPIO4 |
| GPIO17 | 11 | 11 | GPIO17 |

More at [pinout.xyz](https://pinout.xyz/pinout/onoff_shim).

## Battery monitor

The plugin *Battery* reads a battery sensor on I²C, shows the charge under Settings → Status, runs an action when the
battery gets low (for example a warning sound) and shuts the box down cleanly before it is empty. Answer the question
about a battery monitor in `lauschctl setup`; the Pi board switches I²C on (`lauschctl setup raspi`, then restart).

| Driver | Sensor | Charge from |
| --- | --- | --- |
| `max17048` | MAX17048 fuel gauge (Adafruit, SparkFun LiPo boards), address 0x36 | the gauge |
| `ina219` | INA219 current and voltage sensor | the voltage (`empty_voltage` to `full_voltage`) |
| `simulator` | none, discharges slowly | the voltage |

```yaml
plugins:
  battery:
    driver: max17048
    i2c_bus: 1                 # SDA is GPIO2, SCL GPIO3
    warning_voltage: 3300      # millivolts: runs warning_action once
    shutdown_voltage: 3000     # millivolts: shuts the box down
    warning_action: {action: jingle.play, args: {sound: /path/to/low-battery.wav}}
```
