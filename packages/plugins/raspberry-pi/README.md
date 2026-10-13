# lauschkiste-plugins-raspberry-pi

The Raspberry Pi plugins of [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids:

- `device_raspberry_pi`: the Pi as the device: pin map, interfaces (I²C, SPI, I²S), sound cards, boot configuration,
  shutdown and reboot, firmware health, and its steps in `lauschctl setup`
- the peripherals: `gpio_controls` (buttons, rotary encoders, a status LED), `battery` (MAX17048, INA219),
  `power_button` (Pimoroni OnOff SHIM) and `phat_beat` (Pimoroni pHAT BEAT)

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version; `install.sh` does). Installing does not
switch anything on: `lauschctl setup` proposes what fits, and a plugin is switched on in the web app (Settings → Plugins)
or with:

```bash
lauschctl plugin enable gpio_controls   # or battery, power_button, phat_beat, device_raspberry_pi
```

The GPIO libraries come with the `gpio` extra: `lauschkiste-plugins-raspberry-pi[gpio]` (the web app offers to install them).

Documentation: [guide](https://github.com/ladidadida/lauschkiste/blob/main/documentation/en/README.md). MIT license.
