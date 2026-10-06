# OnOff SHIM by Pimoroni

The OnOff SHIM switches the Raspberry Pi on with a button press, shuts it down cleanly with the
next press and then cuts the power. In Lauschkiste it is the `power_button` plugin with the preset
"Pimoroni OnOff SHIM" (button on GPIO17, power-off on GPIO4); no Pimoroni script is needed.

1. Settings → Plugins: switch on "Power button" (and install its packages when asked), restart.
2. Its settings: hardware "Pimoroni OnOff SHIM" (the default).
3. On the box: `lauschctl setup raspi`, then reboot. This adds
   `dtoverlay=gpio-poweroff,gpiopin=4,active_low=1` to `config.txt`, which cuts the power once the
   system has halted.

A press of the button shuts Lauschkiste down like a shutdown card: playback stops, positions are
saved, the shutdown sound plays, then the Pi halts and the SHIM switches it off. Other power
buttons work the same way with the hardware "Own pins".

## How to manually wire OnOff SHIM

The OnOff SHIM comes with a 12-PIN header which needs soldering. If you want to spare some GPIO pins for other purposes, you can individually wire the OnOff SHIM with the Raspberry Pi. Below you can find a table of Pins to be connected.

| Board pin name | Board pin | Physical RPi pin | RPi pin name |
|----------------|-----------|------------------|--------------|
| 3.3V           | 1         | 1, 17            | 3V3 power    |
| 5V             | 2         | 2                | 5V power     |
| 5V             | 4         | 4                | 5V power     |
| GND            | 6         | 6, 9, 20, 25     | Ground       |
| GPLCLK0        | 7         | 7                | GPIO4        |
| GPIO17         | 11        | 11               | GPIO17       |

* More information can be found here: <https://pinout.xyz/pinout/onoff_shim>

## Assembly options

![OnOffShim soldered on a Raspberry Pi](https://cdn.review-images.pimoroni.com/upload-b6276a310ccfbeae93a2d13ec19ab83b-1617096824.jpg?width=640)
