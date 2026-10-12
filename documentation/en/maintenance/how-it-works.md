# How it works

A short tour, so that settings and messages make sense.

## The parts on the box

1. **The Lauschkiste service** plays the music, knows the cards and the library, controls volume and time limits and
   serves the web page. It runs as a *user service* with the name `lauschkiste`, because it has to talk to the sound
   system of your login session.
2. **The sound system (PipeWire)** is part of current Raspberry Pi OS. It makes many kinds of sound hardware work the
   same way and lets Lauschkiste switch between outputs (speaker, Bluetooth).
3. **The web page** is served by Lauschkiste itself, no extra web server. Open `http://<name>` (port 80) or
   `http://<name>:5556`.
4. **The commands** `lauschkiste` (the server) and `lauschctl` (setup and management).

## Core and plugins

The **core** is everything that makes sense on every machine: the player, the library, cards and the reader handling,
volume, timers, time limits and the web page. It is always there. It works on any Linux computer, not only on a
Raspberry Pi.

**Plugins** add what depends on hardware or on other services: Raspberry Pi board support, buttons, battery, RFID
reader drivers, Samba, the Audiobookshelf connection, podcast and radio directories. A plugin only runs when it is
switched on (Settings → Plugins). If one fails to start, Lauschkiste keeps running; the web page and
`lauschctl plugin list` say why.

## Actions

Everything the box can do is an **action** with a name like `player.toggle` or `volume.change_volume`. Cards, buttons,
timers, the web page and the second swipe all trigger actions; the web page shows which exist, and they are listed at
`http://<name>/api/v1/actions`. This is why a button can do what a card does.

## Events

The box announces what happens as events (`player.status`, a card was read, ...). The web page listens to them, which is
why it updates by itself. For your own tools, `lauschctl debug sniff` prints them.

## Where to read on

[Developer documentation](../../developers/README.md) (English) explains the code, the plugin interface and the REST
interface.
