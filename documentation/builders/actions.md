# Actions

Cards, the card removal of place-capable readers and the second swipe all trigger an *action*.
An action is an operation of a core module or plugin, addressed as `<module>.<action>`, with
named arguments:

```yaml
action: player.play_folder
args:
  folder: music/path/to/folder
```

`args` can be left out when the action has no arguments or all of them have defaults:

```yaml
action: player.toggle
```

## Which actions exist?

The running Lauschkiste lists all actions with their arguments at `GET /api/v1/actions`, e.g. in the
browser at `http://<lauschkiste>:5556/api/v1/actions`. `lauschkiste --artifacts` also writes the list to
`shared/artifacts/card_actions.json`. Actions of a plugin only exist while the plugin is enabled.

Frequently used actions of the core:

| Action | Arguments | |
| --- | --- | --- |
| `player.play_card` | `folder`, `recursive` (default false) | play a folder; a second swipe runs the second-swipe action |
| `player.play_folder` | `folder`, `recursive` (default false) | play a folder |
| `player.play_album` | `albumartist`, `album` | play an album |
| `player.play_single` | `song_url` | play one song |
| `audiobooks.play` | `book` | continue an audiobook, see [Audiobooks](audiobooks.md) |
| `player.play`, `player.pause`, `player.toggle`, `player.stop` | | playback |
| `player.next`, `player.prev` | | skip |
| `player.shuffle`, `player.repeat` | `option` (default `toggle`) | playback modes |
| `system.noop` | | do nothing |

Arguments are checked when an action is configured (a card is registered through the web app or
the API); a card with an unknown action or wrong arguments is rejected. Cards whose action is
temporarily unavailable (e.g. its plugin is disabled) stay in the card database and work again
once the plugin is enabled.
