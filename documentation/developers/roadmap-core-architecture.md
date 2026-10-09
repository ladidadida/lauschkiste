# Roadmap: Core Architecture (Fork)

> Historical design record. It was written while the code still carried its old names: `jukebox` in this
> document is today's `lauschkiste`. What is implemented is described in [Feature status](status.md).
>
> Fork context: diverging from upstream because the direction they're pursuing isn't the direction we
> want. Building on `future3/develop` as a base — swap pieces incrementally, keep something runnable
> after every step, ditch what turns out to be dead weight along the way rather than carrying it forward.

Fork goals, roughly in the order we're tackling them:

1. **Core architecture** (this doc) — first, because everything else sits on top of it.
2. **Advanced plugin system** — first slice landed (backend-swap only, see below); the deeper
   "hook into playback/library/API layer" redesign is still being rethought from scratch, not
   adopted from upstream's `future3/draft-entrypoint-plugins` draft. See "Relationship to the
   other tracks" below.

   **Status: first slice done.** Goal was to decouple the jukebox from the Raspberry Pi: the
   default system is now a player + web UI that runs on any Linux box using its normal audio
   output, with everything Pi/mpd-specific opt-in. `player.backend` config (default:
   `local_audio`, decodes via PyAV + outputs via sounddevice/PortAudio -- no mpd, no external
   process) picks the active player backend; `jukebox.player.plugin` dispatches to it via
   `importlib.import_module`, mirroring how `jukebox.rfid.reader` already loaded a hardware
   reader module by name. The `mpd` backend, `rpi-gpio` (GPIO-attached RFID readers), and each
   bundled RFID reader module now live behind `pyproject.toml` extras instead of being
   unconditional core dependencies -- `uv sync --extra <name>` to add one. See
   `packages/jukebox/src/jukebox/player/backends/local_audio.py` and `player/plugin.py`.
   `PlayerCoordinator` (`player/coordinator.py`) already supported multiple named backends before
   this (`register_backend()`), so no coordinator changes were needed -- this slice is entirely
   about *selecting and installing* a backend, not the dispatch mechanism itself.

   **Not done, deliberately deferred:** the FastAPI-router-per-plugin guiding principle below,
   third-party/out-of-tree plugins, and a VLC backend (dispatch table is extensible, just not
   built). `local_audio` also doesn't implement MPD-style tag/album browsing (`list_albums` etc.)
   -- folder-triggered playback (the actual RFID use case) only.

   **Guiding principle for the deeper redesign (agreed, not yet implemented):** FastAPI becomes
   the *one* contract for everything, including plugins (backend and frontend) -- not just the
   browser-facing bridge. A plugin registers a FastAPI router; that's the uniform way anything
   (webapp, CLI, another plugin) calls into it, replacing today's `(package, plugin, method)`
   string addressing with a typed, documented (OpenAPI) surface. Compromise to keep this
   compatible with the "high performance" goal: in-process calls (e.g. an RFID card action
   reaching the player) invoke the router's handler function directly, skipping HTTP/ASGI
   serialization -- only genuinely external or out-of-process callers (browser, external/
   out-of-process plugins) pay for the full HTTP round trip.

   **Status: the webapp-facing half is done.** Every `player.ctrl`/`misc`/`cards` method with a
   real implementation has a typed REST route under `/api/v1/{player,settings,cards}/*` (see
   `jukebox.api.fastapi_server`'s `register_player_routes`/`register_settings_routes`/
   `register_cards_routes`) -- handlers call straight into the registered object via
   `jukebox.registry.get()`, matching the "skip serialization" compromise above without needing
   the FastAPI-router-*per-plugin* machinery this principle originally envisioned (there's no
   plugin system generating these yet, they're hand-written per method). The webapp talks REST
   only, and the generic `POST /api/v1/rpc` endpoint (plus `jukebox.api.dispatch`, which existed
   only to serve it) is **removed**. New functionality gets a typed route, not a generic call.

   Not affected: RFID card actions / `card_removal_action` (`jukebox.utils.bind_rpc_command`/
   `decode_and_call_rpc_command`, see `documentation/builders/rpc-commands.md`) still resolve
   `(package, plugin, method)` in-process via `@plugs.tag`/`registry.call()`. That's a config
   format for card actions, not an HTTP API -- replacing it belongs to the plugin-system redesign.
   Untagging methods breaks it (tried and reverted once, see git history).

   **Status (branch `core-plugin-contract`): core and plugin contract implemented**, all seven
   steps of [core-and-plugins.md](core-and-plugins.md). Earlier plan for reference:

   **Core and plugin contract** -- core is what makes sense on any machine (player,
   library, cards, settings, system info, volume, timers, jingle, input devices); platform-specific
   parts and integrations become opt-in plugins (bundled or external: `raspberry-pi` for power/GPIO/
   battery, `mpd`, RFID reader drivers, MQTT, card sync), both built on one
   contract: an `@action` declaration generating REST route, card action and in-process call,
   `requires`-based start order, a stated threading model, and `cards.yaml` migration. Draft for
   review: [core-and-plugins.md](core-and-plugins.md).
3. **Packaging/install overhaul** — install logic entirely in Python, one package + subpackages, CLI
   drives system setup instead of ~20 bash scripts. Done: see
   [packaging-and-setup.md](packaging-and-setup.md) (wheels, `install.sh`, `jukebox setup`,
   `jukebox plugin`, `jukebox update`).
4. **New name** — Lauschkiste (done).

## Current state (inherited from future3/develop)

- **Backend core**: ZMQ REP RPC server (`src/jukebox/jukebox/rpc/server.py`) — single-threaded blocking
  `recv()` loop, calls `jukebox.plugs.call()` synchronously per request. Also used inproc
  (`inproc://JukeBoxRpcServer`) so internal components (e.g. GPIO button handlers) call through the same
  path as external clients.
- **Browser-facing layer**: Tornado (`src/jukebox/jukebox/api/server.py`) bridges HTTP + WebSocket to
  that RPC. Already reasonably shaped — health check, RPC passthrough, library upload/CRUD, events over
  WebSocket via an `EventBroker` fed by ZMQ SUB — but:
  - RPC calls run through a `ThreadPoolExecutor(max_workers=1)`, which serializes all RPC traffic
    through the browser API. Same shape as the bottleneck diagnosed in a previous session (single
    REP socket + unbounded MPD timeout wedges all web requests) — just moved one layer up.
  - Library endpoints get their own executor, also sized 1.
  - No FastAPI/uvicorn anywhere yet — Tornado is the actual HTTP stack today.
- **CLI**: `run_rpc_tool.py` talks to the ZMQ REP server directly, bypassing Tornado entirely.
- **Plugin dispatch**: `jukebox.plugs.call(package, plugin, method, args, kwargs, as_thread=...)` —
  synchronous, with an opt-in "run in a separate thread" escape hatch used ad hoc per call site.

## Goal

FastAPI + uvicorn as the one middleware layer between browser (HTTP + WebSocket), CLI, and internal
plugin calls. Drop the ZMQ REP hop where it's pure indirection; decide separately whether ZMQ pub/sub is
still the right tool for the event/broadcast side once Tornado (which needed the `ZMQStream` bridge) is
gone.

## Why incremental, not big-bang

Agreed approach: build on `future3/develop`, swap parts one at a time, always have something that runs.
Expect to need cleanup passes between steps rather than one clean rewrite.

## Proposed steps

1. **Inventory concurrency needs first.** Which plugin calls are safe to run in parallel vs. must stay
   serialized against shared hardware state (audio playback, GPIO, MPD)? This decides whether "high
   performance" comes from more executor workers, from making `plugs.call` async-aware, or both — the
   real design question here, not just a mechanical framework swap.

   **Finding:** `jukebox.plugs.call()` already serializes *every* dispatched call behind one
   module-level `threading.RLock` (`_lock_module` in `src/jukebox/jukebox/plugs.py`), independent of
   which plugin/component is being called. So the `ThreadPoolExecutor(max_workers=1)` sizing in the
   Tornado bridge isn't the only serialization point — even with more HTTP-layer concurrency, all
   plugin calls still queue up behind this single lock today. Real parallelism (e.g. a library scan
   running while playback controls stay responsive) requires replacing this one-lock-for-everything
   model with something per-component/per-resource — not yet designed, tracked as an open decision
   below.
2. **Stand up FastAPI alongside Tornado**, reimplementing health/RPC/events first, still backed by the
   existing ZMQ REP client. Proves the swap without touching core dispatch.

   **Status: done.** `src/jukebox/jukebox/api/fastapi_server.py` (`FastApiServer`, `create_app`)
   reimplements health/RPC/events on FastAPI + uvicorn, running independently of and side by side with
   `jukebox.api.server.ApiServer` — nothing wires it into the daemon yet. `EventBroker` and the events
   subscription-command parsing (`parse_subscription_command`) were generalized out of their
   Tornado-specific bits so both bridges share the same code. The RPC executor here uses 4 workers
   instead of Tornado's 1, since `plugs.call()`'s own lock (see finding above) already provides the
   real serialization — more HTTP-layer workers just avoid queuing unrelated requests (e.g. `/health`)
   behind a slow plugin call. Tests: `test/api/test_fastapi_server.py`.
3. **Port the library endpoints** (upload, folders, entries, refresh — the streaming/multipart-heavy
   ones) to FastAPI.

   **Status: done.** `create_app()` in `fastapi_server.py` now also serves
   `PUT /api/v1/library/files`, `POST /api/v1/library/folders`, `GET`/`DELETE
   /api/v1/library/entries`, and `POST /api/v1/library/refresh`, backed by the same
   transport-neutral `jukebox.library.MusicLibrary`/`LibraryError` the Tornado bridge uses, so
   behavior (status codes, error `code`/`message` shape, path/type validation) matches exactly.
   Uploads stream via Starlette's `request.stream()` straight into `UploadSession.write()`
   (no full-body buffering, same as the Tornado version), executed through a dedicated
   single-worker library `ThreadPoolExecutor` kept separate from the RPC executor. Added a
   `_read_limited_body()` helper so the RPC and library-JSON endpoints enforce the same 1 MiB
   streaming body cap (`MAX_MESSAGE_SIZE`) Tornado's `stream_request_body` handlers had -- easy to
   miss on FastAPI since `await request.body()` alone doesn't cap size. Tests ported 1:1 from
   `test/api/test_server.py`'s library test class into `test/api/test_fastapi_server.py`.
4. **Port the WebSocket event broker** to FastAPI's WebSocket support; decide fate of the ZMQ pub/sub hop
   underneath (keep it, or replace with in-process asyncio queues now that everything's one process).

   **Status: done**, but see the reversed decision below. Was already implemented as part of
   step 2 (`_handle_events_websocket` in `fastapi_server.py`); what was left was the decision and
   one real gap, both closed now:
   - ~~**ZMQ pub/sub stays.**~~ **Reversed, see "Simplify away ZMQ and nginx" below.** Original
     reasoning was that `jukebox.publishing` is a system-wide bus, not Tornado-specific, so nothing
     to replace. Still true, but doesn't mean it needs ZMQ specifically -- for a single-process,
     single-Pi app with a handful of local browser clients, ZMQ solves a distributed-systems
     problem (many independent processes, high throughput) that doesn't exist here anymore now
     that dispatch is in-process. `FastApiServer` bridges it via `zmq.asyncio` today; slated to
     become a plain `asyncio.Queue` broadcast instead.
   - **Gap found and fixed: cross-origin WebSocket rejection.** Tornado's `WebSocketHandler`
     rejects cross-origin handshakes by default; Starlette/FastAPI don't do this at all. Without a
     fix, any page in a victim's browser could open a WebSocket to this API and read every
     published topic (classic cross-site WebSocket hijacking) -- worse than a theoretical gap,
     since `api.bind_address` defaults to loopback but nginx proxies it out to the LAN regardless.
     Added `_is_same_origin()` (same-origin check against the `Host` header, mirroring Tornado's
     default `check_origin`) to `fastapi_server.py`. Tests:
     `test_events_websocket_rejects_cross_origin_handshake` /
     `..._allows_same_origin_and_no_origin_header`.
5. **Reassess the ZMQ REP/REQ layer** once FastAPI fully replaces Tornado — does it still earn its keep,
   or can CLI and webapp both call the same in-process FastAPI app / plugin dispatch directly and drop a
   hop?

   **Status: done.** Both remaining ZMQ consumers are gone: the interactive Python RPC CLI
   (`run_rpc_tool.py`) and, once it turned out there was a second one, the C CLI client
   (`src/cli_client/pbc.c`) -- neither was migrated, both were removed outright ("we'll find
   another solution for that later," not designed yet). With no consumers left,
   `jukebox.rpc.server.RpcServer`, `jukebox.rpc.client.RpcClient`, and the `pyzmq` dependency were
   deleted too. (`process_request`, later moved to `jukebox.api.dispatch`, served the FastAPI
   `/api/v1/rpc` handler until that was removed too.) There is currently no CLI/RPC tool at
   all; whatever replaces it will presumably be built against the FastAPI HTTP endpoint from the
   start, per the "everything through FastAPI" principle (see "Advanced plugin system" above).

   `jukebox.daemon`'s main thread now blocks on `self.api_server.join()` instead of
   `self.rpc_server.run()` -- `FastApiServer` (a `threading.Thread`) is the only long-running
   server left, so joining it is what keeps the process alive until `exit_gracefully()` terminates
   it.
6. **Remove the Tornado dependency**, and check what else assumed it: webapp nginx config
   (`resources/default-settings/nginx.default`), `installation/routines/setup_jukebox_webapp.sh`, ports
   referenced in config defaults.

   **Status: partially done.** The Tornado *HTTP bridge* is gone: `jukebox.api.server` deleted,
   `jukebox.daemon` now starts `FastApiServer` instead of `ApiServer`, on the exact same
   `api.bind_address`/`api.port` config keys and default port (5556) -- so nginx, the webapp's Vite
   dev proxy, and `docker-compose.yml` needed zero changes. Verified end-to-end (not just unit
   tests): started the real component-wired daemon pieces plus `FastApiServer` in a throwaway
   config dir, hit `/api/v1/health` and `/api/v1/rpc` over real HTTP, got a correct RPC response,
   shut down cleanly.

   **Update:** the `tornado` *package* is gone now too. It was still a dependency because
   `jukebox.publishing.server.PublishServer` (the core pub/sub proxy, not the browser bridge --
   the actual internal message bus everything uses) imported `zmq.eventloop.ioloop.IOLoop`, which
   unconditionally does `from tornado.ioloop import IOLoop` under the hood (verified by
   uninstalling tornado and watching `PublishServer` fail to import). Replacing `PublishServer`
   with the in-process `EventBus` (see "Simplify away ZMQ and nginx" below) removed that import
   entirely -- `tornado` is no longer in `pyproject.toml`.
7. **Measure before/after.** "High performance" needs a number, not a vibe — concurrent library scans,
   cover-art fetches, and RPC calls during active playback are the realistic stress cases.

## Simplify away ZMQ and nginx

**Decision (discussed, not yet implemented):** both are inherited complexity from the upstream
project's original design, not something this fork chose, and neither pulls its weight for a
single-process app on a single Pi serving a handful of local browser clients over a home LAN:

- **ZMQ** (`pyzmq`) solves distributed-systems problems -- many independent processes, potentially
  high throughput -- that no longer exist here. Plugin dispatch is already in-process (see "Old
  plugin system removed" below), the FastAPI RPC handler already calls `process_request` directly
  rather than through ZMQ REP, and the pub/sub side (status updates, a handful of events per
  second even with several browser tabs open) is comfortably within what a plain `asyncio.Queue`
  broadcast handles. Keeping ZMQ only makes sense if this needs to become a genuinely distributed
  system later (components running as separate processes/containers, possibly relevant if the
  later plugin-system redesign goes that direction) -- not a given, not worth carrying the
  complexity for speculatively.
- **nginx** exists to reverse-proxy `/api/` to the (loopback-bound) FastAPI process and serve the
  built webapp's static files. FastAPI/uvicorn can serve static files directly (`StaticFiles`) and
  bind wherever needed -- nginx's real strengths (TLS termination, high-concurrency static serving,
  buffering under load) aren't relevant at Pi-jukebox scale.

### ZMQ pub/sub: done

`jukebox.publishing` no longer uses ZMQ at all. Replaced with `jukebox.publishing.bus.EventBus`: a
plain thread-safe last-value-cache + subscriber registry (lock + dict + set, no reactor loop, no
background thread). `publish()` is called synchronously from whatever thread published (RFID
reader thread, timer threads, the daemon thread, ...) and dispatches directly to registered
callbacks -- for the FastAPI bridge, that callback (`EventBroker.publish`) is itself already
thread-safe via `asyncio.run_coroutine_threadsafe` (it had to be, to deliver ZMQ-sourced events
into the event loop before; now it does the same job one hop shorter).

`jukebox.publishing.get_publisher().send/resend/close_server` -- the call-site API every component
uses -- is unchanged, so no component code needed to change. `Publisher` is no longer thread-local
(the old "one instance per thread, ZMQ sockets aren't thread-safe" rule doesn't apply to a
lock-protected dict): one shared instance is enough now.

Turned out to also fully drop the `tornado` dependency as a side effect: it was only needed
because `jukebox.publishing.server.PublishServer` imported `zmq.eventloop.ioloop.IOLoop`, which
unconditionally pulled in `tornado.ioloop`. Deleting that whole reactor-based server (see above)
removed the last thing requiring it -- verified with `uv sync` after removing it from
`pyproject.toml` and running the full test suite.

`run_publicity_sniffer.py` (the one external-process consumer, previously a raw ZMQ TCP
subscriber) now connects to `/api/v1/events` as a plain WebSocket client (`websockets` package,
added to `[project.dependencies]`) -- verified against a real running `FastApiServer` +
`components.publishing`, not just unit-tested. New tests: `test/publishing/test_bus.py`, including
one that reproduces and verifies the fix for the original code's "log handler republishes through
the bus it's logging an error for" recursion hazard (see `misc/loggingext.py`'s `PubStreamHandler`)
-- `EventBus.publish()` caps that at one extra level via a thread-local re-entrancy depth guard
instead of the old code's thread-identity/recursion-counter check.

Also removed the now-meaningless `publishing.tcp_port` config key and the `5558` port references
that went with it (`jukebox.default.yaml`, `docker-compose.yml`, both Dockerfiles' `EXPOSE`).

### nginx: done

FastAPI now serves the webapp's static build, `/logs`, and a couple of fallback pages directly
(`jukebox.api.webapp_static.register_webapp_routes`, mounted last in `create_app()` so it never
shadows `/api/v1/*`). Deliberately ported nginx's *actual* behavior rather than inventing new
behavior -- e.g. still no SPA deep-link fallback to `index.html` for unknown paths, since
`nginx.default`'s `try_files $uri $uri/ =404` didn't do that either.

- `index.html` (`/` and `/index.html`) served with `Cache-Control: no-store`; falls back to a
  "bundle is missing" page if the build hasn't been installed, matching the old `@buildwebui`
  error page.
- `build/static/*` mounted via Starlette's `StaticFiles`; any other root-level build file (favicon,
  manifest, locales/*, ...) served through a catch-all with directory-traversal protection
  (resolves the candidate path and checks it's still inside `build_dir` -- tested explicitly, see
  `test_catch_all_rejects_path_traversal_outside_build_dir`).
- `/logs` and `/logs/<file>`: a small directory listing + flat file server over `shared/logs`
  (nginx's `autoindex on`), filename-only path validation (no traversal via `/logs/../secret`).
- Unknown paths get a generic 404 page (nginx's `error_page 404 = /404.html`).

**Bind address changed from `127.0.0.1` to `0.0.0.0`** (`api.bind_address` in
`jukebox.default.yaml`): nginx used to be the only thing reachable from the LAN, reverse-proxying
to a loopback-only browser bridge. There's no separate reverse proxy anymore, so the FastAPI server
itself needs to be reachable directly -- this is the one meaningful behavior change from the
nginx-based setup, not just a refactor, so it's called out explicitly here rather than buried in a
commit message.

Installer changes: `installation/routines/setup_jukebox_webapp.sh` no longer installs/configures
nginx, just downloads the webapp bundle and verifies the build directory exists.
`prepare_dependencies.sh` no longer adds `nginx`/removes `apache2`.
`installation/routines/setup_kiosk_mode.sh`'s Chromium kiosk URL changed from `http://localhost`
(port 80, nginx) to `http://localhost:5556` (FastAPI). Deleted
`resources/default-settings/nginx.default`, `resources/html/404.html`,
`resources/html/runbuildui.html` (content now inlined in `webapp_static.py`; nothing else
referenced them). Verified end-to-end: started a real `FastApiServer` against this repo's actual
`src/webapp/build` and `shared/logs`, hit `/`, `/favicon.ico`, `/logs`, an unknown path (404), and
`/api/v1/health` over real HTTP.

Not verified here (no real Pi/systemd/apt environment available): the installer script changes
themselves. Same caveat as the earlier `uv` installer migration -- worth a smoke test before
relying on them.

### ZMQ REP/REQ, run_rpc_tool.py, and the C CLI client: done (removed, not migrated)

ZeroMQ is gone from the entire project now -- the last two consumers were removed outright rather
than migrated onto FastAPI, since neither is needed *right now* and "we'll find another solution
for that later":

- `run_rpc_tool.py` (interactive Python RPC CLI) and its wrapper `tools/run_rpc_tool.sh`.
- `src/cli_client/pbc.c` (a separate C CLI client) -- found *while* removing `run_rpc_tool.py`:
  earlier notes here claimed the Python CLI was the *only* remaining ZMQ consumer; that was wrong,
  this C client was a second one, missed on the first pass.

With both gone, `jukebox.rpc.server.RpcServer`, `jukebox.rpc.client.RpcClient`, `ci/installation/
zmq_smoke.py`, and the `pyzmq` dependency were deleted too (verified nothing else imports `zmq`
anywhere in `src/` or `test/`). Also cleaned up what existed only to support ZMQ: the
`libzmq5`/`python3-zmq` apt packages (`packages-core.txt`, both Dockerfiles), the dedicated
`run_raspbian_armv6_zmq` CI job that smoke-tested ZMQ on armv6, `libczmq-dev` from the main CI
workflow's apt install, and the `rpc.tcp_port` config key. The HTTP `/api/v1/rpc` endpoint and its
`process_request` dispatcher were removed later, once the webapp was fully on typed REST routes.

There is currently **no RPC/CLI tool of any kind**. Whatever replaces it should be built against
the FastAPI HTTP endpoint from the start, consistent with the "everything through FastAPI"
principle (see "Advanced plugin system" above) -- not scoped or designed yet.

## Dev tooling migrated to uv + bam

Orthogonal to the architecture work above, but done alongside it: Python dev tooling moved from
`pip` + `requirements-dev.txt` + `flake8` + hand-rolled `run_*.sh` wrapper scripts to
[uv](https://docs.astral.sh/uv/) (package manager, `pyproject.toml`) +
[bam](https://gitlab.com/cascascade/bam) (content-hash-cached task runner, `bam.yaml`) + ruff +
pyright, following the conventions of `/home/stefan/Projekte/dev/python-uv-workspace-template`
(a Copier template for fresh CLI projects -- not run directly here since this is an existing
multi-language monorepo, not a fresh scaffold, but its tool choices and `pyproject.toml`/`bam.yaml`
shape were adopted as-is).

`run_pytest.sh` / `run_flake8.sh` / `run_docgeneration.sh` / `run_markdownlint.sh` / `run_jukebox.sh`
are gone, replaced by `bam lint` / `bam test` / `bam docs` / `bam markdownlint` / `uv run python
src/jukebox/run_jukebox.py`. `ruff format` (~70 files would change) and `pyright` (178 pre-existing
errors in basic mode) are wired up as bam tasks but deliberately non-blocking (`|| true`) since the
codebase has never been run through either -- same "no formatting baseline commit yet" situation
upstream already flagged in `roadmap-plugins-and-packaging.md` for their own (not-merged-here) work.

**Update:** `requirements.txt` / `requirements-excluded.txt` are gone too now. The real Pi installer
(`migrate_to_cli/installation/routines/setup_jukebox_core.sh`) and both Dockerfiles were migrated to `uv sync`
against `pyproject.toml` directly (bootstrapping `uv` itself via the official install script if not
already present). One gotcha caught by actually building `docker/Dockerfile.lauschkiste` and importing
`zmq` inside the built image: PyZMQ must keep coming from the `python3-zmq` apt package (via
`--system-site-packages`, using the system libzmq) rather than a PyPI wheel -- `uv sync
--no-install-package pyzmq` on all three call sites keeps that true, otherwise every install would
silently reintroduce the exact "draft-enabled PyZMQ shadowing the system package" problem the
installer already has one-time cleanup logic for. (PyZMQ has since been removed entirely.)

**armv7 verified under QEMU** (no real Pi hardware yet): `docker/armv7/lauschkiste.Dockerfile` (rebased
from buster -- Python 3.7, below `requires-python` -- to trixie) builds and `jukebox run` serves
the API on armv7l. The installer's `_jukebox_core_install_python_requirements` was run in the
`ci/ci-debian.Dockerfile` base (Raspbian trixie repos, `packages-core.txt`) on armv7l as user `pi`,
followed by the service's `ExecStart` in a minimal systemd-like environment. That caught three
real bugs, now fixed: `cffi` (via `sounddevice`) has no armv7l wheel and failed to build without
`libffi-dev` (added, plus `build-essential` since `evdev` never has wheels); a failed `uv sync` did
not abort the installer (now `exit_on_error`); and the service ran `uv run`, but `uv` lives in
`~/.local/bin`, which isn't on the systemd user manager's PATH (now calls `.venv/bin/jukebox`
directly). Source builds under QEMU take ~1-2 min. Still open: the service `Requires=mpd.service`
and the installer always sets up mpd, although `local_audio` is the default backend. This closes out the last piece
of Track B (packaging/install) that isn't a full install/update rewrite -- runtime dependency
installation is uv-based everywhere now, the rest of Track B (bundling the webapp as package data,
resolving checkout-relative paths, etc.) is still open.

## Old plugin system removed

The old dynamic, config-driven plugin system (`jukebox.plugs`, `@plugs.register` /
`@plugs.initialize` / `@plugs.finalize` / `@plugs.atexit` decorators, one lock serializing every
call) has been removed entirely, not just deprioritized. Replaced by `jukebox.registry`: a minimal
explicit call registry with the same `(package, plugin, method)` addressing (so the webapp's RPC
call shape didn't need to change) but no dynamic loading, no decorator magic, and no shared global
lock -- `jukebox.daemon.run()` now wires up each component directly (`register()` / `start()`
calls), and each component is responsible for its own thread-safety.

Everything not immediately essential was stripped along with it: `gpio`, `mqtt`, `volume`,
`timers`, `battery_monitor`, `controls`, `jingle`, `hostif`, `synchronisation` are gone from
`src/jukebox/components`, deleted rather than archived (recoverable from git history if needed).
Only `player` (MPD) and `rfid` (reader + card database) survived, rewired onto `jukebox.registry`.
`publishing` and `misc` also survived (framework-adjacent, not really "plugins"). This was a
deliberate "draft without plugins/components" cut, not an oversight -- the removed pieces come
back later as newly designed components, not restored as-is.

This directly supersedes the "merge `future3/draft-entrypoint-plugins` later" framing further up
in this doc: there is no old plugin system left to extend at this point.

## Relationship to the other fork tracks

- **Plugin system**: first slice (backend-swap for player/RFID hardware, config + optional-
  dependency selection) is done, see "Advanced plugin system" above. Deliberately *not* pulling in
  upstream's `future3/draft-entrypoint-plugins` draft (two-tier core/user-plugin loading,
  config-toggled entry points) for anything deeper — the goal there is more powerful plugins than
  that model supports — how deep a plugin can reach into playback, library, and the API layer is a
  question to design once this core architecture work has settled, not before. Revisit step 5
  above (plugin dispatch call sites) with that redesign in mind rather than migrating the old model.
- **Packaging/installer**: mostly orthogonal, but step 6 above (nginx/service file changes) overlaps with
  the "ship resources as package data" work already scoped in
  `documentation/developers/roadmap-plugins-and-packaging.md` (Track B) — sequence so the same install
  routine isn't edited twice for unrelated reasons.
- **Naming**: deferred, no dependency.

## Open decisions

Resolved: ZMQ pub/sub for events (replaced by in-process `EventBus`, see "Simplify away ZMQ and
nginx"), CLI/ZMQ REP (removed entirely, no replacement designed yet, see "ZMQ REP/REQ..." above),
and `jukebox.plugs`'s single global lock (replaced by `jukebox.registry`, which has no lock at
all -- each component is responsible for its own thread-safety, see "Old plugin system removed").

Still open:

- Real per-component/per-resource concurrency (e.g. a library scan not blocking playback controls)
  isn't designed -- `jukebox.registry.call()` has no shared lock anymore, but nothing *adds*
  deliberate concurrency control either; components are just trusted to be thread-safe on their
  own terms today. This is the actual "high performance" work -- the FastAPI swap alone didn't
  achieve it (see step 1 and step 7 further up).
- Does `/api/v1` get replaced in place, or versioned to `/api/v2` at some point? (Currently: no
  need has come up.)
