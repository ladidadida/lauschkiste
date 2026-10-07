# lauschkiste-plugin-devices

Devices on any board with GPIO: buttons, rotary encoders, a status LED, battery monitor (MAX17048, INA219), a power button (Pimoroni OnOff SHIM) and the Pimoroni pHAT BEAT. A plugin for [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version), then
switch it on in the web app (Settings → Plugins) or with:

```bash
lauschctl plugin enable gpio_controls   # or battery, power_button, phat_beat
```

The GPIO libraries come with the `gpio` extra: `lauschkiste-plugin-devices[gpio]` (the web app offers to install them).

Documentation: [for builders](https://github.com/ladidadida/lauschkiste/blob/main/documentation/builders/README.md). MIT license.
