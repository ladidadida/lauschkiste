# Pimoroni pHAT BEAT (Pirate Radio)

The pHAT BEAT, e.g. in Pimoroni's Pirate Radio kit, has an I²S DAC with amplifier, six buttons and
two bars of eight RGB LEDs. In Lauschkiste it is the `phat_beat` plugin. It is in daily use in a Pirate Radio.

1. Settings → Plugins: switch on "Pimoroni pHAT BEAT" (and install its packages when asked),
   restart. It needs the Raspberry Pi board support.
2. On the box: `lauschctl setup raspi`, then reboot. This switches the DAC on
   (`dtoverlay=hifiberry-dac`) and the on-board audio off.

| Button | Pin | Default action |
| --- | --- | --- |
| Play/pause | GPIO6 | `player.toggle` |
| Next (fast-forward) | GPIO5 | `player.next` |
| Previous (rewind) | GPIO13 | `player.prev` |
| Volume up | GPIO16 | `volume.change_volume` +5, repeats while held |
| Volume down | GPIO26 | `volume.change_volume` -5, repeats while held |
| On/off | GPIO12 | `hardware.shutdown` when held for 2 s |

Every button can run any [action](../../actions.md) instead. The LEDs (GPIO23 data, GPIO24 clock)
show the volume after a change and light up green for a known card and red for an unknown one.
With `leds: vu` they also show the level of each channel while playing (only with the `local_audio`
player), with volume and cards shown over it; `leds: off` leaves them dark and their pins free. The
bars fill up when the box is ready and sink when it shuts down (`animations: false` turns
that off). `colors` picks the colors of the meter and the animations: `classic` (green, yellow,
red), `rainbow`, `ocean`, `sunset`, `unicorn`, `forest` or `fire`. The bars fill as in the Pirate
Radio; `reverse: true` turns them round for a pHAT BEAT mounted the other way.

The on/off button only shuts the system down; the Pirate Radio has no circuit that cuts the power
afterwards.
