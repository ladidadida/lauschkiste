# RFID Readers

* [Basics](basics.md)
  * [Reader Types](basics.md#reader-types)
  * [Reader Configuration](basics.md#reader-configuration)
* Readers
  * [Generic USB Reader](genericusb.md)
  * [RDM6300 Reader](rdm6300.md)
  * [MFRC522 SPI Reader](mfrc522_spi.md)
  * [MFRC522 I2C Reader](mfrc522_i2c.md)
  * [PN532 I2C Reader](pn532_i2c.md)
  * [Generic Readers without HID (NFCpy)](generic_nfcpy.md)

## Writing a reader driver

Readers are plugins: a driver registers at the `rfid.readers` extension point. The bundled drivers live in
`packages/plugins/rfid-readers/src/lauschkiste_plugin_rfid_readers/`; each is its own plugin (`rfid_<driver>`),
declared in that package's `pyproject.toml` and `__init__.py`. A driver in a package of its own does the same with
its own entry point.

A driver is a Python subpackage named after the reader, with the same name for its module, and three files:

```text
lauschkiste_plugin_rfid_readers/awesome_reader/
  awesome_reader.py   the reader: derives from `lauschkiste.rfid.ReaderBaseClass` (`read_card`, `cleanup`, `stop`)
  description.py      the description, without dependencies (keep the file name)
  README.md           the documentation
```

Name the subpackage `<type_of_reader>_<io_bus>_<other_specials>`, for example `generic_usb` or `pn532_i2c_py532`.
Look at an existing driver such as `generic_usb` for the details.
