# Audiobookshelf

The plugin `audiobookshelf` (package `lauschkiste-plugin-audiobookshelf`) shows the books of an
[Audiobookshelf](https://www.audiobookshelf.org) (ABS) server in the Audiobooks tab next to the local ones and
shares the listening position with the ABS apps: a book started on the phone continues on the box and the other way
round. Setup and use for builders: [Audiobooks](../builders/audiobooks.md#audiobookshelf).

Not supported: chapters inside one file (an m4b book is one chapter for next/previous), a "test connection" button,
several servers, ABS podcasts.

## How it fits in

- It registers at `audiobooks.sources` (id `audiobookshelf`; the built-in folders are the source `local`), at
  `player.resolvers` (scheme `abs:`) and at `cache.providers` ([Caching](caching.md)).
- `audiobooks.play`, `restart` and `set_finished` take an optional `source`; cards of ABS books store
  `{book: <id>, source: audiobookshelf}`. Without `source`, `local` is meant.
- Tracks use the internal scheme `abs:<book>/<track>`. The resolver turns them into the server URL plus the
  `Authorization` header when the player opens them, so the key never appears in queues, status, the position
  file or logs. Only the `local_audio` backend uses resolvers, so ABS books need it.
- The `ResumeTracker` delegates the position of a source with its own progress: on start it asks the source, and it
  reports to it instead of writing `settings/audiobooks.json`. The tracker's logic (rewind, finished near the end,
  release when something else plays) is shared with local books.

## Server interface

Authentication is `Authorization: Bearer <API key>` (API keys need ABS 2.26 or newer; create one under Settings → API
Keys for the user the box should use). The plugin uses:

| Call | For |
| --- | --- |
| `GET /api/libraries`, `GET /api/libraries/<id>/items` | the book list (all book libraries of the user) |
| `GET /api/items/<id>` | files, duration and metadata of a book |
| `GET /api/me`, `GET /api/me/progress/<id>` | the position (always read fresh) |
| `PATCH /api/me/progress/<id>` | write position, duration and finished state; the server answers the plain text `OK`, not JSON |
| `GET /s/item/<id>/<file>` | the audio files (range requests), also used for downloads |
| cover of an item | proxied through `/api/v1/audiobookshelf/covers/<id>` (the key must not reach the browser) |

Audio is played directly from the original files; ABS does not transcode here.

## Settings

| Setting | Meaning |
| --- | --- |
| `server_url` | `https://abs.example.org` or `http://nas:13378` |
| `api_key` | secret: kept in `settings/secrets.yaml` (mode 0600), shown as a password field, never sent back |
| `refresh_minutes` | how often the book list is fetched again (default 10); the position is always read fresh |
| `prefer_downloaded` | play the downloaded copy even when the server is reachable (default on) |

## Position and the ledger

The position in the book is the start offset of the playing track plus the elapsed time of the track. The server
wins at the start (a book finished elsewhere starts from the beginning); while playing, the position is written
through the tracker's save interval, on pause, on stop, when something else starts and on shutdown.

Positions that could not be sent are kept in a ledger on the box (`pending`) and sent as soon as the server answers
again, checked every minute. The merge rule does not use the clock, because a Pi can be days off while offline:

- the box's position wins only if the server's position did not move since the box last saw it;
- otherwise the furthest position wins;
- a book finished anywhere stays finished.

A circuit breaker stops asking an unreachable server for a while, so the player does not stall on every request. The
book list is kept on disk, so the box starts without the server and shows a notice; downloaded books come first.

## Offline use

Downloads are done by the `cache` core module ([Caching](caching.md)); this plugin only provides the plan (which
files, with which headers) and the version of a book (changes when the server's copy changes, so the list can offer
"Download again"). Finished books may be removed to make room, books in progress never. A complete download plays as
plain local files through the normal player, so it works with every backend and without the network.

## Handover to other players

[Music Assistant](https://www.music-assistant.io) syncs the position with ABS too. When the box and Music Assistant use
the same ABS user, a book heard on the box continues at the same place on other speakers and vice versa; Lauschkiste
does not need to know about it. The box is meant to work without a server, so the position in ABS is the shared state.
Make sure the same ABS user is used, because progress is per user.

## Open points

- Chapters inside one file (m4b): the source would deliver the chapters with the tracks and the audiobooks module
  would offer next/previous chapter by seeking.
- A "test connection" button in the settings form.
- ABS podcasts through a `podcasts` source, automatic downloads, series and collections.
- m4b over HTTP on a Pi Zero decodes slower than mp3; downloading the book to the box avoids the network part.
