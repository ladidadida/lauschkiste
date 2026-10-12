# Time limits

Lauschkiste can keep listening within bounds: **quiet hours** in which nothing plays, and a **daily listening time**.
It is off until you switch it on: Settings → Playback and audio → Time limits → *Use time limits*.

## Quiet hours

A list of times in which nothing plays, each with a start, an end and the days it applies to (every day, Monday to
Friday, Saturday and Sunday). The default entry is the night from 19:30 to 07:00. An entry that runs past midnight
belongs to the day it starts on: "Monday to Friday" covers Friday evening until Saturday morning, but not Saturday
evening.

Whatever is started in quiet hours stops at once, and the player shows "Quiet time until 07:00".

## Daily listening time

The minutes that something plays are counted per day (pausing does not count), starting again at midnight.

| Setting | Meaning | Default |
| --- | --- | --- |
| `daily_limit_minutes` | the limit per day, 0 for none | 120 |
| `weekend_limit_minutes` | a different limit for Saturday and Sunday | none |
| `warn_minutes` | a warning sound this long before the end, 0 for none | 5 |
| `fade_seconds` | the sound fades out over this time when the limit is reached | |

When the time is used up, the sound fades out and the player stops. Playing again the same day stops at once.

## Extra time for grown-ups

The action `time_limits.allow` adds minutes for today and lifts quiet hours for that time. You can call it from the web
page, or register a card with the action `time_limits.allow` and the argument `minutes` (for example 30) and keep it
where the children do not find it. `time_limits.reset_today` counts the day from zero.

## What it cannot do

- **It is not a lock.** Anyone who can open the web page or knows the card can add time or switch the limits off. It
  helps with agreements in the family; it does not stop a determined child.
- **It needs the right time.** The box has no clock of its own and takes the time from the network. If the time is not
  synchronised (for example in a car without WiFi), quiet hours are *not* enforced, because the time cannot be trusted;
  the player says so. The daily time counts playing time and works without a clock.
