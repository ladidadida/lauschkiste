# lauschkiste-plugin-board-raspberry-pi

Board support for the Raspberry Pi: pin map, interfaces (I²C, SPI, I²S), sound cards, boot configuration, shutdown and reboot, firmware health. A plugin for [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version), then
switch it on in the web app (Settings → Plugins) or with:

```bash
lauschctl plugin enable board_raspberry_pi
```

Documentation: [guide](https://github.com/ladidadida/lauschkiste/blob/main/documentation/en/README.md). MIT license.
