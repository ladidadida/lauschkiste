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
   plugins.audiobookshelf.server_url https://...` and `lauschctl config set
   plugins.audiobookshelf.api_key --secret`). The key is kept in `settings/secrets.yaml` (readable for the
   box's user only, not in the configuration you may share) and is never shown again.
3. The books appear in the Audiobooks tab. On a card the book is `{book: <id>, source: audiobookshelf}`;
   the card dialog offers them like the local ones.

Needs the `local_audio` player. A book that is not downloaded needs the server to play.

### Downloading books

In the Audiobooks tab, the menu of an Audiobookshelf book has **Download to the box**. The files go to
`cache/audiobookshelf/` in the Lauschkiste home (not into the library, so the book stays one entry and keeps
sharing its position with the server). A downloaded book plays from the box even when the server is
reachable (`prefer_downloaded`). Downloading is a function of the core (module `cache`, Settings → Cache):
the download runs in a process of its own with the lowest priority; while something plays it is slowed to
`rate_playing_kbps` (1000 kB/s, `0` waits until the playback stops). `limit_gb` (8) caps the space for all
downloads together; a book that would not fit is refused with the numbers. A stopped download keeps what it
loaded and continues next time. Remove a download in the same menu.

Space: with `remove_old` switched on, the oldest *finished* downloads are removed when a new book
does not fit; books in progress are never removed. If the server changed a book after the download, the
list says so and "Download again" fetches the new version.

### Without the server

The box keeps working when the server is not reachable (portable box, WiFi gone, server off):

- The book list is kept on the box and shows a notice; downloaded books come first and play as usual.
- The position of what you listen to is saved on the box and sent as soon as the server answers again
  (checked every minute). If the book was also listened to elsewhere in the meantime, the furthest position
  wins and a book finished anywhere stays finished. The decision does not use the clock, because a Pi can be
  days off while offline: the box's position wins only if the server's position did not move since the box
  last saw it.
- A book that is not downloaded needs the server to play.
