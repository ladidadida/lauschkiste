# Concepts

Lauschkiste is based on three concepts. A rough understanding helps to read the configuration
files.

## Core and plugins

The **core** is everything that makes sense on every machine Lauschkiste runs on: the player, the
music library, the card database and RFID reader handling, volume, timers and system information.
It is always there.

**Plugins** add platform-specific functionality (e.g. Raspberry Pi hardware: shutdown, GPIO
buttons, battery HATs), other player backends such as `mpd`, RFID reader drivers, or integrations
such as MQTT. A plugin only runs when it is listed under `plugins:` in `lauschkiste.yaml`, even if it is
installed. If a plugin fails to start, the rest of Lauschkiste keeps running; check the logs (see
[Troubleshooting](troubleshooting.md)) or `GET /api/v1/modules`, which also lists skipped plugins
with the reason.

## Actions

Core modules and plugins offer *actions*, e.g. `player.play_folder` or `player.toggle`. The web app
calls them through the REST API, and cards, the card removal of place-capable readers and the
second swipe trigger them too. How to configure them is described in [Actions](actions.md).

## Events

The core and plugins publish their status as typed events, e.g. `player.status` or
`rfid.card_detected`. The web app receives them over the WebSocket `/api/v1/events`; so can your
own application. `lauschctl debug sniff` prints them (see
[Core apps](../developers/coreapps.md#publicity-sniffer)).
