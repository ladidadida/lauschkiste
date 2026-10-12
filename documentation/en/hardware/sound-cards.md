# Sound cards and amplifiers

The Raspberry Pi has a headphone jack of its own (not on the Zero models). For better sound, or a speaker without a
power supply of its own, add a sound card or an amplifier board that sits on the pin header. This page is about those.
A USB speaker or a Bluetooth speaker needs none of it: see [Sound and Bluetooth](../using/sound.md).

All sound cards are set up the same way:

1. Choose the card in the question *Which sound card sits on the header?* of `lauschctl setup`, or later with
   `lauschctl setup hardware`. HiFiBerry boards that name themselves (via the HAT EEPROM) are recognised and preselected.
2. `lauschctl setup raspi` writes the matching line (`dtoverlay=...`) into `/boot/firmware/config.txt`, switches the
   Pi's own audio off and keeps a backup (`config.txt.backup`).
3. Restart the box (`sudo reboot`).

The web page (Settings → Hardware) shows the board, which pins are used, and while a change is still waiting for the
restart. If a card is attached but not set up, the player shows a note.

## HiFiBerry

> The DAC+ was recognised and set up on a Pi 3. The other boards are not tested on real hardware yet.

HiFiBerry DAC+, DAC2 HD, DAC+ ADC, Digi+ and the like, and cheap boards with a PCM5102A. The boards with an EEPROM are
recognised; the Amp and Amp+ (and boards without an EEPROM) you choose yourself from the list.

The boards sit on the 40-pin header. If you need the other pins for buttons or a reader, you can wire the board
separately; it needs these pins:

| Board pin name | Board pin | Raspberry Pi pin | Name |
| --- | --- | --- | --- |
| 3.3V | 1 | 1, 17 | 3V3 |
| 5V | 2 | 2, 4 | 5V |
| GND | 6 | 6, 9, 20, 25 | ground |
| PCM_CLK | 12 | 12 | GPIO18 |
| PCM_FS | 36 | 36 | GPIO19 |
| PCM_DIN | 38 | 38 | GPIO20 |
| PCM_DOUT | 40 | 40 | GPIO21 |

[Raspberry Pi pin overview](https://pinout.xyz). Setup after the instructions of
[HiFiBerry](https://www.hifiberry.com/docs/software/configuring-linux-3-18-x/).

## MAX98357A (I²S amplifier)

A small amplifier for one speaker that needs no driver beyond the overlay. Choose `max98357a` as the sound card.

| MAX98357A | Raspberry Pi | Pin |
| --- | --- | --- |
| VIN | 5V | 2 or 4 |
| GND | ground | 6 |
| BCLK | GPIO18 (PCM_CLK) | 12 |
| LRC | GPIO19 (PCM_FS) | 35 |
| DIN | GPIO21 (PCM_DOUT) | 40 |

`GAIN` and `SD` can stay open (normal gain, amplifier always on).

The board has no volume control of its own. The box sets the volume in software. If it is too loud or too quiet at the
same setting, change `volume.mixer` and the output's `volume_limit` in the settings.

**Known problem:** the amplifier can click when it starts. The box plays a short silence first and fades in, which
makes the click smaller but does not remove it. A fix is being worked on: the box would switch the amplifier on only
after the sound has started, using a pin connected to `SD`.

## Pimoroni pHAT BEAT (Pirate Radio)

The pHAT BEAT, for example in the Pirate Radio kit, has a DAC with amplifier, six buttons and two rows of eight RGB
LEDs. It is in daily use in a Pirate Radio.

1. Answer *yes* to "Is a Pimoroni pHAT BEAT attached?" in `lauschctl setup` (or switch on the plugin *Pimoroni pHAT
   BEAT* under Settings → Plugins and restart).
2. `lauschctl setup raspi`, then restart. This switches the DAC on and the on-board audio off.

| Button | Pin | Does |
| --- | --- | --- |
| Play/pause | GPIO6 | `player.toggle` |
| Next | GPIO5 | `player.next` |
| Previous | GPIO13 | `player.prev` |
| Volume up | GPIO16 | +5, repeats while held |
| Volume down | GPIO26 | -5, repeats while held |
| On/off | GPIO12 | shuts down when held for 2 seconds |

Each button can run any other action instead. The LEDs show the volume after a change and light green for a known card
and red for an unknown one. With `leds: vu` they also show the level of the music while it plays. `leds: off` leaves them
dark and frees their pins; `animations: false` switches off the animation at start and shutdown; `colors` picks
`classic`, `rainbow`, `ocean`, `sunset`, `unicorn`, `forest` or `fire`; `reverse: true` turns the bars round if the HAT
sits the other way. The on/off button only shuts the system down; the Pirate Radio has no circuit that cuts the power.
