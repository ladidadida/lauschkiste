# Core and Plugin Contract

> First step of the "Advanced plugin system" track in
> [roadmap-core-architecture.md](roadmap-core-architecture.md). Implementation status: see
> "Implementation plan" below.

## Terms

- **Core** - always shipped as part of the `lauschkiste` package, always running, not switchable.
  Everything a jukebox needs to be a jukebox.
- **Plugin** - a separately installable package. Either *bundled* (lives in this repo, installed
  alongside the core) or *external* (installed from elsewhere via pip/uv). Only active when listed
  in the config (opt-in, for bundled and external plugins alike).
- **Module** - umbrella term for a core module or a plugin: anything that declares actions,
  queries and events through the contract below.

Core modules and plugins use the same contract, so a plugin can reach as deep as a core module.
They differ only in how they are shipped, loaded and enabled.

## What belongs in the core

**Core is what makes sense on every machine Lauschkiste runs on: a regular Linux PC, a Raspberry
Pi, a container.** Platform- or hardware-specific functionality and integrations with external
systems are plugins. Shutting down is the typical example: on a Pi-based box it is essential, on a
desktop PC nobody wants Lauschkiste to power the machine off: the core `hardware` module only
offers it when a board support plugin is enabled. See [Hardware](hardware.md) for boards, devices
and pins.

## Split

| Core | Plugins |
| --- | --- |
| Player (with the `local_audio` backend) | Board support: `board_raspberry_pi` |
| Library (index, metadata, cover art, see below) | Devices: `gpio_controls`, `battery`, `power_button` |
| Hardware (pins and buses in use, board, shutdown/reboot) | Player backend `mpd` |
| Card database and card action dispatch | RFID reader drivers (one plugin per driver) |
| Settings / system | MQTT |
| System info (IP address, disk usage, CPU temperature, restart Lauschkiste service) | Card synchronisation |
| Volume (incl. output selection, e.g. speakers vs. Bluetooth) | |
| Timers | |
| Jingle (startup/shutdown sound) | |
| Input devices via evdev (USB buttons, media keys, Bluetooth headset buttons) | |

Board support plugins (one per board family) describe the board's pins and interfaces and power it
off; device plugins (buttons, battery, power button) are board-independent and get their pins
through the core `hardware` module. Details in [Hardware](hardware.md).

**Autohotspot** is network configuration, not runtime functionality, and moves to `lauschctl setup`.

### Library

With `local_audio` as the default backend there is no mpd database behind the player anymore, so
the core **Library** module owns what mpd used to provide. Today `local_audio` reports only file
name, position and state (no title, artist, album or duration), album/artist browsing returns 501,
and cover art only covers embedded MP3 (ID3) images through the mpd backend. The Library module:

- keeps an index of the music library in SQLite, built from tags read with `mutagen` (MP3, FLAC,
  MP4/M4A, Ogg/Opus, ...). A scan runs on `library.update()` (the existing refresh endpoint) and
  after uploads and deletions through the library API;
- answers album/artist listings, songs of an album and search from that index;
- provides cover art per song and album from embedded images or folder images
  (`cover.jpg`/`folder.jpg`/...), cached;
- supplies title, artist, album, track and duration for the player status, independent of the
  active backend.

Already backend-independent and staying as is: folder playlists
(`lauschkiste.playlistgenerator.PlaylistCollector`, including `.m3u`) and file management (upload,
folders, delete). Audiobooks, radio and podcasts are separate core modules, see
[Content types](content-types.md).

Not planned for now: saved user playlists, ReplayGain, gapless playback, crossfade.

The RFID *reader framework* (reader thread, same-id delay, card removal, dispatch) is core; only
the hardware drivers are plugins. Without a reader plugin the core runs fine, cards can still be
managed and triggered through the API.

Core never special-cases a plugin. Where core behavior needs a platform-specific step, it runs an
*action*, and plugins contribute actions:

- **Timers** run an action when they expire instead of hard-wiring "shutdown". On a PC that is
  e.g. `player.stop`; with a board plugin `hardware.shutdown` works as well. The same applies to
  cards: a "shut down" card only works while a board plugin is enabled.
- **Webapp:** `GET /api/v1/modules` lists the active modules with their actions and queries. The
  webapp shows e.g. the shutdown button only if a board is active (`GET /api/v1/hardware`).
- Shutting down itself stays simple: the plugin calls `poweroff`, systemd sends SIGTERM, and the
  core runs its normal graceful shutdown (jingle, stop playback, save state).

## Why

Today every piece of functionality is wired up by hand in several places:

- `lauschkiste.daemon.run()` calls each module's `register()`/`start()`/`stop()` explicitly, and start
  order is encoded only in comments.
- Every REST route in `lauschkiste.api.fastapi_server` is hand-written per method and reaches the object
  via the former `jukebox.registry.get()`.
- RFID card actions, `card_removal_action` and `second_swipe_action` are stored as
  `(package, plugin, method)` plus untyped `args`/`kwargs`; arguments are only checked when a card is
  swiped. Aliases live separately in `command_aliases.py`.
- Nothing states which threads may call a module: the API executor (4 workers), the RFID reader
  thread and timers all call the same objects.
- Player backends and reader drivers are selected by importing a module path from a hard-coded
  table; their dependencies are `pyproject.toml` extras of the core package.

## Goals

- One declaration per operation yields the REST route (typed, OpenAPI), the card action and the
  in-process call.
- Plugins as real packages: own dependencies, discovered via entry points, enabled by config.
- Start/stop order derived from declared dependencies.
- A stated threading model with a safe default.
- Card actions validated when they are stored, not when a card is swiped.
- Existing `cards.yaml` files keep working (automatic migration).
- REST paths the webapp uses today stay unchanged.

## Non-goals (for now)

- Webapp UI contributed by plugins.
- Extension points beyond player backends, reader drivers and library sources (see "Extension
  points").
- A plugin index, versioned plugin API or sandboxing.

## The contract

```python
from lauschkiste.contract import Plugin, Context, action, query


class Mqtt(Plugin):
    name = "mqtt"                 # prefix for routes, events and action ids
    requires = ("player", "volume")

    def start(self, ctx: Context) -> None:
        self._ctx = ctx
        self._client = connect(ctx.config["host"])
        ctx.subscribe("player.status", self._forward)

    def stop(self) -> list[threading.Thread]:
        self._client.disconnect()
        return []

    @action()
    def reconnect(self) -> None: ...

    @query()
    def connected(self) -> bool:
        return self._client.is_connected()
```

Core modules subclass `CoreModule` instead of `Plugin`; everything else is identical.

### `@action` and `@query`

| Aspect | `@action` | `@query` |
| --- | --- | --- |
| Purpose | changes state | reads state |
| HTTP method | `POST` (default), `PUT`, `DELETE` | `GET` |
| Default path | `/api/v1/<name>/<method_name>` | `/api/v1/<name>/<method_name>` |
| Arguments | JSON body, model built from the signature | query parameters |
| Card action id | `<name>.<method_name>` | not card-triggerable |
| In-process call | `ctx.modules.volume.set_volume(12)` | same |

- Arguments are declared by the Python signature with type hints. The framework builds a Pydantic
  model from it; FastAPI validates REST calls, and the same model validates card actions when a card
  is registered and when `cards.yaml` is loaded.
- `path` and `method` are optional. Without them the path is derived from the method name
  (`POST /api/v1/volume/set_volume`); where the REST shape matters (webapp, readability) the module
  declares them (`@action(method="PUT", path="/level")`). Card action ids and in-process calls are
  unaffected by the path.
- `path` is relative to `/api/v1/<name>`. An absolute path (starting with `/api/`) is allowed only
  for core modules, to keep today's webapp paths stable (e.g. `/api/v1/settings`).
- An operation a backend doesn't support raises `NotImplementedError`; the framework maps it to
  HTTP 501 (as `_run_on_executor` does today).
- Return values are serialized as JSON; `None` becomes `204 No Content`.
- `name=` overrides the operation name where the method name can't be used, e.g.
  `@action(name='stop') def stop_playback(...)` next to the lifecycle method `stop()`.
- Parameters and return values must be type-annotated; the module fails to load otherwise.
- `extra_routes(router)` is an escape hatch for routes the declarations can't express (e.g.
  streaming uploads); they are not part of the versioned interface.

### Lifecycle hooks

- `start(ctx)` - in dependency order; register at extension points here.
- `ready()` - after every module has started, in the same order. All actions are available now:
  resolve configured actions, start threads that trigger actions (e.g. RFID readers).
- `stop()` - in reverse order; returns threads the daemon waits for.

### Events

Every event is declared with a Pydantic model, like actions; there are no untyped events.

```python
class PlayerStatus(BaseModel):
    state: Literal["play", "pause", "stop"]
    elapsed: float
    duration: float | None
    title: str | None


class Player(CoreModule):
    status = event("status", PlayerStatus)

    def _on_change(self):
        self._ctx.publish(self.status, PlayerStatus(...))
```

- Declared events are listed with the module's actions and queries in `GET /api/v1/modules`, so
  the webapp and plugin authors see the payload shape.
- Payloads are validated when published: in tests and development mode a mismatch raises; in
  production it is logged and the event is dropped, so a faulty plugin cannot break the event
  stream for everyone.
- Existing topics (`playerstatus`, `rfid.card_id`, `core.*`) get proper models in step 2, replacing
  today's mpd-style string fields (`'elapsed': '42.000'`, `'random': '0'`), and are renamed to the
  `<name>.<event>` scheme (`playerstatus` -> `player.status`). The webapp is updated in the same
  step. The player status gains title, artist, album and duration once the
  Library module provides them.

### `Context`

Passed to `start()`; the only way a module reaches the rest of the system:

- `ctx.config` - the module's own config section (`cfg[name]` for core, `cfg['plugins'][name]` for
  plugins), created if missing.
- `ctx.publish(event, payload)` / `ctx.revoke(event)` - publish a declared event; the topic is
  `<name>.<event>`.
- `ctx.subscribe(topic_prefix, callback)` - react to events of other modules.
- `ctx.modules.<name>` - other started modules, restricted to those listed in `requires` (accessing
  an undeclared one raises).
- `ctx.executor(name, workers=1)` - a dedicated thread pool for long-running work (library scans),
  shut down by the framework.
- `ctx.logger` - `jb.<name>`.

### Settings

A module declares its config section as a pydantic model, `settings = MySettings`. Field titles,
descriptions and limits (`Field(..., ge=0, le=100, title=..., description=...)`) end up in the
JSON schema the web app renders as a form; an `ActionEntry` field (action plus arguments, from
`lauschkiste.contract`) is shown as an action picker. The models are only the description: modules
keep reading `ctx.config` with the same defaults.

- `GET /api/v1/settings/modules` lists schema and current values of every running module with
  settings, `PUT /api/v1/settings/modules/<name>` with `{"values": {...}}` validates the given
  fields and writes them to the config file right away.
- After a change the module's `settings_changed(changed)` hook runs; it returns True if the change
  takes effect immediately. Otherwise `GET /api/v1/settings/restart` reports that a restart is
  needed (`system.restart_service`).
- `GET /api/v1/plugins` lists installed plugins (enabled, running, problem, missing extras);
  `PUT /api/v1/plugins/<name>` with `{"enabled": true}` enables one (after a restart).

## Loading and enabling

**Core modules** are listed in code in the `lauschkiste` package. They always start; there is no
switch.

**Plugins** advertise themselves under the entry-point group `lauschkiste.plugins`:

```toml
# packages/plugins/mqtt/pyproject.toml
[project]
name = "lauschkiste-plugin-mqtt"
dependencies = ["lauschkiste", "paho-mqtt"]

[project.entry-points."lauschkiste.plugins"]
mqtt = "lauschkiste_plugin_mqtt:Mqtt"
```

and are enabled by listing them in `lauschkiste.yaml`; their config lives under the same key:

```yaml
plugins:
  mqtt:
    host: 192.168.1.10
  board_raspberry_pi:
    sound_card: max98357a
  gpio_controls:
    buttons:
      next: {pin: GPIO5, on_press: {action: player.next}}
  rfid_reader_rdm6300:
    device: /dev/ttyS0
```

- Installed but not listed: not loaded (not even imported).
- Listed but not installed: logged as an error, everything else starts.
- Bundled plugins live under `packages/plugins/<name>/` as uv workspace members. Their
  dependencies move out of the core `pyproject.toml` extras into each plugin package. The installer
  installs the bundled plugins and pre-fills `plugins:` for the ones the user selected.
- `lauschctl plugin list|enable|disable|install` manages this from the command line. A plugin whose
  dependencies are optional extras of its package names them in `extras` (e.g.
  `extras = ('gpio',)`); `lauschctl plugin enable <name> --with-extras` installs them.
- Plugins can declare capabilities they offer (`provides`) and need (`needs`), e.g. a board plugin
  `provides = ('board', 'gpio', 'i2c')` and a battery gauge `needs = ('i2c',)`. A plugin can only be
  enabled when the enabled plugins provide all it needs, and only one plugin may provide `board`
  (web app, `PUT /api/v1/plugins/<name>` and `lauschctl plugin enable` refuse; at startup such a
  plugin is skipped with a problem). See [Hardware](hardware.md).

## Versioning and compatibility

A plugin depends on two things, and both are versioned separately from the `lauschkiste` package
version:

- **Framework contract** - `lauschkiste.contract.CONTRACT_VERSION`: the `Plugin` base class,
  `@action`/`@query`/`event`, `Context`, lifecycle and threading semantics.
- **Module interfaces** - every module (core or plugin) declares `interface_version`, covering its
  actions, queries, event models and extension-point protocols.

```python
class Mqtt(Plugin):
    name = "mqtt"
    interface_version = "1.0"
    contract = ">=1.0,<2"
    requires = {"player": ">=1.2,<2", "volume": ">=1.0,<2"}
```

- Rules (semantic versioning): adding something (a new action, an optional field in an event model)
  is a minor bump; removing, renaming or changing a type is a major bump.
- `requires` accepts a plain tuple of names (any version) or a mapping to version specifiers.
- At startup the module manager checks `contract` and every `requires` specifier. A plugin that
  doesn't match is skipped with a message naming the module, the required and the actual version.
  Core modules are shipped together and always match.
- Versions are listed in `GET /api/v1/modules`.
- **Enforced in CI, not by discipline:** a test renders every module's interface (JSON schemas of
  action/query arguments and results, event models, extension-point protocols) and the framework
  contract into snapshot files in the repo. A change to a snapshot without the matching version
  bump fails the build: breaking change without major bump, or addition without minor bump.
- The plugin's `lauschkiste` package dependency stays a coarse lower bound only.

## Lifecycle and ordering

- Core modules and enabled plugins are sorted together by `requires` (topological sort). A cycle or
  a missing dependency is a startup error that names the modules involved.
- A core module may not require a plugin.
- `start()` runs in that order, `stop()` in reverse. Threads returned by `stop()` are joined within
  the existing shutdown timeout.
- If a core module fails to start, the daemon fails to start. If a plugin fails, it and every
  plugin that (transitively) requires it are skipped and logged; the rest keeps running.
- The API server starts after all modules and mounts the generated routes.

## Threading model

- Actions and queries can be called concurrently from API workers, the RFID reader thread, timers
  and other modules.
- **Default:** each module gets its own re-entrant lock; every `@action` and `@query` runs under it.
  Calls to *different* modules run in parallel, calls into the *same* module are serialized. This is
  the safe default for code written without concurrency in mind, which matters most for external
  plugins.
- `concurrency = "threadsafe"` on the class disables the lock for modules that handle it themselves
  (e.g. the player, whose `PlayerCoordinator` already guards its state with its own lock).
- Per operation, `@query(exclusive=False)` lets cheap reads skip the lock so status polling never
  waits behind a slow action.
- Long-running work (scans, downloads) belongs on `ctx.executor(...)`, not inside the lock.

## Extension points

Some core modules need implementations supplied by plugins. The owning core module declares the
extension point; plugins register against it in `start()`:

```python
# in a plugin
def start(self, ctx):
    ctx.modules.player.backends.register("mpd", MpdBackend(ctx.config))
```

Three extension points are needed from the start, because today's behavior depends on them:

- **Player backends** (`player.backends`) - `local_audio` is registered by the core; `mpd` becomes a
  plugin. `player.backend` config keeps selecting the active one. The duck-typed backend surface
  `PlayerCoordinator` calls today becomes an explicit protocol.
- **RFID reader drivers** (`rfid.readers`) - every bundled driver is a plugin (`rfid_<driver>`,
  all shipped in the `rfid-readers` package) that registers a reader factory. The reader framework keeps owning threads, timing and
  dispatch.
- **Library sources** (`library.sources`) - the core index is the local source; the `mpd` plugin can
  add its own database as a second source, streaming services later as further ones. The webapp's
  source tabs (`list_library_sources`) already expect this shape.

Further extension points ("powerful plugins": e.g. a playback filter that can veto or rewrite what
is about to play) follow the same pattern and are added when a plugin needs them.

## Card actions

New storage format in `cards.yaml` (also used for `card_removal_action` and `second_swipe_action`
in `lauschkiste.yaml`):

```yaml
'0001234567':
  action: player.play_folder
  args:
    folder: Music/Rock
  ignore_same_id_delay: false
  ignore_card_removal_action: false
```

- `action` is a card action id (`<module>.<action>`), from core or an enabled plugin.
- `args` is a mapping validated against the action's model.
- Registering a card through the API validates the action and its arguments; invalid requests are
  rejected with 422.
- Unknown or invalid entries on load (e.g. a plugin that is not enabled) are kept in the file,
  logged and reported by `GET /api/v1/cards` with an `error` field, never silently dropped. They
  become valid again once the plugin is enabled.

## What goes away

- The former `jukebox.registry` (`register`, `call`, `tag`/`callable_method`), replaced by the module manager.
- `command_aliases.py` and `lauschkiste.utils.{decode_rpc_command,bind_rpc_command,decode_and_call_rpc_command}`.
- The hand-written `register_player_routes`/`register_settings_routes`/`register_cards_routes` in
  `fastapi_server.py`.
- The backend/driver import tables in `lauschkiste.player.plugin` and `lauschkiste.rfid.reader`, and the
  `mpd`/`rpi-gpio`/reader extras in `packages/lauschkiste/pyproject.toml`.
- `documentation/builders/rpc-commands.md`, replaced by a generated list of card actions.

## Implementation plan

1. **Framework** (`lauschkiste.contract`) -- *done*: `CoreModule`, `Plugin`, `Context`,
   `@action`/`@query`/`event`/`extension_point`, module manager (entry-point discovery, opt-in,
   ordering, version checks, lifecycle incl. `ready()`, locks), route generation, action catalog
   with validation, interface snapshots and the CI check (`test/contract/`).
2. **Migrate the core** -- *done*: `system` (info, logs, web app settings), `cards`, `player`
   (backend extension point, typed `player.status`), `rfid` (reader framework, driver extension
   point, `rfid.card_detected`). REST paths the webapp uses stayed the same except
   `DELETE /api/v1/cards/{card_id}`; topics were renamed (`playerstatus` -> `player.status`,
   `rfid.card_id` -> `rfid.card_detected`, `core.*` -> `system.info`) and the webapp follows.
   Card dispatch goes through the action catalog.
3. **First bundled plugins** -- *done*: `packages/plugins/mpd` (player backend) and
   `packages/plugins/rfid-readers` (one plugin per driver in one package; driver dependencies are
   extras of that package). The core has no optional dependencies left. The RFID reader
   configuration tool moved along (`lauschkiste_plugin_rfid_readers.configure`) and enables the driver plugins
   of the readers it configures. Snapshots of bundled plugins live in `<package>/interfaces/`.
4. **Remove the old mechanism** -- *done together with step 2*: registry, command aliases, RPC
   helpers, hand-written routes and the player backend import table are gone.
5. **Library** -- *done*: `lauschkiste.library` core module with a SQLite index (`mutagen` tags and
   durations, incremental rescans on start-up, refresh, upload and delete), album/song/search
   queries, cover art (embedded pictures or folder images, cached, served at
   `/api/v1/library/covers/<name>`), and the `library.sources` extension point (the `mpd` plugin
   registers its database there). The player plays library albums through the new backend
   operation `play_files` and fills title/artist/album/duration/cover of `player.status` from the
   index. The library's routes moved from `/api/v1/player/*` to `/api/v1/library/*`; the local
   source id is `local`. Streaming uploads stay a hand-written route (`extra_routes`); an ASGI
   middleware limits all other request bodies to 1 MiB.
6. **Remaining core modules** -- *done*: `volume` (PulseAudio/PipeWire via pulsectl, falling
   back to the player backend's volume; soft maximum, mute, outputs with per-output volume limit,
   fade-out), `timers` (named countdowns that run an action; `shutdown` only works with a
   board support plugin), `jingle` (startup/shutdown sound through the same PortAudio output as
   `local_audio`, `jingle.play` for cards), system info in `system` (IP addresses, disk usage, CPU
   temperature, periodic `system.health`, `say_my_ip`, `restart_service`), and `input` (evdev
   devices by name with key -> action mappings, optional media keys). Not carried over: the idle-shutdown timer
   and the separate `evdev.yaml` file (device mappings now live under `input:`).
7. **Hardware** -- *done*: core module `hardware` (pins and buses in use, conflicts,
   shutdown/reboot through the board), board support plugin `board_raspberry_pi` (pin map,
   interfaces, sound card/I²C/SPI/power-off pin for `config.txt` via `lauschctl setup raspi`,
   `debug_mode`, firmware health) and the board-independent device plugins `gpio_controls`
   (buttons, rotary encoders, status LED), `battery` (MAX17048, INA219, simulator) and
   `power_button` (OnOff SHIM preset). See [Hardware](hardware.md). Not carried over: the ADS1015
   battery driver, the OnOff SHIM script, the idle-shutdown timer and the old `gpio.yaml` format.
   Autohotspot moves to the installer/`lauschctl setup` track instead.

Each step leaves the daemon runnable and the test suites green.

## Open questions

None at the moment.
