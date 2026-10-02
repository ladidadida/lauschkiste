# Content types

Status: implemented (core modules and web app views).

Lauschkiste plays more than albums. Audiobooks, podcasts and radio behave differently and should be
handled as separate content types, each with its own place in the library, its own playback rules
and its own view in the web app.

## Today

- All audio lives in one folder, `audiofolders` in the Lauschkiste home.
- A folder is played from its first track; `local_audio` keeps no position per folder. The `mpd`
  backend still has an old per-folder resume store (`music_player_status.json`) that the web app
  doesn't use.
- Shuffle and repeat are global player settings.
- Streams and podcasts are special files inside music folders (`*livestream.txt`, `*podcast.txt`,
  `*.m3u`), expanded by `playlistgenerator` when the folder is played. The library index and the
  web app don't know about them.
- The library index (`songs` table) knows files, folders and tags; the web app shows albums and
  folders.

## Content types

| Type | Source | Position | Shuffle/repeat | Unit on a card |
| --- | --- | --- | --- | --- |
| Music | audio files | starts from the beginning | allowed | album / folder |
| Audiobook | audio files | resumed per audiobook | off | audiobook |
| Podcast | feed URL | resumed per episode | off | podcast (newest unheard episode) or episode |
| Radio | stream URL | none (live) | n/a | station |

### Music

Unchanged behaviour: folder or album, shuffle and repeat as set by the user.

### Audiobooks

- One folder per audiobook; tracks in file name order (chapters).
- Position (track and seconds) is stored per audiobook: periodically while playing, on pause,
  stop, switching to something else, and shutdown. Playing the audiobook again continues there.
- On resume, go back a few seconds (configurable, e.g. 10 s) so the listener finds back in.
- Shuffle and repeat are ignored while an audiobook plays; the global settings are restored after.
- Actions: start over, previous/next chapter, mark as finished. A finished audiobook starts from the
  beginning next time.
- The web app shows progress per audiobook.

### Podcasts

- A podcast is a feed URL with a name; episodes are fetched from the feed.
- Position per episode, like audiobooks; an episode counts as heard near its end.
- A card plays the newest unheard episode, or a fixed episode.
- Streaming vs. downloading episodes (offline use, SD card space) is open.

### Radio

- A station is a name, a stream URL and optionally a logo.
- No position, no shuffle; "next/previous" may switch stations within a list.
- A card plays a station.

## Library layout

The music folder gets a new name and one subfolder per file-based type:

```text
<home>/library/
  music/
  audiobooks/
```

Podcasts and radio stations are not folders of audio files; they are stored as entries (name, URL,
settings) in the settings, editable in the web app. The old `*livestream.txt`/`*podcast.txt` files
inside music folders are dropped.

## Cards

A card refers to an item of a type, e.g. `player.play_folder` for music, `audiobooks.play` with the
audiobook folder, `podcasts.play` with the podcast id, `radio.play` with the station id. The
web app's card dialog picks the type first, then the item.

## Web app

The library is organised by content type, not by source. Its tabs are:

- **Continue**: audiobooks in progress and podcasts with unheard episodes.
- **Music**: albums of all sources in one list (filter chips per source once there is more than
  one), and a folder view of `library/music` with upload and file management.
- **Audiobooks**: the audiobooks with progress, and a folder view of `library/audiobooks`.
- **Radio** and **Podcasts**: stations and subscribed feeds.

There is no tab per source. Setting up a source (account, server address) belongs to the settings,
later to the plugin settings in the web app.

## Sources from plugins

A plugin can add content to one or more types, e.g. MPD (music, radio), Spotify (music, podcasts),
Music Assistant (music, radio, podcasts), Audiobookshelf (audiobooks, podcasts). Each type has an
extension point for its sources, like `library.sources` for music today:

- `audiobooks.sources`, `radio.sources`, `podcasts.sources`: list items, play an item, and
  optionally keep the position themselves (Audiobookshelf has its own progress; then Lauschkiste
  uses it instead of its own).
- Items and card actions carry the source (`source` argument, like `provider` for albums); without
  it the built-in source is meant.

The extension points are added with the first plugin that needs them.

## Decisions

- The library is `library/` in the Lauschkiste home with `music/` and `audiobooks/` below. It
  replaces `audiofolders`; the setting moves from `player.music_library_path` to `library.path`.
- The type of a file-based item follows from the folder it is in; folders are not marked.
- One position per audiobook, regardless of the card that starts it.
- Each type is a core module (`audiobooks`, `podcasts`, `radio`) that uses the player through the
  backend interface (`play_files`, `seek`, status), so it works with every backend supporting it.
- Radio: one station per card.
- Podcasts: streamed, no downloads for now.
- Order: library layout, audiobooks, radio, podcasts; the web app follows each step.
