# Packaging, Installation and Setup

> How Lauschkiste is packaged, installed, set up and updated.

## Goals

- **Installable as a package:** `pip install <wheel>` (or `uv tool install`) gives a complete Lauschkiste:
  core, bundled plugins, web app, default settings and sounds. No git checkout needed.
- **Runnable from source, equally supported:** clone the repository, `uv sync`, `uv run lauschkiste`.
  The code never assumes it runs from a checkout.
- **Setup in Python:** everything that configures the machine is an idempotent
  `lauschctl setup <step>` command. An install script only bootstraps: base packages, `uv`, the
  Lauschkiste itself (package or source), then `lauschctl setup`.
- **Plugins from the CLI:** `lauschctl plugin list|enable|disable|install`.
- **Distribution:** wheels attached to GitHub releases and the packages on PyPI; see
  "Packages and releases".

## Where things live: `LAUSCHKISTE_HOME`

All runtime data lives in one directory, `LAUSCHKISTE_HOME`, with this layout:

```text
$LAUSCHKISTE_HOME/
  settings/     lauschkiste.yaml, logger.yaml, cards.yaml, rfid.yaml, library.sqlite, status files
  library/      music/ and audiobooks/
  playlists/
  logs/
  cache/        cover art, ...
```

- Default: `$XDG_DATA_HOME/lauschkiste` (usually `~/.local/share/lauschkiste`); override with the
  `LAUSCHKISTE_HOME` environment variable or `lauschctl --home`.
- The home cannot be a setting (it says where the settings are), so it is the environment variable or
  `--home`. `install.sh` puts the variable into the shell profile and the systemd unit; for development in
  a checkout use `export LAUSCHKISTE_HOME=$PWD/shared`. A `.env` file is not read by Lauschkiste; the
  git-ignored `.env`/`.env.local` only hold local test credentials for scripts.
- Relative paths in the configuration are resolved against `LAUSCHKISTE_HOME`, not against the working
  directory.
- The configuration file is `$LAUSCHKISTE_HOME/settings/lauschkiste.yaml` unless `--conf`/`LAUSCHKISTE_CONF`
  says otherwise. Missing files are created from the packaged templates on first run.

## Package data

- Default settings, sounds and the mpd/autohotspot templates are part of the `lauschkiste` package
  (`lauschkiste/resources/`), read with `importlib.resources`. Source and package installs use the same files.
- The web app build is included in the wheel (`lauschkiste/webapp/`). A source checkout serves
  `packages/webapp/build` instead; `api.webapp_dir` / `LAUSCHKISTE_WEBAPP_DIR` override both.
- Configuration values that point at packaged files use the value `default` (e.g.
  `jingle.startup_sound: default`); any other value is a path.

## Command line

```text
lauschkiste                      start the daemon
lauschctl home                     print LAUSCHKISTE_HOME and the config file in use
lauschctl plugin list              installed plugins, enabled or not, and why one failed to load
lauschctl plugin enable <name>     add to `plugins:`; installs the plugin package's extras if asked
lauschctl plugin disable <name>
lauschctl plugin install <spec>    install a plugin package (pip/uv) into Lauschkiste's environment
lauschctl setup                    run all setup steps for this machine (interactive by default)
lauschctl setup <step>             run one step (`lauschctl setup --list` lists them)
lauschctl setup --check            report which steps are applied, change nothing
lauschctl update                   update Lauschkiste (package: newer release; source: git pull +
                                 uv sync) and re-apply the setup
```

## Setup steps

Each step is a small Python class with `check()` (is it applied?), `apply()` and the questions it
asks. Steps are idempotent: running `lauschctl setup` again repairs or updates, it doesn't duplicate.
Answers are stored in `$LAUSCHKISTE_HOME/settings/setup.yaml` so unattended re-runs
(`lauschctl setup --yes`) reuse them.

The steps: system packages, Raspberry Pi boot settings, the systemd user service, mpd (only when the `mpd`
plugin is chosen), plugins, Samba, port 80, autohotspot, kiosk mode, RFID readers, audio output, boot-time
optimisation and the login message. Steps needing root run their commands through `sudo`.

## Packages and releases

| Distribution | Directory | Import package | Contents |
| --- | --- | --- | --- |
| `lauschkiste` | `packages/cli` | `lauschkiste_cli` | what users install: `lauschkiste`, `lauschctl` |
| `lauschkiste-core` | `packages/lauschkiste` | `lauschkiste` | player, library, cards, API, web app |
| `lauschkiste-plugin-board-raspberry-pi`, `-devices`, `-mpd`, `-rfid-readers`, `-samba`, `-audiobookshelf`, `-directories` | `packages/plugins/*` | `lauschkiste_plugin_*` | bundled plugins |

- **One version for all.** The packages are released together and depend on each other with exact
  pins (`lauschkiste-core==0.1.0a4`), so a plugin never meets a different core. Change the version with
  `ci/set_version.py 0.1.0-alpha.4` (all `pyproject.toml` files, the pins and `version.py`);
  `test/test_packaging.py` fails when they drift apart.
- **PyPI page.** Each package has a `README.md` (shown as the project description, links absolute), a copy
  of the `LICENSE`, authors, keywords, classifiers and URLs; the test checks them too.
- **Build.** `ci/build_wheels.sh` builds the web app, then a source distribution and a wheel of every package
  (the wheel from the source distribution, which carries the web app, so what is published works). The
  GitHub release gets the wheels, PyPI the wheels and source distributions.
- **Check before publishing:** `uvx twine check dist/*`. How a release is made and the one-time PyPI setup:
  [Releasing](releasing.md).

## Install script

`install.sh` (in the repository's `main` branch, run via `curl ... | bash`):

1. Checks the OS, installs base packages (`python3`, `curl`, build tools).
2. Installs `uv`.
3. Installs Lauschkiste, either
   - **package** (default): `uv tool install <wheel URL of the latest GitHub release>`, or
   - **source** (`--source`): `git clone`, `uv sync` in the checkout, with `LAUSCHKISTE_HOME`
     (`--home`, default `<checkout>/shared`) in the shell profile and the service.
4. Runs `lauschctl setup`.

## Details

1. **Paths**: `LAUSCHKISTE_HOME`, path resolution against it, resources as package data, web
   app directory configurable.
2. **Wheels**: `ci/build_wheels.sh` (also `bam wheels`) builds the web app, copies it into
   the `lauschkiste` package and builds the wheels of core, CLI and bundled plugins.
   `.github/workflows/wheels.yml` builds them on every push/PR, installs them into a fresh
   environment and starts Lauschkiste; a tag `v<version>` attaches them to a GitHub release
   (the tag is compared after PEP 440 normalization: `v0.1.0-alpha.1` matches `0.1.0a1`; tags with a
   `-` become pre-releases). Without a stable release, `install.sh` and `lauschctl update` use the
   newest pre-release.
3. **Plugin commands**: `lauschctl plugin list|enable|disable|install`
   (`packages/cli/src/lauschkiste_cli/plugin.py`). `Plugin.extras` (contract 1.1) names the extras of
   the plugin's package that `enable --with-extras` installs; installs go through `uv pip` into the
   Lauschkiste's own environment, `pip` as fallback.
4. **Setup framework and steps**: `packages/cli/src/lauschkiste_cli/setup/`. `System` wraps
   commands, files and machine facts (tests swap in a fake with a temporary root); steps:
   `packages`, `raspi`, `mpd`, `plugins`, `service`, `samba`, `rfid`, `kiosk`, `autohotspot`,
   `boot`, `welcome` (`lauschctl setup --list`). Missing Debian packages of all chosen steps are
   installed in one `apt-get` call before the steps run. Notes:
   - The service is a user unit in `~/.config/systemd/user/`, generated with the actual
     `lauschkiste` executable and `LAUSCHKISTE_HOME`; `loginctl enable-linger` starts it at boot (default
     on a Pi) instead of relying on autologin. It only wants `mpd.service` if the `mpd` plugin is
     enabled.
   - Autologin is only set up for the kiosk mode, which needs it.
   - Autohotspot supports NetworkManager only (Bookworm and later); dhcpcd systems don't offer
     the step.
   - The Samba share is called `lauschkiste` and shares only the library; the password is
     asked for (no default), files keep normal permissions.
   - `rfid` runs the interactive reader configuration and is skipped with `--yes`.
   - Runtime packages only: the default player needs neither ffmpeg nor mpg123; the PipeWire
     stack is installed on a Pi only (desktops bring their own sound server).
5. **Install script**: `install.sh` (options in its header and in
   `documentation/builders/installation.md`). Package mode: `uv tool install` of the release
   wheels (or `--wheels DIR`) with the system `python3`. Source mode: clone (or reuse) a checkout,
   `uv sync --no-dev --frozen`, web app built with npm if available, else taken from the latest
   release wheel; `~/.local/bin/lauschctl` links to the checkout's venv. `LAUSCHKISTE_HOME` (Pi:
   `~/lauschkiste`, source: `<checkout>/shared`) and `~/.local/bin` on `PATH` go into `~/.profile` and
   `~/.bashrc`. `ci/test_install.sh` runs it in a fresh `debian:<codename>-slim` container and
   starts Lauschkiste; the wheels workflow does that for the wheels (trixie, bookworm) and the
   checkout (trixie). No systemd in those containers, so the `service` step is not covered there.
6. **`lauschctl update`** -- *done* (`packages/cli/src/lauschkiste_cli/update.py`). Source checkout:
   `git pull --ff-only`, `uv sync --no-dev --frozen`, web app rebuilt with npm if it changed.
   Package install: newest (or `--version`) GitHub release, if newer than the installed `lauschkiste`;
   its wheels are installed with `uv pip` into the running environment, so other installed plugins
   stay, and the extras of enabled plugins are kept. Afterwards `lauschctl setup --yes` runs in a new
   process (the updated steps) and an active service is restarted. `--check` only reports.

## Open points

- The `service` step is covered by unit tests only; the CI containers have no systemd.

## Decisions

- On a Raspberry Pi the install script sets `LAUSCHKISTE_HOME=~/lauschkiste` (visible, easy to reach via
  Samba); the code's default stays `$XDG_DATA_HOME/lauschkiste`.
- The install script lives in the repository's `main` branch.
