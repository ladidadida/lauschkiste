# Lauschkiste documentation

Lauschkiste is an RFID audio player for kids on the Raspberry Pi. It grew out of
[Phoniebox](https://github.com/MiczFlor/RPi-Jukebox-RFID) (see [phoniebox.de](https://phoniebox.de/)).

## Quickstart

* For builders: building a Lauschkiste
  * [Installation](./builders/installation.md)
  * [Builder guides](./builders/README.md)
  * [Update](./builders/update.md)
* For developers: add features or fix bugs
  * [Developer guides](./developers/README.md)
  * [Feature status](./developers/status.md)
  * [Known issues](./developers/known-issues.md)

## How it is built

* One Python application: core modules (player, library, volume, cards, RFID, timers, ...) and
  plugins (RFID reader drivers, Raspberry Pi hardware, MPD, ...) on a common contract
  ([core and plugins](./developers/core-and-plugins.md))
* A typed REST API and a WebSocket event stream (FastAPI) for the web app; card actions and
  REST routes come from the same declarations
* Installable as a package (`install.sh`, `lauschctl setup`, `lauschctl update`) or run from a
  source checkout ([packaging and setup](./developers/packaging-and-setup.md))
* Where it is heading: [roadmap](./developers/roadmap-core-architecture.md)

## Help wanted

Some features of Phoniebox 2.x are not (yet) back. Check the [feature status](./developers/status.md)
and open an issue if yours is missing.
