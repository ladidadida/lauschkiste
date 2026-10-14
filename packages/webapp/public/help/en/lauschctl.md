# Commands on the box

Some settings change the operating system and need administrator rights. `lauschctl` does them right on the box. Log in with SSH, e.g. in a terminal on your computer:

```bash
ssh <user>@<name-or-ip-of-the-box>
```

Every setup step checks first and only changes what is missing; running it again does no harm. `lauschctl setup --list` lists all steps, `lauschctl setup --check` only reports what is missing.

## Overview

| Command | For |
| --- | --- |
| `lauschctl setup` | set up everything (asks questions) |
| `lauschctl setup <step>` | one step, e.g. `samba` |
| `lauschctl update` | update to the newest version |
| `lauschctl plugin list` | installed plugins |
| `lauschctl home` | where settings and library are |
| `lauschctl uninstall` | remove Lauschkiste from the box (`--check` shows what it would do) |

## Samba {#samba}

```bash
lauschctl setup samba
```

Installs Samba, shares the library as `lauschkiste` and asks for a Samba password. Afterwards share and password can be changed in the web app (Settings → Library).

## Reader {#reader}

```bash
lauschctl setup rfid
```

Asks which reader is connected (e.g. RC522, USB reader) and how it is wired, enables the matching plugin and installs what it needs. Restart Lauschkiste afterwards.

## Audio {#audio}

```bash
lauschctl setup raspi
lauschctl setup audio
```

`raspi` writes what the settings of the Raspberry Pi device plugin and the peripherals ask for to the boot configuration (`config.txt`): sound card (e.g. MAX98357A, HiFiBerry), built-in headphone jack, I²C, SPI and the power-off pin of a power button. Restart the box afterwards. Settings → Hardware shows what is still missing. `audio` chooses the outputs Lauschkiste offers.

## Update {#update}

```bash
lauschctl update
```

Fetches the newest version, installs it and restarts Lauschkiste. Settings, cards and library stay.

## Kiosk {#kiosk}

```bash
lauschctl setup kiosk
```

Installs a minimal graphics system and the Chromium browser, logs in by itself and shows the web app full screen on the attached display after the start. Restart the box afterwards. What the screen shows and the on-screen keyboard are set in Settings → Screen.

## Hotspot {#hotspot}

```bash
lauschctl setup autohotspot
```

Opens its own WiFi when no known one is in range, e.g. when travelling.

## More steps

| Step | For |
| --- | --- |
| `extra_plugins` | install plugins from PyPI, GitHub (`github:owner/repo@tag`) or a URL and enable them |
| `device` | which kind of machine this is (decides what the other steps offer) |
| `hardware` | the sound card on the header (Raspberry Pi) |
| `peripherals` | what is attached: pHAT BEAT, power button, battery monitor, buttons and knobs, plugins of your own |
| `boot` | quiet boot (no boot messages or logo, a few first-boot services off; Bluetooth optionally) |
| `kiosk` | the web app on an attached screen |
| `port` | the web app on port 80, so its address needs no `:5556` (a systemd socket forwards it) |
| `service` | Lauschkiste as a service at boot |
