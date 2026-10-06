# Battery Monitor

The `battery` plugin reads a battery sensor on I²C, publishes the state of charge (shown under
Settings → Status), runs an action when the battery gets low and shuts the box down cleanly before
it is empty. It needs the plugin's `battery` extra (installed from the plugins page) and I²C,
which the Raspberry Pi board switches on automatically (`lauschctl setup raspi`, then reboot).

| Driver | Sensor | State of charge |
| --- | --- | --- |
| `max17048` | MAX17048 fuel gauge (e.g. Adafruit, SparkFun LiPo boards), address 0x36 | from the gauge |
| `ina219` | INA219 current/voltage sensor | from the voltage (`empty_voltage`..`full_voltage`) |
| `simulator` | none, discharges slowly | from the voltage |

```yaml
plugins:
  battery:
    driver: max17048
    i2c_bus: 1                # /dev/i2c-1 (SDA GPIO2, SCL GPIO3 on a Pi)
    warning_voltage: 3300     # mV, runs warning_action once
    shutdown_voltage: 3000    # mV, shuts the box down
    interval_sec: 10
    warning_action: {action: jingle.play, args: {sound: sounds/battery_low.wav}}
```
