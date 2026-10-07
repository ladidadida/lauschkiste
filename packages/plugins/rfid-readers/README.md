# lauschkiste-plugin-rfid-readers

RFID reader drivers, one plugin per driver (RC522 on SPI, MFRC522 and PN532 on I²C, USB readers, RDM6300, NFC). A plugin for [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version), then
switch it on in the web app (Settings → Plugins) or with:

```bash
lauschctl plugin enable rfid_rc522_spi   # one per driver
```

Documentation: [for builders](https://github.com/ladidadida/lauschkiste/blob/main/documentation/builders/README.md). MIT license.
