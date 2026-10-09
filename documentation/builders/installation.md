# Installing Lauschkiste

## 1. Prepare the Raspberry Pi

All Raspberry Pi models work. A Pi 3 or Zero 2 is comfortable; a Pi Zero W runs Lauschkiste well too, but the
installation takes longer (about ten minutes). Use **Raspberry Pi OS Lite** (Trixie, 64 or 32 bit).

With the [Raspberry Pi Imager](https://www.raspberrypi.com/software/): choose the OS (Raspberry Pi OS Lite) and the
SD card, and in the customisation set a hostname (e.g. `lauschkiste`), a user and password, your WiFi, and enable
SSH. Write the card, put it into the Pi and connect with `ssh <user>@<hostname>`.

## 2. Install

Run the install script and follow the questions:

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
```

It installs a few base packages and [uv](https://docs.astral.sh/uv/), then Lauschkiste, and runs
`lauschctl setup`, which asks what to set up on this machine (RFID reader, Samba share, WiFi hotspot, kiosk mode,
boot optimisation, ...). Run it in `screen` or `tmux` if your SSH connection is unreliable.

### Where Lauschkiste comes from

Choose with `--from` (pass options with `bash -s --`, e.g. `curl ... | bash -s -- --from source`):

| `--from` | What you get | Use it for |
| --- | --- | --- |
| `pypi` (default) | the packages on PyPI; `--version 0.1.0a4` for a specific one | released versions |
| `github` | the wheels attached to a GitHub release; `--version TAG` for a specific one | the same release without PyPI |
| `source` | a git checkout in `~/lauschkiste` (`--source DIR`, `--branch NAME`) that runs from its folder | development and trying branches; builds the web app with npm if installed, else takes it from the latest release |

> [!NOTE]
> `--from testpypi` installs test uploads.

### More options

| Option | Meaning |
| --- | --- |
| `--home DIR` | where Lauschkiste keeps its data (default `~/lauschkiste` on a Raspberry Pi) |
| `--library DIR` | where music and audiobooks live (default `<home>/library`); can be changed later with `lauschctl config set library.path DIR` |
| `--repo OWNER/NAME` | install from a fork |
| `--wheels DIR` | install the wheel files in `DIR` instead of downloading a release |
| `--yes` | don't ask, use the defaults |
| `--no-setup` | only install; run `lauschctl setup` later |

## 3. After the installation

Open `http://<hostname>` in a browser (`http://<hostname>:5556` if you did not choose port 80 in the setup).
Put music on the box through the web app or an optional Samba share ([Copying music](copying-music.md)) and
[configure Lauschkiste](configuration.md). All data (music, settings, logs) lives in the home directory;
`lauschctl home` shows where it is.

## Changing the setup and updating

```bash
lauschctl setup --check      # what is set up, what is missing
lauschctl setup rfid         # run a single step (lauschctl setup --list shows them)
lauschctl config get library.path   # read and change single settings (`config set KEY VALUE`)
lauschctl plugin list        # installed plugins; enable and disable them
lauschctl update --check     # is there a newer version?
lauschctl update             # install it, re-apply the setup, restart Lauschkiste
```

`lauschctl update` follows the way Lauschkiste was installed: from PyPI it upgrades from PyPI, from release
wheels it takes the newest release, a git checkout pulls its branch (`--version` picks a specific version).

## Other Linux computers

Lauschkiste is not tied to the Raspberry Pi. On a Debian-based computer (Debian, Ubuntu, ...) the install script works
the same and skips the Raspberry Pi steps; it is tested in Debian 12 and 13 containers. The built-in player plays
through the normal sound output, USB RFID readers work, and the web app and all content features (library,
audiobooks, podcasts, radio, time limits) are the same. What needs a board (GPIO buttons, LEDs, sound cards on the
header, battery, shutdown by a power button) is only available with a board support plugin; shutdown and reboot are
then not offered. On other distributions, install with `--from source` and set up the system packages yourself. Windows and macOS are not supported.
