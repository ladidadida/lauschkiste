# Jukebox Apps

The Jukebox core and its developer tools are exposed through the `jukebox` CLI (`packages/cli`).
To learn more about each command and its parameters, run:

``` bash
$ uv run jukebox <command> --help
```

RFID/audio setup tools are not part of the CLI yet -- see "Configuration Tools" below.

## Jukebox Core

**Command:** `jukebox run` (run via `uv run jukebox run`)

This is the main app. It starts the Jukebox Core.

This runs as a service, which starts automatically after boot-up. At times, it may be necessary to restart the service, for example, after a configuration change. Not all configuration changes can be applied on-the-fly. See [Jukebox Configuration](../builders/configuration.md#jukebox-configuration).

For debugging, it's best to run Jukebox directly from the console rather than as a service, as this provides direct logging information in the console and allows for changing command line parameters. See [Troubleshooting](../builders/troubleshooting.md).

The player backend is selected via `player.backend` in the Jukebox configuration (default:
`local_audio`, no extra install needed). `mpd` and the RFID reader drivers are plugins: enable
them under `plugins:` (e.g. `mpd: {}`, `rfid_generic_usb: {}`), or with
`jukebox plugin enable <name> --with-extras`, which also installs a driver's extra dependencies.

## Configuration Tools

Before running the configuration tools, stop the Jukebox Core service.
See [Best practice procedure](../builders/configuration.md#best-practice-procedure).

### Audio

**Command:** `jukebox setup audio` (`packages/cli/src/lauschkiste_cli/setup/steps/extras.py`)

Selects the primary and secondary audio sinks used by the Jukebox (`volume.outputs`).

Run this once after installation. It can be re-run at any time to change the
selected outputs. For more information see
[Audio Configuration](../builders/audio.md).

### RFID Reader

**Command:** `jukebox setup rfid` (uses `lauschkiste_plugin_rfid_readers.configure`)

Configures the RFID readers and enables their driver plugins.

Run this once to register and configure the RFID readers with Jukebox. It can be re-run at any time to change the settings. For more information see [RFID Readers](./rfid/README.md).

> [!NOTE]
> This tool will always create a new configuration file, thereby overwriting the old one (after confirming with the user). Any manual modifications to the settings will need to be reapplied.

## Developer Tools

### API

Most of the player/settings/cards surface is now typed, documented REST -- see `/docs` (Swagger
UI) on the running daemon for the full, current list. `GET /api/v1/player/status`,
`POST /api/v1/player/play`, `PUT /api/v1/player/volume`, etc. -- see `lauschkiste.api.fastapi_server`
and `documentation/developers/roadmap-core-architecture.md`, "Advanced plugin system" for how this
came together.

There is no dedicated CLI tool for this yet (both previous RPC CLIs were removed -- the
interactive Python tool (`run_rpc_tool.py` / `tools/run_rpc_tool.sh`) and the C client
(`src/cli_client/pbc.c`), along with the ZeroMQ REP server they talked to
(`jukebox.rpc.server.RpcServer`)) -- for now, use `curl` or any HTTP client against the REST
endpoints above. The generic `POST /api/v1/rpc` endpoint was removed as well.

### Publicity Sniffer

**Command:** `jukebox debug sniff` (run via `uv run jukebox debug sniff`)

This command-line tool monitors all messages sent from Jukebox through the publishing interface, printing received messages in the console. It is primarily used for debugging.
