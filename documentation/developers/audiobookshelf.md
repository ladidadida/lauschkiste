# Audiobookshelf

Status: plan, nothing implemented yet.

[Audiobookshelf](https://www.audiobookshelf.org) (ABS) is a self-hosted server for audiobooks and
podcasts with its own library, metadata, covers, per-user progress and apps. The goal: a Lauschkiste
box plays the books of an ABS server like its own, and the position is shared with the ABS apps, so
a book started on the phone continues on the radio and vice versa.

It is the first plugin that adds content to a content type (see [Content types](content-types.md),
"Sources from plugins"); the Music Assistant plugin will reuse what is built here (secret settings,
authenticated streams).

## Goals and non-goals

Goals:

- Books of one ABS server show up in the **Audiobooks** tab next to the local ones, with cover,
  progress and "continue".
- Playback streams from the server, nothing is copied to the box.
- Progress is shared with ABS (the server is the source of truth).
- Cards can start an ABS book, like a local one.
- Setup is done in the web app: server address, API key, libraries.
- Later, the same for ABS podcasts.

Non-goals (for now): downloading books for offline use, managing the ABS library (upload, metadata),
ABS series and collections as their own views, multiple ABS servers, the ABS listening statistics.

## What ABS offers

Read in the [API documentation](https://api.audiobookshelf.org):

- Authentication: `Authorization: Bearer <token>`; `?token=` works for GET requests. Since ABS 2.26
  there are **API keys** (Settings → Users → API Keys, bound to a user, optional expiry, shown once).
  `POST /login` with user name and password returns a user token instead.
- `GET /api/libraries`, `GET /api/libraries/:id/items` (paged, `minified`, filter, sort),
  `GET /api/libraries/:id/search?q=`.
- `GET /api/items/:id`: audio files, `chapters[]` (`start`, `end`, `title`), duration, metadata.
- `GET /api/items/:id/cover`.
- `POST /api/items/:id/play`: a playback session with `audioTracks[]` (`startOffset`, `duration`,
  `contentUrl` such as `/s/item/<id>/<file>`), `chapters[]`, `currentTime`. For podcasts
  `POST /api/items/:id/play/:episodeId`.
- Audio files are served by `GET /s/item/<id>/<file>`.

To be verified against a real server in phase 0 (from memory, the part of the documentation read did
not cover them): progress writes (`PATCH /api/me/progress/:id` with `currentTime`, `duration`,
`progress`, `isFinished`), session sync/close, `GET /api/me/items-in-progress`, the fields of a
minified item list, resizing covers (`?width=`), range requests on `/s/item/...`.

## Where it fits

Lauschkiste already has the pieces:

- `audiobooks` plays an ordered list of files through the player and tracks the position with the
  `ResumeTracker` (file and seconds, taken from `player.status`).
- `library.sources` shows that a plugin can add content; `content-types.md` plans
  `audiobooks.sources` for exactly this.
- `local_audio` plays URLs (reconnecting) and seeks; `play_files(files, start, position, ordered,
  context)` accepts them.
- Settings models give the plugin a form in the web app, including dynamic option lists and action
  buttons.

What is missing is described in the next sections.

## Design

### Plugin

A bundled plugin `audiobookshelf` (package `lauschkiste-plugin-audiobookshelf`, only `requests`,
which the core already needs). It talks to the server with one `requests.Session` and registers at
`audiobooks.sources`. It needs no board or hardware.

### Core: `audiobooks.sources`

An `AudiobookSource` protocol; the built-in folders become the source `local`.

```python
class AudiobookSource(Protocol):
    def describe(self) -> dict: ...                 # id, label
    def list_books(self) -> List[dict]: ...          # id, title, author, cover, duration, progress
    def tracks(self, book: str) -> List[Track]: ...  # what to play: url, start offset in the book, duration, title
    def progress(self, book: str) -> Optional[Progress]: ...
    def save_progress(self, book: str, position: float, duration: float, finished: bool) -> None: ...
    def set_finished(self, book: str, finished: bool) -> None: ...
    def refresh(self) -> None: ...
```

- `Audiobook` gets a `source` field (default `local`); `list_books` merges all sources, one source
  failing (server down) leaves the others and says so in the result.
- `audiobooks.play`, `restart` and `set_finished` get an optional `source` argument; cards carry it
  (`{book, source}`). Without it, `local` is meant, so existing cards keep working.
- The `ResumeTracker` learns to **delegate** the position: for a source with its own progress it asks
  the source on start and reports to it, instead of using `settings/audiobooks.json`. Both stay
  behind one small interface (`store`), so the tracker's logic (rewind, finished near the end,
  release when something else plays) is shared.

### Playback without secrets in URLs

The token must not end up in `player.status`, the position file or logs, and `local_audio` needs it
for every request. So the plugin does not hand out URLs with `?token=`:

- Tracks use an internal scheme, `abs:<book>/<track index>`.
- New extension point `player.resolvers` (`resolve(url) -> Resolved(url, headers)`); `local_audio`
  asks it before `av.open` and passes the headers as ffmpeg's `headers` option. Other backends
  ignore the scheme, so ABS books need `local_audio` (documented).
- Direct play of the original files: our decoder handles mp3, m4a/m4b, opus, flac; ABS never
  transcodes.

This extension point is also what Music Assistant and other authenticated streams need.

### Progress

- Position in the book = `startOffset` of the playing track + `elapsed` of the track (a book can be
  many files or one m4b with chapters).
- **Start:** read the server's `currentTime`, map it to (track, offset), go back by `rewind_sec`,
  play. The server wins; a book finished on the phone starts from the beginning.
- **While playing:** write to ABS every `sync_interval_sec` (default 15), on pause, stop, switching
  to something else and shutdown. The last write wins on the server; the radio never edits a
  position backwards without a reason, only forward-played time is written.
- **Finished:** `isFinished` when the last track ends or the book plays to the end, as in the
  local tracker.
- **Server unreachable:** writes are retried, only the newest position is kept; playback of the
  current track continues from the network buffer, a new book cannot start (clear error in the web
  app instead of silence).
- Start with the stateless progress endpoint. ABS "playback sessions" (listening statistics in the
  ABS UI) can be added later without changing the design.

### Chapters inside one file

Many ABS books are a single m4b with chapters. Lauschkiste treats files as chapters, so **next /
previous chapter** would skip the whole book. Plan: the source delivers `chapters[]` with the
tracks, `PlaybackContext` carries them to the status, `audiobooks` offers `next_chapter` /
`previous_chapter` (seek to the neighbouring chapter start; across files when needed) and the
player shows the chapter title. Cards and the second-swipe action can use them. This is also useful
for local m4b files.

### Covers

ABS covers need the token. The plugin serves `/api/v1/audiobookshelf/covers/<id>` itself, fetches a
reduced size from ABS once (a Zero has little RAM and CPU for large images) and keeps it in the
cover cache.

### Settings

A settings model (`audiobookshelf` section, or a file of its own, `settings_storage()`):

| Setting | Meaning |
| --- | --- |
| `server_url` | `https://abs.example.org` or `http://nas:13378` |
| `api_key` | secret; or `username` and `password` for older servers |
| `libraries` | which ABS libraries to show (dynamic list from the server) |
| `verify_tls` | off for self-signed certificates |
| `refresh_minutes` | how often the book list is fetched again (default 10), plus a "refresh" button |
| `sync_interval_sec` | progress write interval (default 15) |

- **Secrets:** the settings system has no secret fields yet. Add them: the form shows a password
  field, `GET` never returns the value (only whether one is set), an empty value on save keeps the
  old one. The file holding them is written with mode 0600. (The samba password has its own form
  today; this unifies it.)
- A **"Test connection"** action button in the form (the `action` widget exists): checks address,
  key and libraries, and says what is wrong in plain words.
- The plugin is set up in Settings → Plugins like the others; `lauschctl` is not needed.

### Web app

- **Audiobooks** tab: one list; a filter chip per source once there is more than one; ABS books show
  author and the progress bar like local ones. Opening a book offers play / start over / mark as
  finished, as today.
- **Continue** tab includes ABS books in progress (from the server's data, so books started on the
  phone show up).
- Card dialog: the audiobook picker lists all sources and stores `source`.
- Player: "put on card" and "title → library" already work through `PlaybackContext.action/args`,
  they only need the `source` argument.
- Help pages (de/en) for the setup, with the API key steps.

### Cards

A card stores the ABS item id and the title. An item id changes when the book is removed and added
again on the server; then the card shows "not found" with the title instead of failing silently.
(The re-link could be offered in the web app later.)

### Podcasts

ABS podcasts follow in a second step with `podcasts.sources` (the same pieces: list, play an
episode, progress per episode via `play/:episodeId`). The Lauschkiste podcast module keeps its own
feeds; the ABS ones appear next to them.

## Phases

| Phase | Content | Result |
| --- | --- | --- |
| 0 | Spike against a real ABS (Docker with sample books): verify the API calls listed above; stream an mp3 book and an m4b over http(s) with `av` on the Pi Zero (start time, seek, CPU, RAM, TLS cost) | go/no-go; notes in this document |
| 1 | Core groundwork: secret settings, `player.resolvers`, `audiobooks.sources`, delegated progress in the `ResumeTracker`; tests with a fake source | local audiobooks unchanged, tests green |
| 2 | Plugin MVP: connect, list, cover proxy, play, progress sync, finished/restart, settings with test button; tests with a fake ABS server | a book plays from ABS and the position is shared |
| 3 | Web app: merged tab, source chip, continue, card dialog, settings page, help | usable without the command line |
| 4 | Chapters inside one file | next/previous chapter for m4b books |
| 5 | Podcasts from ABS | |
| later | download for offline use, series/collections, listening sessions, live updates (socket.io) | |

Phase 0 and 1 are small, 2 and 3 are the bulk, 4 is medium. Each phase ends with tests, docs and a
commit, as usual; nothing is installed on a box without asking.

## Tests

- Unit tests with a fake source for the audiobooks module and the tracker (merge, delegated
  progress, finished, errors).
- A fake ABS server (FastAPI app in the tests) for the plugin: login/API key, lists, play
  mapping of multi-file and single-file books, progress writes, unreachable server, 401.
- `docker/` gets an optional `audiobookshelf` service with sample content for manual and end-to-end
  tests; CI does not need it.
- Measurements on the Pi Zero (radio) are part of phase 0 and 2: streaming CPU for mp3 and m4b,
  start time of a book, memory of the book list with a few hundred books.

## Risks and open points

- **m4b over HTTP on a Pi Zero:** AAC decoding costs more than mp3, a file with the index at the end
  makes opening slow, and TLS has its own cost. Phase 0 measures this; fallbacks are plain http in
  the home network and, later, downloading the book to the box.
- **ffmpeg of the `av` build:** on 32-bit Raspberry Pi OS the `av` wheel uses the system ffmpeg; it
  must support https and the `headers` option. Checked in phase 0.
- **API differences between ABS versions:** API keys need 2.26 or newer. Older servers use user name
  and password, which the plugin supports through `/login`; token expiry is handled by logging in
  again.
- **Two players, one position:** if the phone and the radio play the same book at the same time,
  the last write wins. That is how ABS itself behaves, so no extra handling.
- **No network, no book:** an ABS book cannot be played without the server. The Audiobooks tab shows
  the cached list (greyed out) and says why.
- **Secrets on the box:** the API key lies in a file readable only by the service user; anyone with
  access to the box (or its backup) can use it, so a key restricted to one user is the right choice.

## Decisions to make

1. Where does the ABS server run (home network, NAS, internet) and does it use https with a
   certificate the box can verify?
2. Which version, and are API keys available (2.26+)?
3. Audiobooks only first (as planned), or are ABS podcasts equally important?
4. Is playing without the server needed (offline cache) soon, or is "the server is always on" fine?
5. Several ABS libraries or servers? The plan has one server, any number of its libraries.
