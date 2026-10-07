---
name: bug report
about: use this template to report bugs
title: "\U0001F41B | BUG SUMMARY"
labels: bug, needs triage
---

## Bug

### What I did

<!--
i.e. `I flashed Raspberry Pi OS Lite (Trixie) and ran the installer script`
-->

### What happened

<!--
i.e. `During the first run of 'apt-get install' an error was shown: 'E: Broken packages'`
-->

### I expected this to happen

<!--
i.e. `I would have expected that this command would magically fix itself when it encounters and error.`
-->

### Further information that might help

<!--
Please post here the output of 'tail -n 500 /var/log/syslog' or 'journalctl -u mopidy' ( Spotify edition only)

i.e. `find logfiles at https://paste.ubuntu.com/p/cRS7qM8ZmP/`
-->

## Software

### Base image and version

<!--
i.e. `2019-09-26-raspbian-buster-lite.img`

Otherwise the output of `cat /etc/os-release`
-->

### Branch / Release

<!--
i.e. the version shown in the web app under Settings, or `lauschctl update --check`
-->

### Installscript

<!--
i.e. `install.sh` (package) or `install.sh --source`
-->

## Hardware

### RaspberryPi version

<!--
i.e. `3 B+`

Can be obtained by executing `sudo cat /sys/firmware/devicetree/base/model` on the RaspberryPi
-->

### RFID Reader

<!--
i.e. `16c0:27db HXGCoLtd Keyboard`

Can be found in the output of `sudo lsusb -v` when it is connected via USB.
-->

### Soundcard

<!--
i.e. `0d8c:0014 C-Media Electronics, Inc. Audio Adapter (Unitek Y-247A)`

Can be found in the output of `sudo lsusb -v` when it is connected via USB.
-->

### Other notable hardware

<!--
i.e. post the relevant part of `settings/lauschkiste.yaml` (see `lauschctl home`):
-->

### Version and hardware

<!--
Lauschkiste version (Settings → Status in the web app), Raspberry Pi model, RFID reader, sound card, how it was installed.
`lauschctl setup --check` shows what is set up on the machine.
-->
