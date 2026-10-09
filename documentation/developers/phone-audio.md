# Playing from a phone (Bluetooth)

Status: plan, nothing implemented yet.

Some content cannot be played by the box itself, because it only plays in the app of its provider. The case
that started this: **audiobooks of the Onleihe** (the library lending service). The goal: the box can be used
as the loudspeaker of a phone, and while the phone plays, the box behaves like a player (it shows what plays and
its buttons work).

## Why not the Onleihe itself

- The Onleihe has **no public interface** for audio. Titles are lent through its own app, whose integrated
  player is the only one that plays them (streaming, or downloaded inside the app).
- Titles are protected by **DRM** (the lending period is enforced by it). Taking the audio out of the app means
  circumventing that protection, which German copyright law forbids (§ 95a UrhG) even for lent media.
  Lauschkiste does not do that, and no plugin of it should.
- What is allowed and works with every app: the phone plays, **the box is only the speaker**.

## Ways to get the sound from the phone to the box

| Way | Works with | Needs on the box | Verdict |
| --- | --- | --- | --- |
| **Bluetooth (A2DP)** | every app, Android and iOS | BlueZ and a sound server | **chosen**: the only one that takes any app |
| AirPlay | iPhone/iPad, apps that offer it | shairport-sync | possible later as a further source |
| Google Cast, Spotify Connect, DLNA | apps that offer it (the Onleihe app is not known to) | a receiver each | later, per service |

## What the test box already has

Checked on the Pi Zero W (`loma-box-light`): a Bluetooth adapter (`hci0`, currently powered off), BlueZ 5.82,
**PipeWire 1.4.2 with WirePlumber and `libspa-0.2-bluetooth`**, all installed and running (PipeWire answers as a
PulseAudio server for our volume module); 427 MB RAM, ARMv6 single core. With PipeWire the phone's audio arrives as
a normal stream on the box's sound output, so no extra decoder has to be written. Open: how much CPU the SBC/AAC
decoding takes on the Zero (phase 0 measures it).

## Design

### Layers

1. **System** (`lauschctl setup bluetooth`): BlueZ and the Bluetooth part of PipeWire installed, adapter powered
   on, name of the box ("Lauschkiste"), device class "loudspeaker", a pairing agent without PIN (the phone only
   asks "pair?"), the box not discoverable by default.
2. **Plugin `phone_audio`** (talks to BlueZ over D-Bus, with the pure-Python `dbus-fast` that also installs on the
   Pi Zero):
   - **Pairing window:** the action `phone_audio.pair(minutes=2)` makes the box discoverable and pairable for a
     short time, then closes it again. Pairing is the only moment a stranger in range could connect, so it is
     never open permanently. Triggers: a button in the web app, a card ("pairing card"), a GPIO button.
   - **Devices:** paired phones (name, connected, last seen), `forget`, a limit on how many are kept (default 3).
     A paired phone reconnects by itself when it comes into range.
   - **Streaming state:** BlueZ announces when a phone starts and stops sending audio (`MediaTransport1`: `active`
     or `idle`), and, if the app supports it, what plays (`MediaPlayer1`: title, artist, album, position).
3. **Player backend `phone`** (registered at `player.backends`): while a phone streams it is the active
   backend. The status shows title and artist from the phone (apps that send nothing show "Phone: <name>"), and
   the box's play/pause/next/previous go to the phone as media keys (AVRCP). The volume is the box's (the same
   mixer as for everything else).

### Hand-over

| Event | What happens |
| --- | --- |
| Phone starts streaming while the box plays | the box pauses its own playback; the phone is in charge |
| Phone stops (pause, other app, out of range) | the box stays silent; it does **not** resume by itself |
| A card is placed while the phone streams | the phone is paused over AVRCP, the card's content plays |
| Quiet hours or the daily limit ([time limits](../builders/time-limits.md)) | the phone is paused and its sound muted, the same rules as for everything else |
| Two phones | the one that streams first keeps the box until it stops |

### In the web app

A "Bluetooth" block in the settings: state, paired phones, **Pair a phone** (with a countdown while the window is
open), forget. The player page shows what the phone plays and a note "from <phone>". No new top-level page.

### Settings

`device_name` (default "Lauschkiste"), `pairing_minutes` (2), `max_devices` (3), `pause_own_playback` (on),
`volume` (the volume the box starts the phone's stream at).

## Phases and estimate

The effort is given in working days of focused work; the hardware part is where the time goes.

| Phase | Content | Days |
| --- | --- | --- |
| 0 | **Spike on the Zero, without code**: power the adapter, pair a phone with `bluetoothctl`, play the Onleihe app to the MAX98357A, measure CPU, RAM and dropouts, see what AVRCP data the Onleihe app (and a music app) sends | 0.5 to 1 |
| 1 | `lauschctl setup bluetooth`; plugin with pairing window, device list and forget; actions and tests with a fake BlueZ | 1 to 1.5 |
| 2 | Streaming state, hand-over, player backend `phone` (status, media keys, volume), interplay with time limits; tests with fake D-Bus objects, then real phones | 2 to 3 |
| 3 | Web app (block in the settings, notice in the player), pairing card, translations, documentation | 1 |
| 4 | Hardening: reconnect, several phones, an hour of continuous playing on the Zero, Android and iOS differences | 1 to 2 |

**About 6 to 9 days for everything; a usable first version (phases 0, 1 and the hand-over of phase 2 without
metadata) in 2 to 3 days.** Phase 0 decides whether the Zero W is strong enough; if not, the recommendation
would be a Zero 2 W or a Pi 3 for a box that is also used as a Bluetooth speaker.

### Risks

- **Phones differ.** Android makers and iOS versions handle AVRCP, reconnecting and absolute volume differently;
  this is the part that takes the longest and needs several real devices.
- **CPU of the Zero W** with a sound server, Bluetooth decoding and the web app at once (phase 0 measures it).
- **Apps decide what they send.** The Onleihe app may send no title or position over AVRCP; the box then shows only
  that a phone plays.
- **Pairing without PIN** is convenient and acceptable only because the window is short and opened on purpose.
- The Bluetooth radio and WiFi of the Zero share one antenna; a long stream may stutter while the web app
  is used a lot.

## Questions for the decision

1. Android or iPhone (or both) for the Onleihe? Both work with A2DP, the quirks differ.
2. Should the box's buttons control the phone (needs AVRCP), or is "the phone is just a speaker feed" enough?
3. How should pairing be started: web app only, or also a card or a button on the box?
4. Later: do AirPlay or Spotify Connect belong to the same idea ("external sources" with the same hand-over)?
   The design above would be the first of them.

## Recommendation

Not part of `0.1.0-alpha.4`. Release that first, and take this as the next feature. **Phase 0 can be done today, with
no code**: the PipeWire stack of the test Zero should accept a phone as it is. If that works, the idea is proven.
