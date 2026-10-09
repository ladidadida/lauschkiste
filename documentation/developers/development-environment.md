# Development Environment

You have two development options. To interact with GPIO or other hardware, it's required to develop directly on a Raspberry Pi. For general development of Python code (Lauschkiste) or JavaScript (Web App), your own machine (Linux, Mac, Windows) is enough.

- [Development Environment](#development-environment)
  - [Develop on Raspberry Pi](#develop-on-raspberry-pi)
    - [Steps to install](#steps-to-install)
  - [Develop on local machine](#develop-on-local-machine)
    - [Using WSL](#using-wsl)

## Develop on Raspberry Pi

The full setup is running on the RPi and you access files via SSH.

### Steps to install

We recommend to use at least a Pi 3 or Pi Zero 2 for development. While this hardware won\'t be needed in production, it comes in helpful while developing.

1. Follow the [installation preperation](../builders/installation.md#1-prepare-the-raspberry-pi) steps
1. [Install](../builders/installation.md#where-lauschkiste-comes-from) your feature/fork branch of Lauschkiste (`install.sh --from source --repo <you>/lauschkiste --branch <branch>`).

## Develop on local machine

Lauschkiste also runs on any Linux machine. The Raspberry Pi specific stuff will not work of course. That is no issue depending our your development area. USB RFID Readers, however, will work. The built-in player (`local_audio`) needs no further software; the `mpd` plugin additionally needs a running
[MPD](https://www.musicpd.org/).

Install the runtime and development dependencies with [uv](https://docs.astral.sh/uv/) (project
metadata and tool config live in `pyproject.toml`):

``` bash
uv sync --group dev
```

You start the Lauschkiste core application and the Web App development server separately (see [Web App](./webapp.md)).

### Using WSL

You can also use WSL on Windows 10 or 11. This section describes how to use WSL with Visual Studio Code.

1. Install a Debian or Ubuntu image from Microsoft Store
2. Install the extension [Remote Explorer](https://marketplace.visualstudio.com/items?itemName=ms-vscode.remote-explorer) in Visual Studio Code
3. Select Remote Explorer
4. Select "WSL Targets"
5. Right-click on the previously installed WSL image and select "Connect in Current/New Window"
6. Follow the instructions from above
