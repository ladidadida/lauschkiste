# The installer

`install.sh` installs Lauschkiste and nothing else; `lauschctl setup` then sets up the machine. For the user's view
see the [guide](../en/get-started/install.md). This page lists the options of the script. Pass options with
`bash -s --`, for example `curl ... | bash -s -- --from source`.

## Where Lauschkiste comes from

Choose with `--from` (pass options with `bash -s --`, e.g. `curl ... | bash -s -- --from source`):

| `--from` | What you get | Use it for |
| --- | --- | --- |
| `pypi` (default) | the packages on PyPI; `--version 0.1.0a4` for a specific one | released versions |
| `github` | the wheels attached to a GitHub release; `--version TAG` for a specific one | the same release without PyPI |
| `source` | a git checkout in `~/lauschkiste` (`--source DIR`, `--branch NAME`) that runs from its folder | development and trying branches; builds the web app with npm if installed, else takes it from the latest release |

> [!NOTE]
> `--from testpypi` installs test uploads.

## uv or pip

[uv](https://docs.astral.sh/uv/) is the preferred installer, but nothing forces it on you: if `uv` is not on the
machine, the packages (`pypi`, `github`) are installed with `pip` into their own virtual environment
(`~/.local/share/lauschkiste-venv`), which needs less space and nothing else. `uv` is installed only for
`--from source`, test indexes, or when it is already there. An existing installation always stays the way it was
installed; the script never switches it. Whichever way: if an installation fails, the previous one is put back.

## More options

| Option | Meaning |
| --- | --- |
| `--home DIR` | where Lauschkiste keeps its data (default `~/lauschkiste` on a Raspberry Pi) |
| `--repo OWNER/NAME` | install from a fork |
| `--wheels DIR` | install the wheel files in `DIR` instead of downloading a release |
| `--no-dev` | with `--from source`: leave out the development tools (pytest, ruff, `bam`, ...), which are installed by default |

## Other Linux computers

Lauschkiste is not tied to the Raspberry Pi. On a Debian-based computer (Debian, Ubuntu, ...) the install script works
the same and skips the Raspberry Pi steps; it is tested in Debian 12 and 13 containers. The built-in player plays
through the normal sound output, USB RFID readers work, and the web app and all content features (library,
audiobooks, podcasts, radio, time limits) are the same. What needs a Raspberry Pi (GPIO buttons, LEDs, sound cards on the
header, battery, shutdown by a power button) is only available with a device plugin that offers it; shutdown and reboot are
then not offered. On other distributions, install with `--from source` and set up the system packages yourself. Windows and macOS are not supported.
