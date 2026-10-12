# RFID-Leser und Karten

Der Leser erkennt die Karten. Du kannst zwischen einem Leser wählen, der in USB steckt (einfach), und Lesern, die du an die
Pins des Pi verdrahtest (günstig, etwas Arbeit). Richte den Leser so ein:

```bash
lauschctl setup rfid
```

Der Schritt fragt, welchen Leser du hast, schaltet das passende Plugin ein und installiert, was es braucht. Schließe alle
USB-Leser an, bevor du ihn ausführst. Die Einstellungen landen in `settings/rfid.yaml`; du darfst den Schritt jederzeit
wiederholen (er schreibt die Datei nach Rückfrage neu). Starte Lauschkiste danach neu.

## Karten wählen

Leser arbeiten mit einer von zwei Frequenzen: **125 kHz** (RDM6300) oder **13,56 MHz** (alle anderen). Karten, Aufkleber und
Anhänger müssen dazu passen. Mit dem MFRC522 funktionieren nur die Typen *Mifare Classic 1k/4k* und *Mifare Ultralight*,
nicht NTAG2xx.

## Welche Leser eine aufliegende Karte bemerken

Manche Leser senden ein Signal, wenn eine Karte aufgelegt wird. Andere senden ein Signal, solange die Karte da ist; sie
erlauben Musik, die aufhört, wenn die Karte weggenommen wird ([Karten](../using/cards.md#karten-die-auf-der-box-liegen-bleiben)).
Bekannt dafür sind: RDM6300, MFRC522 (SPI) und PN532 (I2C). USB-Leser tun das meistens **nicht**.

## Die Leser

| Leser | Anschluss | Karte bleibt liegen | Getestet |
| --- | --- | --- | --- |
| [USB-Leser](#usb-leser-tastaturtyp) | USB | meist nicht | noch nicht |
| [RC522 / MFRC522](#rc522--mfrc522-spi) | SPI | ja | ja, im täglichen Einsatz |
| [MFRC522 an I2C](#mfrc522-an-i2c) | I2C | | noch nicht |
| [PN532](#pn532-an-i2c) | I2C | ja | noch nicht |
| [RDM6300](#rdm6300-seriell) | seriell | ja | noch nicht |
| [USB-NFC-Leser ohne Tastaturmodus](#usb-nfc-leser-ohne-tastaturmodus-nfcpy) | USB | | noch nicht |

„Noch nicht“ heißt: geschrieben und mit automatischen Tests geprüft, aber vom Projekt noch nicht an echter Hardware
ausprobiert. Berichte gern, was du findest.

### USB-Leser (Tastaturtyp)

Die meisten billigen USB-Leser verhalten sich wie eine Tastatur, die die Kartennummer tippt. Sie brauchen keine
Verdrahtung. Der Benutzer, unter dem Lauschkiste läuft, muss in der Gruppe `input` sein (normalerweise der Fall; sonst
`sudo usermod -a -G input <benutzer>`).

### RC522 / MFRC522 (SPI)

Die günstige blaue Platine. Sie spricht SPI, das die Raspberry-Pi-Unterstützung einschaltet (`lauschctl setup raspi`, dann
Neustart).

| MFRC522 | Funktion | Raspberry Pi | Pin |
| --- | --- | --- | --- |
| SDA | Chip-Auswahl | GPIO8 (SPI0 CE0) | 24 |
| SCK | Takt | GPIO11 (SPI0 SCLK) | 23 |
| MOSI | Daten raus | GPIO10 (SPI0 MOSI) | 19 |
| MISO | Daten rein | GPIO9 (SPI0 MISO) | 21 |
| IRQ | Unterbrechung | GPIO24 | 18 |
| RST | Reset | GPIO25 | 22 |
| GND | Masse | | 20 |
| 3.3V | Strom | | 17 |

Manche Platinen beschriften MOSI und MISO vertauscht. Vertauschen schadet nichts: Wird keine Karte gelesen, tausche die
beiden Kabel. Ohne die IRQ-Leitung fragt die Box ständig ab, was viel CPU braucht; ohne die RST-Leitung muss der Reset-Pin
an 3,3 V liegen.

Optionen in `rfid.yaml` (`config:`): `spi_ce` (0 oder 1), `pin_irq` (24), `pin_rst` (25), `antenna_gain` (4), `mode_legacy`
(false; nur für große Sammlungen mit 4-Byte-Nummern aus älteren Installationen).

### MFRC522 an I2C

Derselbe Chip über I2C, zum Beispiel die M5Stack RFID 2 Unit. Optionen: `i2c_bus` (1), `i2c_address` (0x28). Die Adresse
findest du, wenn du `i2c-tools` installierst und `i2cdetect -y 1` ausführst.

| MFRC522 | Raspberry Pi | Pin |
| --- | --- | --- |
| 5V | 5V | 4 |
| GND | GND | 6 |
| SDA | GPIO2 (SDA) | 3 |
| SCL | GPIO3 (SCL) | 5 |

### PN532 an I2C

Gute Reichweite und viele Kartentypen, zum Beispiel die Adafruit-PN532-Platine. Sie braucht zwei Pins, fragt aber ab. Stell
ihre beiden Jumper auf I2C: SEL0 an, SEL1 aus. Schließe 5V an (nicht zusätzlich 3,3V).

| PN532 | Raspberry Pi | Pin |
| --- | --- | --- |
| 5V | 5V | 4 |
| GND | GND | 6 |
| SDA | GPIO2 (SDA) | 3 |
| SCL | GPIO3 (SCL) | 5 |

### RDM6300 (seriell)

Ein 125-kHz-Leser am seriellen Anschluss (UART). Seine RX/TX-Pegel sind 3,3 V, nicht 5 V, wie oft behauptet wird; prüfe
deine Platine, bevor du etwas verdrahtest. Pins verdrahtest du auf eigene Gefahr.

### USB-NFC-Leser ohne Tastaturmodus (nfcpy)

Für USB-NFC-Geräte, die sich nicht als Tastatur benutzen lassen. [nfcpy](https://nfcpy.readthedocs.io/en/latest/overview.html)
listet die unterstützten Geräte. Schließe das Gerät an, bevor du `lauschctl setup rfid` ausführst: Der Schritt hindert den
Kernel daran, es zu beanspruchen, und findet das Gerät. Für mehrere Geräte gibst du jedem in `rfid.yaml` seinen
`device_path`, zum Beispiel `usb:072f:2200` (Hersteller- und Produkt-ID).

## Einstellungen des Lesers

Jeder Leser hat einen Eintrag in `settings/rfid.yaml`:

```yaml
rfid:
  readers:
    read_00:
      module: rc522_spi
      config: {}                 # leserspezifisch, von lauschctl setup rfid gefüllt
      same_id_delay: 1.0         # Sekunden, bevor dieselbe Karte wieder zählt (gegen Prellen)
      place_not_swipe:
        enabled: false           # true: die Karte bleibt liegen; braucht einen Leser, der das erkennt
        card_removal_action:
          action: player.pause
```

`card_removal_action` ist für alle Karten dieses Lesers gleich. Einzelne Karten können die Aktion beim Wegnehmen oder die
Verzögerung abschalten, siehe [Karten](../using/cards.md).
