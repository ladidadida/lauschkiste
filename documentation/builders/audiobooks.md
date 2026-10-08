# Audiobooks

Audiobooks live in `library/audiobooks` (see [Copying music](copying-music.md)), one folder per
audiobook. Its files are the chapters, played in file name order (`2.mp3` before `10.mp3`).

An audiobook continues where it stopped, going back a few seconds so the listener finds back in.
The position is saved while playing, when pausing and when Lauschkiste shuts down. Once the last
chapter has played to the end, the audiobook counts as finished and starts from the beginning the
next time. Chapters always play in order, regardless of shuffle and repeat.

## Cards

```yaml
action: audiobooks.play
args:
  book: Pippi Langstrumpf
```

`book` is the folder name below `library/audiobooks`. Playing the audiobook that is already playing
changes nothing; a paused one continues. With a place-capable reader and `player.pause` as card
removal action, removing the card pauses and placing it again continues.

| Action | Arguments | |
| --- | --- | --- |
| `audiobooks.play` | `book`, `source` | play from the saved position |
| `audiobooks.restart` | `book`, `source` | play from the beginning |
| `audiobooks.set_finished` | `book`, `finished` (default true), `source` | mark as finished or not; both start from the beginning next time |

`source` is `local` (the library, the default) or the id of a plugin that adds audiobooks, see below.

`GET /api/v1/audiobooks` lists all audiobooks with chapter, position and progress.

## Settings

```yaml
audiobooks:
  rewind_sec: 10                          # go back this far when continuing
  state_file: settings/audiobooks.json    # positions
```

## Audiobookshelf

The plugin `audiobookshelf` shows the books of an [Audiobookshelf](https://www.audiobookshelf.org)
server next to the local ones and streams them from the server. The position is kept on the server, so
a book started in the Audiobookshelf app continues on the box and the other way round.

1. In Audiobookshelf create an API key (Settings → API Keys) for the user the box should use.
2. In the web app open Settings → Plugins, switch on `audiobookshelf` and enter the server address and the
   key (or `lauschctl plugin enable audiobookshelf`, then `lauschctl config set
   plugins.audiobookshelf.server_url https://...` and `...api_key`). The key is stored in the
   configuration file, which is then readable for the box's user only, and is never shown again.
3. The books appear in the Audiobooks tab. On a card the book is `{book: <id>, source: audiobookshelf}`;
   the card dialog offers them like the local ones.

Needs the `local_audio` player and a reachable server: a book that is not on the box cannot play without it.
Downloading books for offline use is planned, see [Audiobookshelf](../developers/audiobookshelf.md).
