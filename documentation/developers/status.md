# Feature status

Where Lauschkiste stands (alpha). Plans have their own documents; the history of the architecture is in
the [roadmap](roadmap-core-architecture.md).

## Works

| Area | What |
| --- | --- |
| Playback | built-in player (`local_audio`, PyAV and PortAudio), MPD as a plugin; shuffle, repeat, sleep timer, playback speed for audiobooks and podcasts, queue |
| Content | music, audiobooks (position per book), podcasts (feeds, position per episode), radio stations; see [Content types](content-types.md) |
| Sources | audiobooks from an [Audiobookshelf](audiobookshelf.md) server (streaming, shared position, offline use), podcast and radio directories (Apple Podcasts, fyyd, Podcast Index, radio-browser.info), OPML and M3U/PLS import and export |
| Downloads | a [cache in the core](caching.md) for audiobooks and podcast episodes: low priority, space limit, removal of old items |
| Time limits | quiet hours and a daily listening time with extra time for parents (core module, off by default; [Time limits](../builders/time-limits.md)) |
| Library | one folder with `music/` and `audiobooks/`, index with tags and cover art, folder watching, upload and file management in the web app, optional Samba share |
| Cards | RFID cards with actions (play, volume, timers, shutdown, ...), learning mode, second swipe, card database in the web app |
| Readers | RC522 (SPI), MFRC522 and PN532 (I²C), USB readers, RDM6300, NFC (nfcpy) as plugins |
| Hardware | board support for the Raspberry Pi, GPIO buttons and rotary encoders, status LED, battery monitor (MAX17048, INA219), power button (OnOff SHIM), Pimoroni pHAT BEAT with LED level meter, I²S sound cards; see [Hardware](hardware.md) |
| Volume and timers | volume with soft maximum and outputs, fade-out, named timers (stop, fade, shutdown), startup and shutdown sound |
| Input | evdev devices (USB buttons, media keys, Bluetooth headset buttons) |
| Web app | player, library, cards, settings of all modules and plugins, plugin management, hardware and pin overview, help, German and English |
| API | REST and WebSocket, typed operations and events generated from the modules ([Core and plugins](core-and-plugins.md)) |
| Installation | install script, `lauschctl setup` steps (re-runnable), updates, plugins from the command line, port 80, WiFi hotspot, kiosk mode; packages for PyPI ([Releasing](releasing.md)) |

## Planned

- Playing from a phone over Bluetooth, for apps that cannot be integrated, such as the Onleihe
  ([plan](phone-audio.md)).
- A handover to other rooms through Music Assistant (needs the same Audiobookshelf user; see the
  [Audiobookshelf plan](audiobookshelf.md)), m4b audiobooks with chapters in one file.
- Release on PyPI ([Releasing](releasing.md)).
- Installing straight from a git branch or tag without a release (the web app would have to be built on the
  box or taken from a CI build).
- A switch for Bluetooth on the Raspberry Pi, more board support plugins, general LED strip control.
- An MQTT plugin (the [old documentation](../builders/components/mqtt/mqtt-integration.md) still describes
  the earlier implementation).

## Not carried over from Phoniebox 2.x and the first future3 versions

Spotify, the idle shutdown timer, the old GPIO configuration file format, the C command line client and
ZeroMQ. Some may come back as plugins.
