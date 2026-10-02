# AGENTS.md

Guidance for AI coding agents (Claude, Codex, Copilot, etc.) working in this repository.

## What this project is

**Lauschkiste**: an RFID-controlled audio player for kids on the Raspberry Pi, grown out of
Phoniebox (RPi-Jukebox-RFID "future3") and largely rewritten since. Kids (and others) tap an RFID card on a reader and the box
plays a specific playlist/album — no screen required. This branch (`future3/develop`) is a
from-scratch rewrite of the legacy (v2, shell-script based) project; do not assume v2 conventions
apply.

## Repository layout

```text
pyproject.toml     uv workspace root (virtual: no [project] table); shared dev-tool config
                   (ruff/pyright/pytest/coverage/pydoc-markdown) lives here
packages/          uv workspace members
  lauschkiste/     Python core application ("Lauschkiste core") — the daemon that runs on the Pi
    pyproject.toml Real [project] table (package=true), runtime dependencies, hatchling backend
    src/lauschkiste/   The installable package: the core/plugin contract (contract/), the core
                   modules (core_modules.py: system, library, player, volume, timers, jingle,
                   input, cards, rfid), FastAPI API bridge
                   (api/), in-process event bus (publishing/), config handling. Removed former
                   components come back as core modules (volume, timers, jingle, system info,
                   input devices) or plugins (raspberry-pi, mqtt, card sync) -- see
                   documentation/developers/core-and-plugins.md.
    interfaces/    Interface snapshots of the framework contract and every core module, checked
                   by test/contract/test_snapshots.py (see "Core and plugins" below)
  cli/             Lauschkiste CLI (lauschkiste-cli): `lauschkiste` (start the daemon), `home`,
                   `plugin list|enable|disable|install`, `update`, `setup` (machine setup steps in
                   lauschkiste_cli/setup/, see documentation/developers/packaging-and-setup.md),
                   `debug sniff` (publishing-bus WebSocket sniffer).
  webapp/          React front-end (the touch/web UI), talks to the core via HTTP/WebSocket
                   (FastAPI, `/api/v1/*`). Not a uv workspace member (npm/Vite project), but lives
                   alongside the Python packages structurally.
docker/            Dockerfiles + compose files for a non-Pi development environment
install.sh         Installer (curl | bash): base packages, uv, Lauschkiste (release wheels or --source),
                   then `lauschctl setup`
shared/            LAUSCHKISTE_HOME when running from this checkout (see .env): settings, library,
                   playlists, logs, cache
documentation/     Project docs: builders/ (end users/installers) and developers/ (contributors)
test/              Python unit tests (pytest)
ci/                CI helper scripts: build_wheels.sh, test_install.sh (install.sh in a Debian
                   container)
```

## Architecture essentials

- **Core and plugins** (`lauschkiste.contract`, design in `documentation/developers/core-and-plugins.md`):
  every piece of functionality is a *module*: a `CoreModule` (always shipped, always running,
  listed in `lauschkiste/core_modules.py`) or a `Plugin` (separate package, found via the
  `lauschkiste.plugins` entry-point group, loaded only when listed under `plugins:` in lauschkiste.yaml).
  Start order comes from `requires`. Modules declare operations with `@action` (state-changing:
  REST route + card action `<module>.<action>` + in-process call) and `@query` (read-only GET),
  typed events with `event(name, Model)` (topic `<module>.<name>`), and extension points
  (`player.backends`, `rfid.readers`). Everything must be type-annotated; argument models are
  built from the signature. Don't hand-write REST routes or card aliases for new functionality --
  declare them on a module. Per-module lock by default (`concurrency = 'threadsafe'` opts out).
- **Interface versioning**: each module has an `interface_version`, the framework a
  `CONTRACT_VERSION`. Snapshots in `packages/lauschkiste/interfaces/` (and `interfaces/<plugin>.json` in bundled
  plugin packages) are compared in CI: a breaking change (removed/renamed operation or field,
  type change, protocol change) needs a major bump, an addition a minor bump. After bumping, run
  `uv run python -m lauschkiste.contract.snapshots --update` and commit the snapshot.
- **API**: the webapp talks to routes generated from the modules' operations (`/api/v1/player/*`,
  `/api/v1/settings`, `/api/v1/cards`, ... -- see `/docs` on the running daemon), plus
  `GET /api/v1/modules` (active modules, their operations/events, skipped plugins) and
  `GET /api/v1/actions` (card actions with argument schemas). Card entries, card removal actions
  and the second-swipe action are stored as `action: <module>.<action>` plus named `args`
  (`documentation/builders/actions.md`). ZeroMQ, the
  generic HTTP RPC endpoint and the old call registry are gone. A first CLI slice exists
  (`packages/cli`, `lauschkiste`/`lauschctl debug sniff`), but a dedicated CLI for the API is not
  designed yet.
- **Event bus** (`lauschkiste.publishing.get_bus()`, a `lauschkiste.publishing.bus.EventBus`): thread-safe,
  in-process, last-value cached. Modules publish typed events through `ctx.publish(event,
  payload)` (validated against the event's model; raises with `LAUSCHKISTE_STRICT=1`, logs and drops
  otherwise), never untyped dicts. The
  webapp subscribes via the FastAPI WebSocket bridge (`/api/v1/events`); `lauschctl debug sniff`
  connects there too as a plain WebSocket client.
- **Player backend**: registered at the `player.backends` extension point, selected via
  `player.backend` config. Default is `local_audio` (decodes via PyAV, outputs via sounddevice/
  PortAudio, no external process); `mpd` (an external mpd server, via `python-mpd2`) is an opt-in
  alternative. Backends implement `lauschkiste.player.backend.PlayerBackend`; the player module turns
  their raw status into the typed `player.status` event (`lauschkiste.player.status.PlayerStatus`).
- **Library** (`lauschkiste.library`): owns the music library -- file management, a SQLite index of
  tags/durations (`$LAUSCHKISTE_HOME/settings/library.sqlite`), cover art (`$LAUSCHKISTE_HOME/cache/covers`), and the
  `library.sources` extension point for further catalogs (mpd, streaming). Browsing routes are
  `/api/v1/library/*`; the local source id is `local`.
- **Paths** (`lauschkiste.paths`): all runtime data lives in `LAUSCHKISTE_HOME` (`--home`, `$LAUSCHKISTE_HOME`,
  default `$XDG_DATA_HOME/lauschkiste`; this checkout's `.env` sets it to `shared/`). Relative paths in
  the configuration resolve against it; never resolve paths
  against the working directory or the checkout. Packaged files (default settings, sounds, service
  templates) live in `lauschkiste/resources/`, read via `lauschkiste.paths.resource()`. The web app is
  served from `api.webapp_dir` / `$LAUSCHKISTE_WEBAPP_DIR`, else from the package, else (source checkout) from
  `packages/webapp/build`.
  See `documentation/developers/packaging-and-setup.md`.
- **Bundled plugins** live in `packages/plugins/*` (uv workspace members, installed by `uv sync`
  but only loaded when enabled under `plugins:`): `raspberry-pi` (shutdown/reboot, GPIO, battery,
  firmware health; the installer enables it), `mpd` (player backend) and `rfid-readers`
  (one plugin per reader driver, `rfid_<driver>`; each driver's dependencies are an extra of that
  package -- `uv sync --inexact --extra <driver-extra>`, e.g. `rc522-spi`).

## Languages, tools, conventions

- **Python** (core, min version 3.11): PEP 8 style, enforced by **ruff** (`[tool.ruff]` in
  `pyproject.toml`, max line 127, max-complexity 12 — mirrors the old flake8 config, not yet
  running ruff's isort/pyupgrade rules or `ruff format` on the existing tree, see
  `documentation/developers/roadmap-core-architecture.md`). All Python plugin/config folder & file
  names are `snake_case`, descriptive, general→specific (see `CONTRIBUTING.md` "Naming
  conventions" section) — this is a deliberate v2→v3 break, follow it strictly.
- **JavaScript/React** (`packages/webapp`): Create React App (`react-scripts`), MUI v5, i18next for
  translations (`de`/`en` under `packages/webapp/public/locales`), Ramda, react-router-dom.
- **Config format**: YAML (`ruamel.yaml`), defaults in `packages/lauschkiste/src/lauschkiste/resources/default-settings/`.
- Everything under any `scratch*`-named folder is git- and ruff-ignored — safe scratch space,
  never a place for real code.

## Common commands (run from repo root)

Package manager is **uv**; the dev/CI workflow is driven by **[bam](https://gitlab.com/cascascade/bam)**
(`bam.yaml`), a content-addressed task runner — cached, so re-running an unchanged task is instant.
The old `run_*.sh` wrapper scripts are gone.

```bash
uv sync --group dev             # install/update the .venv (runtime + dev dependencies, core and
                                 # bundled plugins); reader drivers with extra dependencies need
                                 # --extra <driver-extra> (see "Bundled plugins" above)
uv run lauschkiste              # start the Lauschkiste core -- creates $LAUSCHKISTE_HOME/settings/
                                 # lauschkiste.yaml and logger.yaml from the packaged templates on
                                 # first run if missing (here: shared/settings/, via .env).
uv run lauschctl home             # show LAUSCHKISTE_HOME and the config file in use
uv run lauschctl plugin list      # installed plugins, enabled or not; also enable/disable <name>
                                 # [--with-extras], install <spec> [--enable]
uv run lauschctl setup --check    # what `lauschctl setup [<step>...]` would change on this machine
                                 # (steps: `lauschctl setup --list`; answers in settings/setup.yaml)
uv run lauschctl update --check   # newer release / upstream commits? (`lauschctl update` applies it)
bam lint                        # ruff check (cached)
bam format                      # ruff format (auto-fix)
bam format-check                # ruff format --check (informational only for now, see roadmap)
bam typecheck                   # pyright (informational only for now, see roadmap)
bam test                        # pytest, writes .reports/junit.xml
bam docs                        # regenerate API docs (pydoc-markdown)
bam markdownlint                # lint markdown docs (needs packages/webapp/node_modules)
bam ci-checks                   # everything CI runs, in one command
bam build                       # build the webapp into packages/webapp/build/, so `lauschkiste`
                                 # alone serves both the API and the UI on :5556 -- no npm start
                                 # needed just to use the app (no hot-reload though; for active
                                 # frontend dev use `cd packages/webapp && npm run dev` instead)
bam docker-dev                  # local mpd+lauschkiste+webapp stack without PulseAudio/hardware
uv run lauschctl debug sniff      # print all messages on the publishing queue
```

Webapp (`cd packages/webapp`): standard CRA scripts — `npm start`, `npm run build`, `npm test`.

## Before committing / opening a PR

- If you touched **any** `.py` file: run `bam lint` and fix findings (or justify exceptions
  in the PR).
- Run `bam test` if you touched code with test coverage, and add tests for new modules
  under `test/`.
- Commit message prefixes `(docs)`, `(maint)`, `(packaging)` are used for trivial changes that
  don't need an issue number.
- Target branch is `future3/develop`, not `future3/main`, unless told otherwise.
- Full contributor guidelines: `CONTRIBUTING.md`.

## Testing without Raspberry Pi hardware

The default `player.backend: local_audio` + `generic_usb`/`fake_reader_gui` RFID readers need no
Pi-specific hardware or extra system packages at all -- `uv run lauschkiste` plays through this
machine's normal audio output directly. The Docker dev environment
(`documentation/developers/docker.md`) is still useful for testing the full stack (core, webapp and
nginx-free FastAPI static serving) in isolation, but is no longer required just to avoid GPIO/
mpd/RFID hardware.

## Key docs to read before larger changes

- `documentation/developers/core-and-plugins.md` — core/plugin contract design
- `documentation/builders/concepts.md` — core, plugins, actions, events in one page
- `documentation/builders/actions.md` — action format for cards and config
- `documentation/developers/coreapps.md` — what each core entry-point script does
- `documentation/developers/python.md` — Python dev environment notes
- `documentation/developers/webapp.md` — webapp dev notes
- `documentation/developers/docker.md` — Docker-based dev environment
- `documentation/developers/status.md` — feature parity status vs. v2
