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
