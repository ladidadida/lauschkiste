# lauschkiste-plugins

The general plugins of [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids. The
bundle holds, one plugin each:

- devices for an ordinary computer: `device_pc_test` (just trying it out, changes nothing outside Lauschkiste) and
  `device_pc_box` (a computer that is a box of its own: port 80, Samba, console login, kiosk screen)
- RFID reader drivers: `rfid_generic_usb`, `rfid_rc522_spi`, `rfid_mfrc522_i2c`, `rfid_pn532_i2c_py532`,
  `rfid_rdm6300_serial`, `rfid_generic_nfcpy`
- `samba`: share the library on the network
- `audiobookshelf`: audiobooks from an Audiobookshelf server
- `podcast_directories`, `radio_directories`: find podcasts and radio stations

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version; `install.sh` does). Installing does not
switch anything on: `lauschctl setup` proposes what fits the machine, and a plugin is switched on in the web app
(Settings → Plugins) or with:

```bash
lauschctl plugin enable rfid_rc522_spi
```

The libraries of a driver come with an extra, for example `lauschkiste-plugins[rc522-spi]` (the web app offers to install
them).

Documentation: [guide](https://github.com/ladidadida/lauschkiste/blob/main/documentation/en/README.md). MIT license.
