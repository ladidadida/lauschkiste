# When something doesn't work

## No sound

- Check the volume in the player and the maximum volume under Settings → Playback & audio.
- Choose the right audio output under Settings → Playback & audio.
- Sound card and outputs are set up on the box, see [Commands on the box](/help/lauschctl?section=audio).

## A card does nothing

- Is a reader running? Settings → Cards lists the readers. None: [set up the reader](/help/lauschctl?section=reader).
- Is the card registered? The player shows unknown cards with "Register".
- If the card list shows a warning for the card, its action is not available right now, e.g. because a plugin is off or an album was deleted.

## New files don't show up

Tap refresh in the library. Music belongs in `library/music`, audiobooks in `library/audiobooks`.

## The web app can't be reached

- The box needs a few seconds after switching on.
- Address: `http://<name-of-the-box>:5556` or the IP address (Settings → Status, or a card that reads out the IP address).

## Restarting Lauschkiste

Settings → System → "Restart now" restarts only Lauschkiste. If that doesn't help, restart the box (same page).

## Logs

On the box the logs are in `logs/` in the Lauschkiste home (`lauschctl home` shows where); `errors.log` contains only errors.
