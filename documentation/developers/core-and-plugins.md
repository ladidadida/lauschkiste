# Core and Plugin Contract

> Reference for what the core, its modules and plugins are, and the contract between them. What works today:
> [Feature status](status.md).

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
| Library (index, metadata, cover art, see below) | Devices: `gpio_controls`, `battery`, `power_button`, `phat_beat` |
| Audiobooks, podcasts, radio ([Content types](content-types.md)) | Player backend `mpd` |
| Cache for downloads ([Caching](caching.md)) | RFID reader drivers (one plugin per driver) |
| Hardware (pins and buses in use, board, shutdown/reboot) | Audiobookshelf server as a source |
| Card database and card action dispatch | Podcast and radio directories |
| Settings / system | Samba share |
| System info (IP address, disk usage, CPU temperature, restart Lauschkiste service) | |
| Volume (incl. output selection, e.g. speakers vs. Bluetooth) | |
| Timers, time limits | |
| Jingle (startup/shutdown sound) | |
| Input devices via evdev (USB buttons, media keys, Bluetooth headset buttons) | |

Board support plugins (one per board family) describe the board's pins and interfaces and power it
off; device plugins (buttons, battery, power button) are board-independent and get their pins
through the core `hardware` module. Details in [Hardware](hardware.md).

**Autohotspot** is network configuration, not runtime functionality, and is done by `lauschctl setup autohotspot`.

### Library

With `local_audio` as the default backend there is no mpd database behind the player, so the core **Library**
module provides what browsing needs:

- an index of the music library in SQLite, built from tags read with `mutagen` (MP3, FLAC, MP4/M4A, Ogg/Opus,
  ...). A scan runs on `library.update()` (the refresh endpoint), when files change and after uploads and
  deletions through the library API;
- album/artist listings, songs of an album and search from that index;
- cover art per song and album from embedded images or folder images (`cover.jpg`/`folder.jpg`/...), cached;
- title, artist, album, track and duration for the player status, independent of the active backend.

Backend-independent as well: folder playlists
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

## Goals

- One declaration per operation yields the REST route (typed, OpenAPI), the card action and the in-process call.
- Plugins as real packages: own dependencies, discovered via entry points, enabled by config.
- Start/stop order derived from declared dependencies.
- A stated threading model with a safe default.
- Card actions validated when they are stored, not when a card is swiped.

Not provided: web app UI contributed by plugins, a plugin index, sandboxing.

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
  for core modules, to keep the web app's paths stable (e.g. `/api/v1/settings`).
- An operation a backend doesn't support raises `NotImplementedError`; the framework maps it to
  HTTP 501 .
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
- Event topics follow the `<name>.<event>` scheme (`player.status`, `rfid.card_detected`, ...).

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
- **Secrets** (API keys, passwords): mark a field `Field(..., json_schema_extra={'secret': True})`. The
  web app shows a password field; `GET` never returns the value (`secrets_set` lists the fields that
  have one) and an empty value on save keeps the old one. The values are not written to the main
  config but to `secrets.yaml` next to it (mode 0600, same key path, `plugins.<name>.<key>`), which
  people neither share nor back up by accident. The module still reads them with `ctx.config.get(...)`.
  On the command line: `lauschctl config set plugins.<name>.<key> --secret` (asks for the value),
  `lauschctl config get` hides them (`--reveal` shows them).
- **Translations of a plugin** ship with its package: `<package>/translations/<language>.json` (`en.json` is
  the base and complete, `de.json` etc. are optional). A package with several plugins (devices, RFID readers) lists
  them all in one file. For every plugin the file has its display name and the texts of its settings in the shape
  of `settings.fields.<plugin>` of the web app:

  ```json
  {
    "plugins": {
      "podcast_directories": {
        "name": "Find podcasts",
        "description": "Search for podcasts in several directories and subscribe with one tap.",
        "fields": {
          "itunes": {
            "label": "Apple Podcasts", "help": "…",
            "country": {"label": "Country", "help": "…", "values": {"de": "Germany"}}
          }
        }
      }
    }
  }
  ```

  `GET /api/v1/translations/<language>` returns the bundles of all installed plugins; the web app merges them into
  its own texts (its own always win). What is missing falls back in this order: the language asked for, English
  (the web app's, then the plugin's `en.json`), the `title`/`description` of the field in the settings model, and for
  the plugin's name its `title` class attribute (`Plugin.title`, English) and finally the plugin's name made
  readable (`podcast_directories` becomes "Podcast directories", never the bare name). The `description` is the
  one-line text under the name in the plugin list; without a translation the first line of the plugin class's
  docstring is shown. A test checks that every plugin has an English name and description and that all languages of a
  plugin have the same keys as `en.json`.
- `GET /api/v1/plugins` also carries what the package says about itself (`author`, `license`, `homepage`,
  `documentation`, `issues`, from its metadata), so that a plugin list or a future plugin manager needs no
  extra files.
- `GET /api/v1/plugins` lists installed plugins (enabled, running, problem, missing extras);
  `PUT /api/v1/plugins/<name>` with `{"enabled": true}` enables one (after a restart).

## Loading and enabling

**Core modules** are listed in code in the `lauschkiste` package. They always start; there is no
switch.

**Plugins** advertise themselves under the entry-point group `lauschkiste.plugins`:

```toml
# packages/plugins/example/pyproject.toml
[project]
name = "lauschkiste-plugin-example"
dependencies = ["lauschkiste-core", "paho-mqtt"]

[project.entry-points."lauschkiste.plugins"]
example = "lauschkiste_plugin_example:Example"
```

and are enabled by listing them in `lauschkiste.yaml`; their config lives under the same key:

```yaml
plugins:
  example:
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
- Bundled plugins live under `packages/plugins/<name>/` as uv workspace members, each with its own
  dependencies. The installer installs them and pre-fills `plugins:` for the ones the user selected.
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

The basic extension points:

- **Player backends** (`player.backends`) - `local_audio` is registered by the core, `mpd` is a
  plugin. The `player.backend` setting selects the active one; the backend surface is an explicit protocol.
- **RFID reader drivers** (`rfid.readers`) - every bundled driver is a plugin (`rfid_<driver>`,
  all shipped in the `rfid-readers` package) that registers a reader factory. The reader framework keeps owning threads, timing and
  dispatch.
- **Library sources** (`library.sources`) - the core index is the local source; the `mpd` plugin can
  add its own database as a second source, streaming services can be further ones.

More that exist now: `player.level_meters` (VU meters), `player.resolvers` (turn a track address into what
is opened plus headers, so that credentials never appear in a queue), `audiobooks.sources` (books from
elsewhere), `cache.providers` (items that can be downloaded, see [Caching](caching.md)) and
`podcasts.directories` and `radio.directories` (below).

### Podcast and radio directories

A plugin that lets people find podcasts registers an object at `podcasts.directories` under an id (and an
optional `label` attribute for the name shown); for radio stations it is `radio.directories`, the same shape with
`name` and `url` instead of `title` and `feed_url`. The module merges the answers of all of them for `search` and
`top`, takes turns between directories, drops duplicates by address and names a directory that failed without
losing the others (`lauschkiste.directories`):

```python
class MyDirectory:
    label = "My directory"

    def search(self, term: str, limit: int) -> list[dict]:
        return [{"title": ..., "feed_url": ..., "author": ..., "image": ...}]  # author, image optional

    def top(self, limit: int) -> list[dict]:
        return [...]  # popular podcasts, same mappings

# in start():
ctx.modules.podcasts.directories.register("mine", MyDirectory())
```

Every directory has its own interface (some need a key, some need a second request), which is why a new
one is code and not a setting. `lauschkiste-plugin-directories` shows four examples (Apple Podcasts, fyyd,
Podcast Index, radio-browser.info). Directories send what people type to a third party; a plugin should say so in its documentation.

Further extension points ("powerful plugins": e.g. a playback filter that can veto or rewrite what
is about to play) follow the same pattern and are added when a plugin needs them.

## Card actions

Storage format in `cards.yaml` (also used for `card_removal_action` and `second_swipe_action`
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
