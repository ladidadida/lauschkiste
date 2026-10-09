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

## Find podcasts

With the plugin `podcast_directories` (Settings → Plugins, or `lauschctl plugin enable podcast_directories`)
the button "Subscribe to podcast" opens a search: type a name, or look at the popular podcasts when the
field is empty, and subscribe with one tap. "Add by address" is still there for a feed address.

Each directory has a switch and the setting that fits it in the settings of the plugin:

| Directory | What it offers | Settings |
| --- | --- | --- |
| Apple Podcasts | search and popular podcasts per country, no key | `itunes.enabled`, `itunes.country` (default `DE`) |
| fyyd | a German directory: search and popular podcasts per language, no key | `fyyd.enabled`, `fyyd.language` |
| Podcast Index | needs a free key and secret from podcastindex.org (off until you enter them) | `podcastindex.enabled`, `podcastindex.language`, `podcastindex_key`, `podcastindex_secret` |

Every directory has its own interface, so a further one needs code: see
[Podcast and radio directories](../developers/core-and-plugins.md#podcast-and-radio-directories).

Every search goes to the directories that are switched on, so switch off those you do not want to ask.
A directory that does not answer is named in the dialog and the others still show their results.

[podcast.de](https://www.podcast.de) has no public interface, so it is not among them (German podcasts are
found in Apple Podcasts and fyyd as well).

### From and to other apps (OPML)

The menu next to the button imports and exports an OPML file, the list format of podcast apps. To move
over from AntennaPod, export your subscriptions there (Settings → Import/Export → OPML export) and choose
"Import from an OPML file". The episodes are loaded in the background; podcasts you already follow are skipped.
"Export as an OPML file" gives the other direction.
