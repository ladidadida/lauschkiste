# What you need

You can build a Lauschkiste in an afternoon. Nothing needs soldering for the basic version.

## The computer

Lauschkiste needs a small computer that stays on in the corner. You do not have to buy a Raspberry Pi for it, and Pis
are not cheap any more. The choices, roughly from cheapest to most comfortable:

| Computer | Good for | Remarks |
| --- | --- | --- |
| **What you already have**: an old laptop, a mini PC, a spare PC | trying it, or a box with a screen and speakers built in | Any 64 bit Linux PC works: [On a PC, laptop or mini PC](other-computers.md). Often the cheapest start. |
| Raspberry Pi Zero W | a very small, cheap box | Works and is tested, but slow: the install takes about ten minutes longer, the web page opens slowly, and a screen is out of the question. No headphone jack: sound needs a small amplifier board, a USB sound card or Bluetooth. |
| Raspberry Pi Zero 2 W | the same, but faster | Four cores instead of one, same size and same missing headphone jack. A good small box. Not tested by us yet. |
| Raspberry Pi 3 B / 3 B+ | the all-rounder | Fast enough for everything including a small touch screen. Has a headphone jack and USB. Tested, and **our recommendation** if you buy one, or if you find one second-hand. |
| Raspberry Pi 4 | a screen on the box, many streams | More than the box needs, but fine. A second-hand one is a good find. |
| Raspberry Pi 5 | nothing extra | Works in principle, but costs more, needs a stronger power supply, has no headphone jack and brings nothing the box needs. |
| Older Pi 1 or Pi 2 | if one sits in a drawer | Slow like the Zero W. |

Recommendation: use a computer you already have for the first try. For a box to give away, a **Pi 3 B** (second-hand is
fine) or a **Pi Zero 2 W** is the sweet spot; take the Pi 3 if you want a headphone jack or a screen. Prices change a
lot, so look at the shops before you decide.

## The other parts

| Part | What for | Notes |
| --- | --- | --- |
| A microSD card, 16 GB or more (Pi only) | the box's memory | Music takes space; a bigger card holds more. Other computers use their own disk. |
| A power supply (Pi only) | | The one that fits your Pi model. |
| Speakers | | Active speakers with a headphone plug, a USB speaker, or a small amplifier board, see [sound cards](../hardware/sound-cards.md). A laptop has its own. |
| An RFID reader (optional) | reads the cards | Only if you want cards. The easy start is a USB reader. Readers that you wire to the Pi are described in [RFID readers](../hardware/readers.md). |
| RFID cards, stickers or key fobs (optional) | one per album, book or station | Buy ones that match the reader's frequency (125 kHz or 13.56 MHz). |

Without a reader the box is played from the web page on a phone or tablet, with buttons or with a screen: cards are one
way to control the box, not a must. See [The box is running](first-steps.md).

You also need a computer, tablet or phone in the same WiFi to open the web page that controls the box, and, for a Pi, a
way to write the SD card (a computer with a card slot or a card reader).

## What you do not need

- No screen or keyboard on the box. Everything is set up from your computer.
- No programming. You type a few commands once, copy and paste is enough.

## Before you start

- Decide on a name for the box, for example `lauschkiste`. It becomes the address of the web page.
- Have your WiFi name and password at hand.
- Put your music in folders on your computer, one folder per album or audiobook.

Next: [Install](install.md). On a PC or laptop instead of a Pi: [On a PC, laptop or mini PC](other-computers.md).
