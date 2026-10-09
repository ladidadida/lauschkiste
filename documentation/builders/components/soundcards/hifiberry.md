# HiFiBerry

The setup works for the most common set of HiFiBerry boards but also other "DAC" related sound cards like `I2S PCM5102A DAC`.

## Automatic setup

Choose the board in the web app (Settings → Plugins → Raspberry Pi → Sound card, e.g. `hifiberry-dac`), then
run `lauschctl setup raspi` on the box and reboot. The step adds the board's `dtoverlay` to
`/boot/firmware/config.txt` (replacing another sound overlay), switches the on-chip audio off and keeps a backup
as `config.txt.backup`. Settings → Hardware shows while a change is still pending.

The setup is based on [HiFiBerry's instructions](https://www.hifiberry.com/docs/software/configuring-linux-3-18-x/).

## How to manually wire your HiFiBerry board

Most HiFiBerry boards come with 40-pin header that you can directly attach to your Pi. This idles many GPIO pins that may be required for other inputs to be attached (like GPIO buttons or RFID). You can also connect your HiFiBerry board separately. The following table show cases the pins required.

* [Raspberry Pi Pinout](https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/os/using-gpio.adoc)

| Board pin name | Board pin | Physical RPi pin | RPi pin name |
|----------------|-----------|------------------|--------------|
| 3.3V           | 1         | 1, 17            | 3V3 power    |
| 5V             | 2         | 2, 4             | 5V power     |
| GND            | 6         | 6, 9, 20, 25     | Ground       |
| PCM_CLK        | 12        | 12               | GPIO18       |
| PCM_FS         | 36        | 36               | GPIO19       |
| PCM_DIN        | 38        | 38               | GPIO20       |
| PCM_DOUT       | 40        | 40               | GPIO21       |

You can find more information about manually wiring in a [forum thread](https://forum-raspberrypi.de/forum/thread/44967-kein-ton-ueber-hifiberry-miniamp-am-rpi-4/?postID=401305#post401305).
