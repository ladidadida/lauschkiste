# The commands

Two commands do everything on the box. Log in with SSH and type them in a terminal; each one explains itself with
`--help`.

## `lauschctl`: set up and manage the box

| Command | What it does |
| --- | --- |
| `lauschctl setup` | sets up the box step by step and asks questions; `--yes` accepts earlier answers |
| `lauschctl setup <step>` | runs one step; `--list` lists the steps, `--check` only reports what is missing |
| `lauschctl update` | installs a newer version |
| `lauschctl uninstall` | removes what Lauschkiste created, and itself last |
| `lauschctl config get\|set <key> [value]` | reads and changes a single setting |
| `lauschctl plugin list\|enable\|disable\|install` | manages plugins |
| `lauschctl home` | prints the folder with the data and the settings file in use |

### The setup steps

`lauschctl setup` goes in two parts: first the device (what kind of machine this is) and its options, then what is
attached to it (the peripherals) and their options. Each step looks first and only changes what is missing, so running one again is safe.

| Step | For |
| --- | --- |
| `device` | which kind of machine this is; decides what the other steps offer |
| `packages` | the system packages Lauschkiste needs (and, if you want, an upgrade of the system) |
| `hardware` | the sound card on the header (Raspberry Pi) |
| `plugins` | enables the plugins the answers call for |
| `service` | Lauschkiste as a service that starts with the box |
| `port` | the web page on port 80, so the address needs no `:5556` |
| `audio` | chooses the audio outputs ([Sound](../using/sound.md)) |
| `samba` | the library as a network folder ([Music](../using/music.md)) |
| `rfid` | the RFID reader ([RFID readers](../hardware/readers.md)) |
| `kiosk` | the web page on an attached screen ([A screen](../hardware/screen.md)) |
| `autohotspot` | the box's own WiFi ([Away from home](../using/wifi-hotspot.md)) |
| `boot` | quiet boot, Bluetooth optionally off |
| `welcome` | the message when you log in |
| `extra_plugins` | installs plugins from PyPI, GitHub (`github:owner/repo@tag`) or a URL, also for hardware of your own |
| `peripherals` | what is attached: pHAT BEAT, power button, battery monitor, buttons and knobs, and your own |
| `peripheral_options` | the options of what is attached (e.g. the battery sensor) |
| `raspi` | writes the sound card and the pins to the boot configuration (restart afterwards) |

## `lauschkiste`: the server

`lauschkiste` is the program that plays. On a box it runs as a service that starts with the box; you rarely call it
yourself. To see what it does, stop the service and start it in the console:

```bash
systemctl --user stop lauschkiste
lauschkiste -vv           # more messages; Ctrl-C stops it
systemctl --user start lauschkiste
```

Control the service with `systemctl --user start|stop|restart|status lauschkiste`.
