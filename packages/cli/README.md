# Lauschkiste

<img src="https://raw.githubusercontent.com/ladidadida/lauschkiste/main/documentation/assets/logo/white/lauschkiste-logo-text-berry-white.svg" alt="Lauschkiste" width="380">

**An open-source RFID audio player for kids.** Put a card on the box and music or an audiobook
starts. Runs on a Raspberry Pi (from the Zero up), managed from any browser. Alpha software.

*Lauschkiste* is German: *lauschen* means to listen closely, *die Kiste* is the box.

## Features

- RFID/NFC cards start albums, audiobooks, podcasts, radio stations or actions (volume, timers, shutdown, ...)
- Audiobooks also from an Audiobookshelf server (with downloads for offline use); podcast and radio search
- Quiet hours and a daily listening time
- Web app for the library, cards, settings and playback
- Built-in player, no extra audio daemon needed; MPD as a plugin
- Plugins for RFID readers, Raspberry Pi hardware (buttons, encoders, LEDs, battery) and more
- Setup steps you can re-run safely, updates from the command line

## Installation

On a Raspberry Pi with Raspberry Pi OS (Lite) or another Debian, the installer sets up everything
(system packages, the service, the Samba share and more, asking before each step):

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
```

Only the Python package (Python 3.11 or newer, Linux, PortAudio for the sound output). While there
are only pre-releases, pip needs `--pre`:

```bash
uv tool install lauschkiste                      # or: pipx install --pip-args=--pre lauschkiste
lauschkiste                                      # start the server, the web app is on http://localhost:5556
```

This package installs the server (`lauschkiste`) and the management command `lauschctl`:

```bash
lauschctl setup --check    # what is set up on this machine
lauschctl plugin list      # installed plugins
lauschctl update           # newer version
```

## Packages

| Package | Contents |
| --- | --- |
| `lauschkiste` | this package: the commands |
| `lauschkiste-core` | the player, library, cards, volume, timers, web API and web app |
| `lauschkiste-plugin-board-raspberry-pi` | Raspberry Pi board support (pins, boot configuration, power) |
| `lauschkiste-plugin-devices` | GPIO buttons, rotary encoders, LEDs, battery monitor, power button, pHAT BEAT |
| `lauschkiste-plugin-rfid-readers` | RFID reader drivers |
| `lauschkiste-plugin-mpd` | MPD as a player backend |
| `lauschkiste-plugin-samba` | share the library on the network |
| `lauschkiste-plugin-audiobookshelf` | audiobooks from an Audiobookshelf server |
| `lauschkiste-plugin-time-limits` | quiet hours and a daily listening limit |
| `lauschkiste-plugin-directories` | find podcasts and radio stations (Apple, fyyd, Podcast Index, radio-browser) |

Plugins are installed next to this package and switched on in the web app or with
`lauschctl plugin enable <name>`.

## Documentation

- [For builders](https://github.com/ladidadida/lauschkiste/blob/main/documentation/builders/README.md): installation, configuration, hardware
- [For developers](https://github.com/ladidadida/lauschkiste/blob/main/documentation/developers/README.md): architecture, plugins, development setup

## Origin and license

Lauschkiste grew out of [Phoniebox](https://github.com/MiczFlor/RPi-Jukebox-RFID), the RFID
jukebox started by Micz Flor, and keeps its history. It is not a drop-in replacement: settings and card files of
Phoniebox are not compatible. MIT license.
