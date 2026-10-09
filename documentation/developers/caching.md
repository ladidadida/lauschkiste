# Caching content on the box

Status: steps 1 to 3 are implemented (the `cache` core module, the Audiobookshelf plugin and the podcast
episodes as providers, `availability` on audiobooks and episodes); music and radio are still open. The download cache of the Audiobookshelf plugin
([Audiobookshelf](audiobookshelf.md), "Offline use") became a core module so that other plugins (podcasts,
Music Assistant, further sources) get it for free.

## Why in the core

Everything a download needs has nothing to do with the source: a worker that runs at the lowest priority,
resumes interrupted files, slows down while something plays, keeps a space limit, removes old files and
shows progress. Only two things are specific to a source: **which files make up an item** (and how to
authenticate) and **what happens to the position** when the server is away. The first is a small plugin
interface; the second stays in the plugin (or the module that owns the position).

## The `cache` core module

`cache` is a core module (always running, no setting to switch it on). It owns the folder
`cache/<source>/<item>/` of the home, the worker and the settings:

| Setting | Meaning |
| --- | --- |
| `limit_gb` | space all downloads may use together (default 8, never more than the free space minus a reserve) |
| `rate_playing_kbps` | download speed while something plays (default 1000, `0` waits) |
| `remove_old` | make room by removing the oldest items the source allows removing (default off) |

Operations (card actions and REST like every other module): `cache.download(source, item)`,
`cache.cancel(source, item)`, `cache.remove(source, item)`, query `cache.downloads()` (state, progress,
bytes, "changed on the server", total and free space).

For modules and plugins in the same process: `cache.files(source, item)` returns the complete local files
of an item (paths, durations) or nothing; a plugin uses it to play from the box when it can.

## The plugin side: `cache.providers`

A plugin that can provide content for download registers a provider at the extension point
`cache.providers` under its source id (the same id it uses at `audiobooks.sources` or
`library.sources`). That registration is the property "can be cached"; nothing else is declared.

```python
class CacheProvider(Protocol):
    def plan(self, item: str) -> CachePlan: ...        # files to fetch
    def version(self, item: str) -> Optional[str]: ... # changes when the server's copy changes
    def removable(self, item: str) -> bool: ...        # may it be removed to make room (e.g. finished)?

class CachePlan(BaseModel):
    title: str
    version: Optional[str]
    files: List[CacheFile]    # name, url, size, duration (optional), headers (for authentication)
```

The core fetches `plan()` once per download, writes it to a private file (mode 0600, removed when the
worker is done, so credentials appear neither on the command line nor in the environment) and starts the
worker process with it. The worker is the generalised `downloader` of the Audiobookshelf plugin.

Everything the plugin knew about files (names, `meta.json`, completeness check, range requests, size check)
moves into the core. What stays in the plugin: building the plan from its API, the position (including the
offline ledger of Audiobookshelf) and the decision whether to prefer the local copy.

## Showing where content comes from

Items in the library views carry two facts, filled in by the module that lists them:

- `source`: id and label of where the item lives (`local`, `audiobookshelf`, `mpd`, a podcast feed, ...).
- `availability`: `local` (a file of the library), `cached` (downloaded from a source) or `stream`
  (played over the network).

`availability` for cacheable sources comes from `cache.files()`, so no list has to merge states itself.
The web app shows both in one muted line under the title and offers filter chips per source (the music
views already do). Radio stations are always `stream`; podcast episodes are `stream` until they are cached.

## Who uses it

| Content | Item | Provider |
| --- | --- | --- |
| Audiobookshelf books | a book (all its files) | the Audiobookshelf plugin |
| Podcast episodes | an episode (the enclosure) | the `podcasts` module itself; episodes then play offline |
| Music Assistant or other music sources | an album or track | later, by their plugins |

The web app has one component for the download button and its state, used by every list.

## Steps

1. **Core module and worker** (done), with tests; the Audiobookshelf plugin is a provider and its download
   code is gone. Decisions: one global limit; automatic removal only of what the provider marks removable
   (finished books, later heard episodes), never an item in progress; the offline ledger of positions stays in
   the plugin. The name `cache` and the wording in the web app are still open (a symbol may be better than a word).
2. **`source` and `availability`** (done for audiobooks and podcast episodes): the lists show where an item
   comes from and whether it is streamed or on the box, with filter chips per source for audiobooks. Radio
   stations show their address; music has the source chips but no line per album yet.
3. **Podcast episodes** as the second provider (done): the item id is `<podcast>~<episode>`, the files are the
   enclosure (its listed size is ignored, the worker takes the length it downloaded). An episode plays from
   the box when it is there and continues at the position of the stream, because the position is kept under
   the episode's address, not the file that plays. The "heard" ones may be removed to make room.
4. Later: per-source limits, "keep" flags, automatic downloads (for example the next books of a series while
   on WiFi).

## Open points

- A global limit is simple; a limit per source may be wanted once several plugins fill the cache.
- `removable()` decides what automatic removal may touch. For books it is "finished", for podcast episodes
  "heard"; items in progress must never be removed.
- Positions while offline are not generalised: only Audiobookshelf has a server-side position. If another
  source gets one, the ledger moves from the plugin into the core `ResumeTracker`.
