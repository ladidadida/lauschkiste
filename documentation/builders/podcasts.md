# Podcasts

A podcast is an RSS (or Atom) feed. Subscribed podcasts are kept in `settings/podcasts.yaml` and
managed through the web app or the API. Episodes are streamed, not downloaded, so playing them
needs an internet connection.

The episodes of a feed are cached and fetched again when they are older than `refresh_minutes`; if
the feed can't be reached, the cached episodes are used. Each episode continues where it stopped,
going back a few seconds, and counts as heard once it has played to the end.

## Cards

```yaml
action: podcasts.play
args:
  podcast: betthupferl
```

Without `episode`, the card plays the newest unheard episode (or the newest, when all are heard).
With `episode` (the id from the list of episodes) it always plays that one.

| Action | Arguments | |
| --- | --- | --- |
| `podcasts.play` | `podcast`, `episode` (optional) | play the newest unheard or a given episode |
| `podcasts.set_heard` | `podcast`, `episode`, `heard` (default true) | mark as heard or not; both start from the beginning next time |
| `podcasts.refresh` | `podcast` (optional) | fetch the episodes of one or all podcasts |

## API

| Request | Body | |
| --- | --- | --- |
| `GET /api/v1/podcasts` | | all podcasts with the number of (unheard) episodes |
| `GET /api/v1/podcasts/<id>/episodes` | | episodes, newest first, with position and heard state |
| `POST /api/v1/podcasts` | `url`, `name` (optional, default: the feed's title) | subscribe |
| `PUT /api/v1/podcasts/<id>` | `name` | rename |
| `DELETE /api/v1/podcasts/<id>` | | unsubscribe |

## Settings

```yaml
podcasts:
  refresh_minutes: 60    # fetch a feed again when its episodes are older
  max_episodes: 100      # episodes kept per podcast
  rewind_sec: 10         # go back this far when continuing
```

## Download episodes

The menu of an episode has **Download to the box**. A downloaded episode plays without the network and
continues where you stopped it streaming (the position belongs to the episode). Downloads share the space
and speed settings of the cache (Settings → Cache, [Audiobooks](audiobooks.md#downloading-books)); with
`remove_old` switched on, heard episodes are removed first when the space is full. Unsubscribing from a
podcast removes its downloaded episodes.
