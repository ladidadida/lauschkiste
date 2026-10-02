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
| `audiobooks.play` | `book` | play from the saved position |
| `audiobooks.restart` | `book` | play from the beginning |
| `audiobooks.set_finished` | `book`, `finished` (default true) | mark as finished or not; both start from the beginning next time |

`GET /api/v1/audiobooks` lists all audiobooks with chapter, position and progress.

## Settings

```yaml
audiobooks:
  rewind_sec: 10                          # go back this far when continuing
  state_file: settings/audiobooks.json    # positions
```
