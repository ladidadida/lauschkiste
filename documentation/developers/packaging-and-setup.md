# Packaging, Installation and Setup

> Plan for the "Packaging/install overhaul" track of
> [roadmap-core-architecture.md](roadmap-core-architecture.md). Implementation status: see
> "Implementation plan" below.

## Goals

- **Installable as a package:** `pip install <wheel>` (or `uv tool install`) gives a complete jukebox:
  core, bundled plugins, web app, default settings and sounds. No git checkout needed.
- **Runnable from source, equally supported:** clone the repository, `uv sync`, `uv run jukebox run`.
  The code never assumes it runs from a checkout.
- **Setup in Python:** everything the Bash installer does today becomes idempotent
  `jukebox setup <step>` commands. An install script only bootstraps: base packages, `uv`, the
  jukebox itself (package or source), then `jukebox setup`.
- **Plugins from the CLI:** `jukebox plugin list|enable|disable|install`.
- **Distribution:** wheels attached to GitHub releases first, PyPI later (after the renaming
  question is settled).

## Where things live: `JUKEBOX_HOME`

All runtime data lives in one directory, `JUKEBOX_HOME`, with the layout `shared/` has today:

```text
$JUKEBOX_HOME/
  settings/     jukebox.yaml, logger.yaml, cards.yaml, rfid.yaml, library.sqlite, status files
  audiofolders/ the music library
  playlists/
  logs/
  cache/        cover art, ...
```

- Default: `$XDG_DATA_HOME/jukebox` (usually `~/.local/share/jukebox`); override with the
  `JUKEBOX_HOME` environment variable or `jukebox --home`.
- A source checkout's `.env` sets `JUKEBOX_HOME=shared`, so development keeps using the repository's
  `shared/` directory exactly as today. `jukebox` finds that `.env` from its own location (not the
  working directory) and resolves relative paths in it against the file's directory.
- Relative paths in the configuration are resolved against `JUKEBOX_HOME`, not against the working
  directory. Existing configurations (`shared/settings/cards.yaml` style values from a checkout
  install) keep working: a relative path starting with `shared/` is resolved against the home's
  parent.
- The configuration file is `$JUKEBOX_HOME/settings/jukebox.yaml` unless `--conf`/`JUKEBOX_CONF`
  says otherwise. Missing files are created from the packaged templates on first run (already the
  case today).

## Package data

- Default settings, sounds, the systemd unit template, mpd/autohotspot templates move from the
  top-level `resources/` into the `jukebox` package (`jukebox/resources/`), read with
  `importlib.resources`. Source and package installs use the same files.
- The web app build is included in the wheel (`jukebox/webapp/`). A source checkout serves
  `packages/webapp/build` instead; `api.webapp_dir` / `JUKEBOX_WEBAPP_DIR` override both.
- Configuration values that point at packaged files use the value `default` (e.g.
  `jingle.startup_sound: default`); any other value is a path.

## Command line

```text
jukebox run                      start the daemon (as today)
jukebox home                     print JUKEBOX_HOME and the config file in use
jukebox plugin list              installed plugins, enabled or not, and why one failed to load
jukebox plugin enable <name>     add to `plugins:`; installs the plugin package's extras if asked
jukebox plugin disable <name>
jukebox plugin install <spec>    install a plugin package (pip/uv) into the jukebox's environment
jukebox setup                    run all setup steps for this machine (interactive by default)
jukebox setup <step>             run one step: service, audio, mpd, samba, autohotspot, kiosk,
                                 rfid, boot, ...
jukebox setup --check            report which steps are applied, change nothing
jukebox update                   update the jukebox (package: newer release; source: git pull +
                                 uv sync) and apply configuration migrations
```

## Setup steps

Each step is a small Python class with `check()` (is it applied?), `apply()` and the questions it
asks. Steps are idempotent: running `jukebox setup` again repairs or updates, it doesn't duplicate.
Answers are stored in `$JUKEBOX_HOME/settings/setup.yaml` so unattended re-runs
(`jukebox setup --yes`) reuse them.

Steps port the former Bash installer routines: system packages, Raspberry Pi
settings, the systemd user service, mpd (only when the `mpd` plugin is chosen), Samba, autohotspot,
kiosk mode, RFID readers (the existing reader configuration tool), audio output, boot-time
optimisation. Steps needing root run their commands through `sudo`.

## Install script

`install.sh` (in the repository's `main` branch, run via `curl ... | bash`):

1. Checks the OS, installs base packages (`python3`, `curl`, build tools).
2. Installs `uv`.
3. Installs the jukebox, either
   - **package** (default): `uv tool install <wheel URL of the latest GitHub release>`, or
   - **source** (`--source`): `git clone`, `uv sync` in the checkout, with `.env` pointing
     `JUKEBOX_HOME` wherever the user wants it.
4. Runs `jukebox setup`.

## Implementation plan

1. **Paths** -- *done*: `JUKEBOX_HOME`, path resolution against it, resources as package data, web
   app directory configurable; `.env` for source mode.
2. **Wheels** -- *done*: `ci/build_wheels.sh` (also `bam wheels`) builds the web app, copies it into
   the `jukebox` package and builds the wheels of core, CLI and bundled plugins.
   `.github/workflows/wheels.yml` builds them on every push/PR, installs them into a fresh
   environment and starts the jukebox; a tag `v<version>` attaches them to a GitHub release.
3. **Plugin commands** -- *done*: `jukebox plugin list|enable|disable|install`
   (`packages/cli/src/lauschkiste_cli/plugin.py`). `Plugin.extras` (contract 1.1) names the extras of
   the plugin's package that `enable --with-extras` installs; installs go through `uv pip` into the
   jukebox's own environment, `pip` as fallback.
4. **Setup framework and steps** -- *done*: `packages/cli/src/lauschkiste_cli/setup/`. `System` wraps
   commands, files and machine facts (tests swap in a fake with a temporary root); steps:
   `packages`, `raspi`, `mpd`, `plugins`, `service`, `samba`, `rfid`, `kiosk`, `autohotspot`,
   `boot`, `welcome` (`jukebox setup --list`). Missing Debian packages of all chosen steps are
   installed in one `apt-get` call before the steps run. Differences to the Bash installer:
   - The service is a user unit in `~/.config/systemd/user/`, generated with the actual
     `jukebox` executable and `JUKEBOX_HOME`; `loginctl enable-linger` starts it at boot (default
     on a Pi) instead of relying on autologin. It only wants `mpd.service` if the `mpd` plugin is
     enabled.
   - Autologin is only set up for the kiosk mode, which needs it.
   - Autohotspot supports NetworkManager only (Bookworm and later); dhcpcd systems don't offer
     the step.
   - The Samba share is called `jukebox` and shares `JUKEBOX_HOME`.
   - `rfid` runs the interactive reader configuration and is skipped with `--yes`.
   - Runtime packages only: the default player needs neither ffmpeg nor mpg123; the PipeWire
     stack is installed on a Pi only (desktops bring their own sound server).
5. **Install script** -- *done*: `install.sh` (options in its header and in
   `documentation/builders/installation.md`). Package mode: `uv tool install` of the release
   wheels (or `--wheels DIR`) with the system `python3`. Source mode: clone (or reuse) a checkout,
   `uv sync --no-dev --frozen`, web app built with npm if available, else taken from the latest
   release wheel; `~/.local/bin/jukebox` links to the checkout's venv. `JUKEBOX_HOME` (Pi:
   `~/jukebox`, source: `<checkout>/shared`) and `~/.local/bin` on `PATH` go into `~/.profile` and
   `~/.bashrc`. `ci/test_install.sh` runs it in a fresh `debian:<codename>-slim` container and
   starts the jukebox; the wheels workflow does that for the wheels (trixie, bookworm) and the
   checkout (trixie). No systemd in those containers, so the `service` step is not covered there.
6. **`jukebox update`** -- *done* (`packages/cli/src/lauschkiste_cli/update.py`). Source checkout:
   `git pull --ff-only`, `uv sync --no-dev --frozen`, web app rebuilt with npm if it changed.
   Package install: newest (or `--version`) GitHub release, if newer than the installed `jukebox`;
   its wheels are installed with `uv pip` into the running environment, so other installed plugins
   stay, and the extras of enabled plugins are kept. Afterwards `jukebox setup --yes` runs in a new
   process (the updated steps) and an active service is restarted. `--check` only reports.
   Configuration migrations: none needed so far. Old relative paths (`shared/...`,
   `../../shared/...`, `../../resources/audio/...`) are handled where paths are resolved, and the
   card database converts itself on start. A versioned migration step gets added with the first
   incompatible configuration change.
7. **Remove the Bash installer** -- *done*: `migrate_to_cli/` (installer, RFID and audio tools,
   now `jukebox setup rfid` / `jukebox setup audio`; the HifiBerry script is the `sound_card`
   question of `jukebox setup raspi`), its Debian CI (`ci/ci-debian.Dockerfile`,
   `ci/installation/`, `test_docker_debian*_v3.yml`), `packages-core.txt`, the service template
   (the unit is generated) and the upstream-only `bundle_webapp_and_release_v3.yml`.

## Open points

- The `service` step is covered by unit tests only; the CI containers have no systemd.
- A first release (tag `v<version>`) is needed before `install.sh` works without `--source`/`--wheels`.
- Configurations from upstream installs (`modules:`, `gpioz:`, `host:`, ...) are not converted to
  the plugin configuration; only their paths keep working.

## Decisions

- On a Raspberry Pi the install script sets `JUKEBOX_HOME=~/jukebox` (visible, easy to reach via
  Samba); the code's default stays `$XDG_DATA_HOME/jukebox`.
- The install script lives in the repository's `main` branch.
