# Battery Monitor

The `raspberry_pi` plugin monitors a battery through an INA219 current/voltage sensor on I2C bus 1
(install the plugin's `battery-ina219` extra: `uv sync --inexact --extra battery-ina219`).

```yaml
plugins:
  raspberry_pi:
    battery:
      enabled: true
      driver: ina219            # 'simulator' for trying it out without hardware
      shunt_ohms: 0.1
      empty_voltage: 3000       # mV, 0 %
      full_voltage: 4200        # mV, 100 %
      warning_voltage: 3300     # mV, runs warning_action once
      shutdown_voltage: 3000    # mV, shuts the Pi down
      interval_sec: 10
      warning_action: {action: jingle.play, args: {sound: sounds/battery_low.wav}}
```

`sounds/battery_low.wav` is a file of your own, relative to the Lauschkiste home.

Readings are smoothed and published as `raspberry_pi.battery` (`voltage_mv`, `soc`, `warning`); the
web app shows them in the settings. The ADS1015 driver of the old battery monitor has not been
ported yet.
