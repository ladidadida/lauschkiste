# Time limits

Lauschkiste keeps listening within bounds: **quiet hours** in which nothing plays, and a **daily listening time**.
It is part of the core and **off until you switch it on**: Settings → Playback & audio → Time limits → "Use time
limits".

## Quiet hours

A list of times in which nothing plays, each with a start, an end and the days it applies to ("every day",
"Monday to Friday", "Saturday and Sunday"). The default entry is the night, from 19:30 to 07:00. An entry that
runs past midnight belongs to the day it starts on: "Monday to Friday" covers Friday evening until Saturday
morning, but not Saturday evening.

Whatever is started in quiet hours stops at once. The player shows "Quiet time until 07:00".

## Listening time per day

The minutes something plays are counted per day (pausing does not count); the count starts again at midnight.
`daily_limit_minutes` is the limit (0 for none), `weekend_limit_minutes` can be a different one for Saturday and
Sunday. `daily_limit_minutes` is 120 by default. A warning sound plays `warn_minutes` (5) before the end; 0 switches the warning off. When the time is used up, the sound
fades out over `fade_seconds` and the player stops; playing again the same day stops at once.

## Extra time for parents

The action `time_limits.allow` adds minutes for today and lifts quiet hours for that time. It works from the web
app and from a card: register a card with the action `time_limits.allow` and the argument `minutes` (for example 30)
and keep it where the children do not find it. `time_limits.reset_today` counts the day from zero again.

## What it cannot do

- **It is not a lock.** Anyone who can open the web app or knows the card can add time or switch the time limits off.
  It is a helper for agreements in the family, not protection against a determined child.
- **It needs the right time.** The box has no clock of its own; it takes the time from the network. If the clock is
  not synchronized (for example in a car without WiFi) quiet hours are *not* enforced, because the time cannot be
  trusted; the player says so. The daily time is counted by the playing time and works without a clock.
