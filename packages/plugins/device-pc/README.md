# lauschkiste-plugin-device-pc

Device plugins for an ordinary computer (PC, laptop, mini PC) running [Lauschkiste](https://github.com/ladidadida/lauschkiste), an open-source RFID audio player for kids.

- `device_pc_test`: just trying it out. It provides nothing but "this is a device": no changes to the system, so a computer that is also used for other things is left alone.
- `device_pc_box`: a computer that is a box of its own. `lauschctl setup` may then set it up for that: port 80, Samba, console login and a kiosk screen.

Install it next to [`lauschkiste`](https://pypi.org/project/lauschkiste/) (same version). `lauschctl setup` asks which one fits (and preselects the test one on a computer that is not a Raspberry Pi); by hand:

```bash
lauschctl plugin enable device_pc_box
```

Documentation: [guide](https://github.com/ladidadida/lauschkiste/blob/main/documentation/en/get-started/other-computers.md). MIT license.
