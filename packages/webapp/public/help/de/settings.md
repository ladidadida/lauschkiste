# Einstellungen

Alles, was nur Lauschkiste selbst betrifft, stellst du in der Web-App ein. Änderungen werden sofort gespeichert; manche wirken erst nach einem Neustart von Lauschkiste, dann erscheint oben „Jetzt neu starten“. Das startet nur den Lauschkiste-Dienst neu, nicht die ganze Box.

| Seite | Inhalt |
| --- | --- |
| Status | Version, IP-Adresse, Speicher, Temperatur, Akku |
| Wiedergabe & Audio | Ausgänge (Name, Gerät, Lautstärkegrenze), Lautstärke, Player, Hörbücher, Podcasts, Start- und Endton, Tasten von USB-Geräten und Medientasten |
| Karten | Kartenliste, Verhalten beim erneuten Auflegen, Lesegeräte (Sperrzeit, Auflegen statt Wischen, Aktion beim Abnehmen) |
| Bibliothek | Cover, Einlesen, Netzlaufwerk (Samba) |
| Plugins | Erweiterungen an- und ausschalten und einstellen, z. B. Raspberry Pi (GPIO-Tasten, Drehregler, LED, Akku) |
| System | Ansagen, Neustart, Herunterfahren |

## Plugins

Plugins erweitern Lauschkiste um Hardware und Quellen. Ein- und Ausschalten wirkt nach einem Neustart. Fehlen einem Plugin Pakete, installiert „Installieren“ auf der Plugin-Seite sie nach; das kann einige Minuten dauern.

## Was nur auf der Box geht

Einstellungen am Betriebssystem brauchen Administratorrechte und laufen über `lauschctl setup` auf der Box: Soundkarte, Samba installieren, WLAN-Hotspot, Boot-Optimierung, Kiosk-Modus, Lesegerät einrichten. Siehe [Befehle auf der Box](/help/lauschctl).
