# Lauschkiste

**An open-source RFID audio player for kids.** Put a card on the box and music or an audiobook
starts. Runs on a Raspberry Pi, managed from any browser.

[![Python checks and tests](https://github.com/ladidadida/lauschkiste/actions/workflows/pythonpackage_future3.yml/badge.svg?branch=main)](https://github.com/ladidadida/lauschkiste/actions/workflows/pythonpackage_future3.yml)
[![Wheels and install](https://github.com/ladidadida/lauschkiste/actions/workflows/wheels.yml/badge.svg?branch=main)](https://github.com/ladidadida/lauschkiste/actions/workflows/wheels.yml)

*Lauschkiste* is German: *lauschen* means to listen closely, *die Kiste* is the box.
Say it like "LOWSH-kiss-tuh".

## Features

- RFID/NFC cards start albums, playlists or actions (volume, timers, shutdown, ...)
- Web app for the library, cards, settings and playback
- Built-in player, no extra audio daemon needed; MPD as a plugin
- Plugins for RFID readers, Raspberry Pi hardware (buttons, encoders, LED, battery) and more
- One-line installation, setup steps you can re-run safely, updates from the command line

## Installation

On a Raspberry Pi with Raspberry Pi OS (Lite):

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
```

Then open `http://<your-pi>` (on other machines `http://<host>:5556`). Details: [Installation](documentation/builders/installation.md).

```bash
lauschctl setup --check    # what is set up on this machine
lauschctl plugin list      # installed plugins
lauschctl update           # newer version
```

## Documentation

- [For builders](documentation/builders/README.md): installation, configuration, hardware
- [For developers](documentation/developers/README.md): architecture, plugins, development setup

## Origin

Lauschkiste grew out of [Phoniebox](https://github.com/MiczFlor/RPi-Jukebox-RFID)
([phoniebox.de](https://phoniebox.de/)), the RFID jukebox started by Micz Flor, and keeps its
history. Thanks to the Phoniebox community for many years of work and ideas. Lauschkiste
reworked the core (REST API, plugin system, packaging) and goes its own way since; see
[the roadmap](documentation/developers/roadmap-core-architecture.md).

## License

MIT, see [LICENSE](LICENSE).
