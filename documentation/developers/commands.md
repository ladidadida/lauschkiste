# Commands

Lauschkiste has two commands (`packages/cli`). In a source checkout run them with `uv run`, e.g.
`uv run lauschctl --help`; each command and sub-command explains itself with `--help`.

## `lauschkiste`: the server

Starts the core, the plugins and the web app. On a box it runs as a user service that starts at boot
(`systemctl --user restart lauschkiste` after a configuration change; not every setting is applied on the fly, see
[Settings and files](../en/maintenance/configuration.md)). For debugging, stop the service and start `lauschkiste` in a console:
the log goes there and `-v`/`-vv` raise the log level ([Troubleshooting](../en/maintenance/troubleshooting.md)).

`--conf FILE` starts it with a different configuration file, `--home DIR` with another home (see `lauschctl home`).

## `lauschctl`: manage the machine

| Command | What it does |
| --- | --- |
| `lauschctl setup [STEP]` | sets up this machine step by step; `--list`, `--check`, `--yes` ([Packaging and setup](packaging-and-setup.md)) |
| `lauschctl update` | installs a newer version and re-applies the setup |
| `lauschctl uninstall` | removes what Lauschkiste created, and itself at the end |
| `lauschctl config get\|set KEY [VALUE]` | reads and changes single settings |
| `lauschctl plugin list\|enable\|disable\|install` | manages plugins |
| `lauschctl home` | prints the home directory and the configuration file in use |
| `lauschctl debug sniff` | prints the events of the running server (see below) |

Setup steps worth knowing: `audio` chooses the audio outputs ([Sound](../en/using/sound.md)), `rfid` configures
the RFID readers and enables their driver plugins ([RFID readers](../en/hardware/readers.md); it writes a new reader
configuration after asking), `hardware` asks for the connected hardware.

## The API

The web app talks to a typed REST API; `/docs` (Swagger UI) on the running server lists it, and
[Core and plugins](core-and-plugins.md) explains where the routes come from. For scripts, use `curl` or any HTTP
client; `GET /api/v1/modules` lists the active modules with their operations and events.

## Debugging events

`lauschctl debug sniff` connects to the WebSocket `/api/v1/events` and prints every event the server publishes
(`player.status`, `rfid.card_detected`, ...). It is a plain client: any WebSocket client can do the same.
