# Soundkarten und Verstärker

Der Raspberry Pi hat eine eigene Kopfhörerbuchse (nicht die Zero-Modelle). Für besseren Klang oder einen Lautsprecher ohne
eigenes Netzteil setzt du eine Soundkarte oder eine Verstärkerplatine auf den Pin-Header. Um sie geht es hier. Ein
USB-Lautsprecher oder ein Bluetooth-Lautsprecher braucht nichts davon: siehe [Ton und Bluetooth](../using/sound.md).

Alle Soundkarten richtest du gleich ein:

1. Wähle die Karte bei der Frage *Which sound card sits on the header?* („Welche Soundkarte steckt auf der Stiftleiste?“) in `lauschctl setup` oder später mit
   `lauschctl setup hardware`. HiFiBerry-Platinen, die sich selbst melden (über das HAT-EEPROM), werden erkannt und
   vorgewählt.
2. `lauschctl setup raspi` schreibt die passende Zeile (`dtoverlay=...`) in `/boot/firmware/config.txt`, schaltet das eigene
   Audio des Pi aus und legt eine Sicherung an (`config.txt.backup`).
3. Starte die Box neu (`sudo reboot`).

Die Webseite (Einstellungen → Hardware) zeigt die Platine, welche Pins wofür benutzt werden und ob eine Änderung noch auf den
Neustart wartet. Ist eine Karte angeschlossen, aber nicht eingerichtet, zeigt der Player einen Hinweis.

## HiFiBerry

> Die DAC+ wurde auf einem Pi 3 erkannt und eingerichtet. Die anderen Platinen sind noch nicht an echter Hardware getestet.

HiFiBerry DAC+, DAC2 HD, DAC+ ADC, Digi+ und ähnliche sowie günstige Platinen mit PCM5102A. Platinen mit EEPROM werden erkannt;
den Amp und Amp+ (und Platinen ohne EEPROM) wählst du selbst aus der Liste.

Die Platinen sitzen auf dem 40-poligen Header. Brauchst du die übrigen Pins für Tasten oder einen Leser, kannst du die
Platine getrennt verdrahten; sie braucht diese Pins:

| Name auf der Platine | Pin der Platine | Pin am Raspberry Pi | Name |
| --- | --- | --- | --- |
| 3.3V | 1 | 1, 17 | 3V3 |
| 5V | 2 | 2, 4 | 5V |
| GND | 6 | 6, 9, 20, 25 | Masse |
| PCM_CLK | 12 | 12 | GPIO18 |
| PCM_FS | 36 | 36 | GPIO19 |
| PCM_DIN | 38 | 38 | GPIO20 |
| PCM_DOUT | 40 | 40 | GPIO21 |

[Pinübersicht des Raspberry Pi](https://pinout.xyz). Einrichtung nach der Anleitung von
[HiFiBerry](https://www.hifiberry.com/docs/software/configuring-linux-3-18-x/).

## MAX98357A (I²S-Verstärker)

Ein kleiner Verstärker für einen Lautsprecher, der außer dem Overlay keinen Treiber braucht. Wähle `max98357a` als Soundkarte.

| MAX98357A | Raspberry Pi | Pin |
| --- | --- | --- |
| VIN | 5V | 2 oder 4 |
| GND | Masse | 6 |
| BCLK | GPIO18 (PCM_CLK) | 12 |
| LRC | GPIO19 (PCM_FS) | 35 |
| DIN | GPIO21 (PCM_DOUT) | 40 |

`GAIN` und `SD` können offen bleiben (normale Verstärkung, Verstärker immer an).

Die Platine hat keinen eigenen Lautstärkeregler. Die Box stellt die Lautstärke per Software ein. Ist es bei gleicher
Einstellung zu laut oder zu leise, ändere `volume.mixer` und das `volume_limit` des Ausgangs in den Einstellungen.

**Bekanntes Problem:** Der Verstärker kann beim Start knacken. Die Box spielt zuerst kurz Stille und blendet ein, das macht
das Knacken kleiner, beseitigt es aber nicht. An einer Lösung wird gearbeitet: Die Box würde den Verstärker erst einschalten,
wenn der Ton gestartet ist, über einen Pin, der an `SD` hängt.

## Pimoroni pHAT BEAT (Pirate Radio)

Die pHAT BEAT, zum Beispiel im Pirate-Radio-Bausatz, hat einen DAC mit Verstärker, sechs Tasten und zwei Reihen mit je acht
RGB-LEDs. Sie ist täglich in einem Pirate Radio im Einsatz.

1. Antworte in `lauschctl setup` auf „Is a Pimoroni pHAT BEAT attached?“ mit *ja* (oder schalte das Plugin *Pimoroni pHAT BEAT*
   unter Einstellungen → Plugins ein und starte neu).
2. `lauschctl setup raspi`, dann Neustart. Das schaltet den DAC ein und das Onboard-Audio aus.

| Taste | Pin | Tut |
| --- | --- | --- |
| Play/Pause | GPIO6 | `player.toggle` |
| Weiter | GPIO5 | `player.next` |
| Zurück | GPIO13 | `player.prev` |
| Lauter | GPIO16 | +5, wiederholt bei gedrückter Taste |
| Leiser | GPIO26 | -5, wiederholt bei gedrückter Taste |
| Ein/Aus | GPIO12 | fährt herunter, wenn 2 Sekunden gehalten |

Jede Taste kann stattdessen eine andere Aktion ausführen. Die LEDs zeigen nach einer Änderung die Lautstärke und leuchten grün
für eine bekannte und rot für eine unbekannte Karte. Mit `leds: vu` zeigen sie beim Abspielen auch den Pegel der Musik.
`leds: off` lässt sie dunkel und gibt ihre Pins frei; `animations: false` schaltet die Animation beim Start und Herunterfahren aus;
`colors` wählt `classic`, `rainbow`, `ocean`, `sunset`, `unicorn`, `forest` oder `fire`; `reverse: true` dreht die Balken um,
wenn die HAT andersherum sitzt. Die Ein/Aus-Taste fährt das System nur herunter; das Pirate Radio hat keine Schaltung, die danach
den Strom trennt.
