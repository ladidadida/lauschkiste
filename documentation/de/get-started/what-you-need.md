# Was du brauchst

Eine Lauschkiste baust du an einem Nachmittag. Für die einfache Version musst du nichts löten.

## Der Computer

Lauschkiste braucht einen kleinen Computer, der in der Ecke dauernd an bleibt. Dafür musst du keinen Raspberry Pi kaufen,
und Pis sind nicht mehr billig. Die Möglichkeiten, ungefähr vom günstigsten zum bequemsten:

| Computer | Gut für | Hinweise |
| --- | --- | --- |
| **Was du schon hast**: ein alter Laptop, ein Mini-PC, ein übriger PC | Ausprobieren, oder eine Box mit eingebautem Bildschirm und Lautsprechern | Jeder 64-Bit-Linux-PC geht: [Auf PC, Laptop oder Mini-PC](other-computers.md). Oft der günstigste Start. |
| Raspberry Pi Zero W | eine sehr kleine, billige Box | Funktioniert und ist getestet, aber langsam: Die Installation dauert etwa zehn Minuten länger, die Webseite öffnet sich langsam, an einen Bildschirm ist nicht zu denken. Keine Kopfhörerbuchse: Für den Ton brauchst du eine kleine Verstärkerplatine, eine USB-Soundkarte oder Bluetooth. |
| Raspberry Pi Zero 2 W | dasselbe, aber schneller | Vier Kerne statt einem, gleiche Größe und ebenfalls keine Kopfhörerbuchse. Eine gute kleine Box. Von uns noch nicht getestet. |
| Raspberry Pi 3 B / 3 B+ | der Allrounder | Schnell genug für alles, auch für einen kleinen Touch-Bildschirm. Hat Kopfhörerbuchse und USB. Getestet und **unsere Empfehlung**, wenn du einen kaufst oder gebraucht findest. |
| Raspberry Pi 4 | ein Bildschirm an der Box, viele Streams | Mehr, als die Box braucht, aber gut. Ein gebrauchter ist ein guter Fund. |
| Raspberry Pi 5 | nichts zusätzlich | Geht im Prinzip, kostet aber mehr, braucht ein stärkeres Netzteil, hat keine Kopfhörerbuchse und bringt nichts, was die Box braucht. |
| Ältere Pi 1 oder Pi 2 | wenn einer in der Schublade liegt | Langsam wie der Zero W. |

Empfehlung: Nimm für den ersten Versuch einen Computer, den du schon hast. Für eine Box zum Verschenken ist ein **Pi 3 B**
(gebraucht ist in Ordnung) oder ein **Pi Zero 2 W** genau richtig; nimm den Pi 3, wenn du eine Kopfhörerbuchse oder einen
Bildschirm willst. Die Preise schwanken stark, schau also in die Shops, bevor du dich entscheidest.

## Die anderen Teile

| Teil | Wofür | Hinweise |
| --- | --- | --- |
| Eine microSD-Karte, 16 GB oder mehr (nur Pi) | der Speicher der Box | Musik braucht Platz; je größer die Karte, desto mehr passt drauf. Andere Computer nehmen ihre eigene Platte. |
| Ein Netzteil (nur Pi) | | Das passende zu deinem Pi-Modell. |
| Lautsprecher | | Aktive Lautsprecher mit Kopfhörerstecker, ein USB-Lautsprecher oder eine kleine Verstärkerplatine, siehe [Soundkarten](../hardware/sound-cards.md). Ein Laptop hat eigene. |
| Ein RFID-Leser (optional) | liest die Karten | Nur, wenn du Karten willst. Am einfachsten ist ein USB-Leser. Leser, die du an den Pi anschließt, stehen unter [RFID-Leser](../hardware/readers.md). |
| RFID-Karten, Aufkleber oder Anhänger (optional) | eine pro Album, Buch oder Sender | Kauf solche, die zur Frequenz des Lesers passen (125 kHz oder 13,56 MHz). |

Ohne Leser spielst du die Box über die Webseite auf Handy oder Tablet, mit Tasten oder mit einem Bildschirm: Karten sind
eine Möglichkeit, die Box zu bedienen, kein Muss. Siehe [Die Box läuft](first-steps.md).

An der Box selbst brauchst du einen Benutzer mit Administratorrechten (`sudo`), siehe [Installieren](install.md). Dazu brauchst du einen Computer, ein Tablet oder ein Handy im selben WLAN, um die Webseite zu öffnen, die die Box steuert,
und bei einem Pi eine Möglichkeit, die SD-Karte zu beschreiben (ein Computer mit Kartenschacht oder ein Kartenleser).

## Was du nicht brauchst

- Keinen Bildschirm und keine Tastatur an der Box. Alles wird von deinem Computer aus eingerichtet.
- Keine Programmierkenntnisse. Du tippst einmal ein paar Befehle; Kopieren und Einfügen genügt.

## Bevor du anfängst

- Überlege dir einen Namen für die Box, zum Beispiel `lauschkiste`. Er wird zur Adresse der Webseite.
- Halte den Namen und das Passwort deines WLANs bereit.
- Lege deine Musik auf dem Computer in Ordner, ein Ordner pro Album oder Hörbuch.

Weiter: [Installieren](install.md). Auf einem PC oder Laptop statt eines Pi: [Auf PC, Laptop oder Mini-PC](other-computers.md).
