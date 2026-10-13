# Podcasts

A podcast is a feed on the internet that adds new episodes. The box streams episodes, so playing them needs the
internet unless you download them.

## Subscribe

In the library open **Podcasts** and tap **Subscribe to podcast**:

- **Search.** With the plugin *Podcast directories* (on from the setup; Settings → Plugins switches it off) the dialog searches Apple Podcasts, fyyd (a
  German directory) and, with a free key, Podcast Index. Type a name, or leave the field empty to see the popular
  ones, and subscribe with one tap. Every directory has a switch in the plugin's settings, and what you type is sent to
  the directories that are on.
- **By address.** If you know the feed address, use *Add by address*.

Every episode continues where it stopped and counts as heard once it has played to the end.

## On a card

Play an episode and tap the card button in the player, or choose *Play podcast* when registering a card in the card
list. Without an episode, the card
plays the newest episode not heard yet (or the newest, if all are heard). With a chosen episode it always plays that
one.

## Download episodes

The menu of an episode has **Download to the box**. A downloaded episode plays without the internet and continues
where you stopped it. Downloads share the space settings of Settings → Library → Cache; with *remove old* on, heard
episodes are removed first when it is full. Unsubscribing removes the downloaded episodes of that podcast.

## From and to other apps

The menu next to *Subscribe to podcast* imports and exports an **OPML file**, the list format of podcast apps. To move
over from AntennaPod, export your subscriptions there (Settings → Import/Export → OPML export) and choose *Import
from an OPML file*. Podcasts you already follow are skipped.

## Settings

| Setting | Meaning | Default |
| --- | --- | --- |
| `podcasts.refresh_minutes` | fetch a feed again when its episodes are older | 60 |
| `podcasts.max_episodes` | episodes kept per podcast | 100 |
| `podcasts.rewind_sec` | go back this far when continuing | 10 |
