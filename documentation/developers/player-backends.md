# Player Backends

The `player` core module plays through a **backend**. `local_audio` is built in (PyAV decoding, PortAudio
output); the `mpd` plugin adds an MPD server as a second one. A further backend is a plugin that registers at the
extension point `player.backends`.

## Register a backend

```python
def start(self, ctx):
    ctx.modules.player.backends.register('streaming', StreamingBackend())
```

The name is a stable, lowercase identifier. The setting `player.backend` selects the backend that is active at
start and is the default one: folder playback, local files and library updates go to the default backend; transport
controls (pause, next, seek, volume) go to the active one. Switching stops the previous backend first
(`GET /api/v1/player/backends` lists them).

## The backend protocol

`lauschkiste.player.backend.PlayerBackend` lists what a backend implements: transport (`play`, `pause`, `stop`,
`next`, `prev`, `seek`, `toggle`, `shuffle`, `repeat`, `jump`, `stop_after_current`), content (`play_single`,
`play_folder`, `play_files`), the second swipe (`is_second_swipe`, `play_second_swipe`), `playerstatus`,
`playlistinfo`, `get_volume`/`set_volume` and `exit`.

- `set_status_callback(callback)` receives the raw status mapping whenever it changes. The coordinator forwards it
  only while the backend is active (`set_active(active)` is called on every change), so a polling backend can stop
  polling while inactive. The player module turns the raw status into the typed `player.status` event.
- `play_files(paths, start, position, ordered)` replaces the queue and plays from `position` seconds into entry
  `start`. Audiobooks, podcasts and radio use it, so they work with every backend that implements it.
- Optional capabilities are looked up by name when needed: a backend without them makes the operation answer 501.
  Examples: `set_resolver(resolve)` (receives the function that resolves track URLs, see below),
  `set_level_callback(callback)` (reports the output level for level meters; only `local_audio` measures it).

## Related extension points

- `player.level_meters`: a device plugin (for example `phat_beat`) registers `level(left, right, delay)` and gets
  the RMS level of each channel about ten times a second.
- `player.resolvers`: a plugin registers a `resolve(url) -> (url, headers)` for a URL scheme (for example `abs:`),
  so that tracks of authenticated sources carry no credentials in queues, status or logs. Only `local_audio`
  uses resolvers.

## Library sources

A catalog (an MPD database, a streaming service) is added to the library at `library.sources`, not through the
player. A source implements `lauschkiste.library.module.LibrarySource`:

- `describe()` returns `{'id', 'label', 'views': [{'id', 'label', 'kind', 'content_types'}]}`; `kind: items` is a
  catalog list rendered with the shared album and track views.
- `list_items(content_types)` returns entries with `albumartist`, `album`, `content_type`, `content_uri` and
  optionally `cover_url`; `list_songs`, `get_song`, `cover(song_url)` and `refresh()` complete it.

`content_uri` must stay stable, because playback and card assignments keep it. Cards for such items store the
source (`provider`) next to the URI. An overview combines all sources and isolates the failure of an optional one;
a request for one explicit source returns that source's error. The built-in local source has the id `local`.
