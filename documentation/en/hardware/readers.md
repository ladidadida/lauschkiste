# RFID readers and cards

The reader recognises the cards. You can choose between a reader that plugs into USB (simple) and readers that you wire
to the pins of the Pi (cheap, a bit of work). Set the reader up with:

```bash
lauschctl setup rfid
```

The step asks which reader you have, enables the right plugin and installs what it needs. Connect all USB readers before
you run it. The settings land in `settings/rfid.yaml`; you may run the step again at any time (it rewrites the file
after asking). Restart Lauschkiste afterwards.

## Choosing cards

Readers work at one of two frequencies: **125 kHz** (RDM6300) or **13.56 MHz** (all others). Cards, stickers and key
fobs must match. With the MFRC522 only the types *Mifare Classic 1k/4k* and *Mifare Ultralight* work, not NTAG2xx.

## Which readers notice a card staying on

Some readers send one signal when a card is put on. Others send a signal as long as the card is there; they allow
music that stops when the card is taken off ([Cards](../using/cards.md#cards-that-stay-on-the-box)). Known to do this:
RDM6300, MFRC522 (SPI) and PN532 (I2C). USB readers mostly do **not**.

## The readers

| Reader | Connection | Card stays on | Tested |
| --- | --- | --- | --- |
| [USB readers](#usb-readers-keyboard-type) | USB | mostly not | not yet |
| [RC522 / MFRC522](#rc522--mfrc522-spi) | SPI | yes | yes, in daily use |
| [MFRC522 on I2C](#mfrc522-on-i2c) | I2C | | not yet |
| [PN532](#pn532-on-i2c) | I2C | yes | not yet |
| [RDM6300](#rdm6300-serial) | serial | yes | not yet |
| [USB NFC readers without keyboard mode](#usb-nfc-readers-without-keyboard-mode-nfcpy) | USB | | not yet |

"Not yet" means: written and tested with automated tests, but not yet on real hardware by the project. Please report
what you find.

### USB readers (keyboard type)

Most cheap USB readers behave like a keyboard that types the card number. They need no wiring. The user running Lauschkiste
must be in the group `input` (normally the case; otherwise `sudo usermod -a -G input <user>`).

### RC522 / MFRC522 (SPI)

The cheap blue board. It talks over SPI, which the Raspberry Pi device plugin switches on (`lauschctl setup raspi`,
then restart).

| MFRC522 | Function | Raspberry Pi | Pin |
| --- | --- | --- | --- |
| SDA | chip select | GPIO8 (SPI0 CE0) | 24 |
| SCK | clock | GPIO11 (SPI0 SCLK) | 23 |
| MOSI | data out | GPIO10 (SPI0 MOSI) | 19 |
| MISO | data in | GPIO9 (SPI0 MISO) | 21 |
| IRQ | interrupt | GPIO24 | 18 |
| RST | reset | GPIO25 | 22 |
| GND | ground | | 20 |
| 3.3V | power | | 17 |

Some boards label MOSI and MISO the other way round. Nothing breaks if you swap them wrong: if no card is read, swap the
two wires. Without the IRQ wire the box polls, which uses a lot of CPU; without the RST wire the reset pin must be
connected to 3.3V.

Options in `rfid.yaml` (`config:`): `spi_ce` (0 or 1), `pin_irq` (24), `pin_rst` (25), `antenna_gain` (4),
`mode_legacy` (false; only for large collections of 4-byte numbers from older installations).

### MFRC522 on I2C

The same chip over I2C, for example the M5Stack RFID 2 unit. Options: `i2c_bus` (1), `i2c_address` (0x28). To find the
address install `i2c-tools` and run `i2cdetect -y 1`.

| MFRC522 | Raspberry Pi | Pin |
| --- | --- | --- |
| 5V | 5V | 4 |
| GND | GND | 6 |
| SDA | GPIO2 (SDA) | 3 |
| SCL | GPIO3 (SCL) | 5 |

### PN532 on I2C

Good reading range and many card types, e.g. the Adafruit PN532 breakout. It needs two pins, but polls. Set its two
jumpers for I2C: SEL0 on, SEL1 off. Connect 5V (not also 3.3V).

| PN532 | Raspberry Pi | Pin |
| --- | --- | --- |
| 5V | 5V | 4 |
| GND | GND | 6 |
| SDA | GPIO2 (SDA) | 3 |
| SCL | GPIO3 (SCL) | 5 |

### RDM6300 (serial)

A 125 kHz reader on the serial port (UART). Its RX/TX levels are 3.3 V, not 5 V as often said; check your board
before you wire anything. You wire pins at your own risk.

### USB NFC readers without keyboard mode (nfcpy)

For USB NFC devices that cannot be used as a keyboard. [nfcpy](https://nfcpy.readthedocs.io/en/latest/overview.html)
lists the supported devices. Connect the device before running `lauschctl setup rfid`: the step stops the kernel from
claiming it and finds the device. To use several devices, give each its `device_path` in `rfid.yaml`, for example
`usb:072f:2200` (vendor and product ID).

## Reader settings

Every reader has an entry in `settings/rfid.yaml`:

```yaml
rfid:
  readers:
    read_00:
      module: rc522_spi
      config: {}                 # reader specific, filled by lauschctl setup rfid
      same_id_delay: 1.0         # seconds before the same card counts again (against bouncing)
      place_not_swipe:
        enabled: false           # true: the card stays on; needs a reader that can tell
        card_removal_action:
          action: player.pause
```

`card_removal_action` is the same for all cards on that reader. Individual cards can switch the removal action off or
the delay off, see [Cards](../using/cards.md).
