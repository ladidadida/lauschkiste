# Installing Lauschkiste

## Install Raspberry Pi OS Lite

> [!IMPORTANT]
> All Raspberry Pi models are supported. For sufficient performance, **we recommend Pi 2, 3 or Zero 2** (`ARMv7` models). Because Pi 1 or Zero 1 (`ARMv6` models) have limited resources, they are slower (during installation and start up procedure) and might require a bit more work! Pi 4 and 5 are an excess ;-)

Before you can install the Lauschkiste software, you need to prepare your Raspberry Pi.

This instruction uses the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/). We recommend using the latest **Raspberry Pi OS Lite** image - Trixie.

### Raspberry Pi Imager

1. Connect a Micro SD card to your computer (preferable an SD card with high read throughput)
1. Start the Raspberry Pi Imager
1. Model: select "No filtering"
1. OS: select **Raspberry Pi OS (other)** and then **Raspberry Pi OS Lite** (64 bit, 32 bit should also work) - the version without Desktop environment
1. Storage: Select your Micro SD card (your card will be formatted)
1. Customize:
    * Hostname: choose hostname for the network (e.g. "lauschkiste")
    * Localization: choose according to your location
    * User: choose a username and a password
    * Wifi: provide your wifi settings
    * Remote: enable SSH with "Use password authentication"
1. Click `Write`
1. Confirm the next warning about erasing the SD card with `Yes`
1. Wait for the imaging process to be finished (it'll take a few minutes)
1. Plug the SD into your Pi and optionally connect keyboard, monitor and mouse.

## Install Lauschkiste software

Run the install script in your SSH terminal and follow the questions:

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
```

It installs a few base packages and [uv](https://docs.astral.sh/uv/), then Lauschkiste from the
latest release, and finally runs `lauschctl setup`, which asks what to set up on this machine
(Samba, WiFi hotspot, kiosk mode, RFID reader, boot optimisation, ...).

On a Raspberry Pi all data -- music, settings, logs -- lives in `~/lauschkiste`
(`LAUSCHKISTE_HOME`); `lauschctl home` shows where it is.

After a successful installation, [configure your Lauschkiste](configuration.md).

> [!TIP]
> Depending on your hardware, this can take a while. Don't let your computer go to sleep, and
> consider running the installation in `screen` or `tmux`, so a dropped SSH connection doesn't
> interrupt it.

Music gets onto the box through the web app, SFTP (with your Pi login) or an optional Samba
share of the library, see [Copying music](copying-music.md).

### Options

Pass options to the script with `bash -s --`, e.g.
`curl -fsSL .../install.sh | bash -s -- --source`:

| Option | Meaning |
| --- | --- |
| `--source [DIR]` | Install from a git checkout (default `~/lauschkiste`) instead of the release packages |
| `--branch NAME` | Branch for `--source` (default `main`) |
| `--version TAG` | Install a specific release instead of the latest |
| `--repo OWNER/NAME` | Install from a fork |
| `--home DIR` | Where Lauschkiste keeps its data |
| `--yes` | Don't ask; use the defaults |
| `--no-setup` | Only install; run `lauschctl setup` later |

### Changing the setup later

`lauschctl setup` can be run again at any time; every step checks first and only changes what is
missing. Your earlier answers are remembered (`settings/setup.yaml` in the Lauschkiste home).

```bash
lauschctl setup --check      # what is set up, what is missing
lauschctl setup samba        # run a single step (see: lauschctl setup --list)
lauschctl setup rfid         # configure an RFID reader
lauschctl plugin list        # installed plugins; enable/disable them
```

### Updating

```bash
lauschctl update --check     # is there a newer version?
lauschctl update             # install it, re-apply the setup, restart Lauschkiste
```

A package installation updates to the latest release (`--version vX.Y.Z` for a specific one), a
source installation pulls its branch.
