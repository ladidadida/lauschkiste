# Card Database

In the card database, an [action](actions.md) is assigned to every card. It runs every time the
card is swiped (or placed) on the reader.

Cards are usually registered through the web app. The database is stored in
`$LAUSCHKISTE_HOME/settings/cards.yaml` (config key `cards.database`):

> [!IMPORTANT]
> Card IDs **must** be strings! So, be sure to quote numbers!

```yaml
'0001':
  action: player.pause
'0002':
  action: player.play_card
  args:
    folder: path/to/folder
```

## Additional options

These options may be specified for every card.

### ignore_card_removal_action: true \| false (default: false)

Only applies when using a place-capable reader and *place_not_swipe* is *true*. This option is
ignored otherwise, so it does not hurt.

Do not execute the card removal action when this card is removed from the reader. Useful for
command cards, e.g. one that starts a timer.

### ignore_same_id_delay: true \| false (default: false)

Override the `same_id_delay` parameter from the reader configuration for this card. If true, the
`same_id_delay` for this card is treated as 0. This makes sense e.g. for a "next song" card in
combination with a place-capable RFID reader: as long as the card is placed on the reader, the
action repeats.

> [!NOTE]
> This parameter causes *ignore_card_removal_action* to be treated as true

```yaml
'0005':
  action: player.next
  ignore_same_id_delay: true
  ignore_card_removal_action: true
```
