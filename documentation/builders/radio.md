# Radio

Radio stations are internet streams with a name and optionally a logo. They are kept in
`settings/radio.yaml` and managed through the web app or the API; each card plays one station.

A station URL can be the stream itself or an `.m3u`/`.pls` playlist from the station's website;
playlists are resolved to their first stream when the station is played. While a station plays,
the player status shows the station name and, where the station sends it, the current title.
A stream that drops out is reconnected automatically.

## Cards

```yaml
action: radio.play
args:
  station: deutschlandfunk
```

`station` is the station id, derived from its name when the station is added (shown in the list of
stations).

## API

| Request | Body | |
| --- | --- | --- |
| `GET /api/v1/radio/stations` | | all stations |
| `POST /api/v1/radio/stations` | `name`, `url`, `logo` (optional) | add a station |
| `PUT /api/v1/radio/stations/<id>` | `name`, `url`, `logo` (each optional; empty `logo` removes it) | change a station |
| `DELETE /api/v1/radio/stations/<id>` | | delete a station |
| `POST /api/v1/radio/play` | `station` | play a station |

## Stations file

```yaml
stations:
  deutschlandfunk:
    name: Deutschlandfunk
    url: https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3
```

## Find stations

With the plugin `radio_directories` (Settings → Plugins, or `lauschctl plugin enable radio_directories`) the
button "Add station" opens a search in [radio-browser.info](https://www.radio-browser.info), an open directory of
internet radio stations (no sign-in). Type a name, or a topic such as "kinder": stations whose name or tags
match are listed, with logo, country, codec and bitrate. Without a search term the popular stations of your
country are shown. One tap adds a station; stations you already have show a check mark.

The country for the popular stations and the switch for the directory are in the settings of the plugin. What
you type is sent to radio-browser.info. "Add by address" in the menu is still there for any stream address.

### Station lists (M3U and PLS)

The menu next to the button imports an `.m3u` or `.pls` file, the list format radio apps and players use, and
exports your stations as an `.m3u` file. Imported stations are named from the file; addresses you already have
are skipped.

## Now playing and the "Continue" list

The player shows the station's logo as the picture, its name, and what the stream says about itself: the
current title (artist and song, as far as the station sends it, and it changes while you listen) and the genre or
description the station announces. Stations that send nothing show just their name.

Stations you played last are listed under "Continue" (Library → Continue, "Recently played stations"). The menu of
an entry has **Remove from "Continue"**; the station itself stays. The same works for audiobooks and podcasts there:
an audiobook comes back when you listen on, a podcast when a new episode arrives or you hear one.
