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

`raspi` sets up a sound card (e.g. HiFiBerry) and can switch the built-in headphone jack off; restart the box afterwards. `audio` chooses the outputs Lauschkiste offers.

## Update {#update}

```bash
lauschctl update
```

Fetches the newest version, installs it and restarts Lauschkiste. Settings, cards and library stay.

## Hotspot {#hotspot}

```bash
lauschctl setup autohotspot
```

Opens its own WiFi when no known one is in range, e.g. when travelling.

## More steps

| Step | For |
| --- | --- |
| `boot` | faster start (Bluetooth, IPv6, boot messages off) |
| `kiosk` | the web app on an attached screen |
| `mpd` | mpd for playback instead of the built-in player |
| `service` | Lauschkiste as a service at boot |
