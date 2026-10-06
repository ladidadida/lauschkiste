# Befehle auf der Box

Einige Einstellungen ändern das Betriebssystem und brauchen Administratorrechte. Die erledigt `lauschctl` direkt auf der Box. Dazu meldest du dich per SSH an, z. B. am Computer im Terminal:

```bash
ssh <benutzer>@<name-oder-ip-der-box>
```

Jeder Einrichtungsschritt prüft zuerst und ändert nur, was fehlt; erneutes Ausführen schadet nicht. `lauschctl setup --list` zeigt alle Schritte, `lauschctl setup --check` nur, was fehlt.

## Übersicht

| Befehl | Wofür |
| --- | --- |
| `lauschctl setup` | alles einrichten (fragt nach) |
| `lauschctl setup <schritt>` | einen Schritt, z. B. `samba` |
| `lauschctl update` | auf die neueste Version aktualisieren |
| `lauschctl plugin list` | installierte Plugins |
| `lauschctl home` | wo Einstellungen und Bibliothek liegen |

## Samba {#samba}

```bash
lauschctl setup samba
```

Installiert Samba, gibt die Bibliothek als `lauschkiste` frei und fragt nach einem Samba-Passwort. Danach lassen sich Freigabe und Passwort in der Web-App ändern (Einstellungen → Bibliothek).

## Lesegerät {#reader}

```bash
lauschctl setup rfid
```

Fragt, welches Lesegerät angeschlossen ist (z. B. RC522, USB-Leser) und wie es verdrahtet ist, schaltet das passende Plugin ein und installiert, was es braucht. Danach Lauschkiste neu starten.

## Audio {#audio}

```bash
lauschctl setup raspi
lauschctl setup audio
```

`raspi` schreibt in die Boot-Konfiguration (`config.txt`), was in den Einstellungen des Raspberry-Pi-Plugins und der Geräte-Plugins gewählt ist: Soundkarte (z. B. MAX98357A, HiFiBerry), eingebauter Kopfhörerausgang, I²C, SPI und der Abschalt-Pin eines Ein-/Aus-Tasters. Danach die Box neu starten. Was noch fehlt, zeigt Einstellungen → Hardware. `audio` legt fest, welche Ausgänge Lauschkiste anbietet.

## Update {#update}

```bash
lauschctl update
```

Holt die neueste Version, installiert sie und startet Lauschkiste neu. Einstellungen, Karten und Bibliothek bleiben erhalten.

## Hotspot {#hotspot}

```bash
lauschctl setup autohotspot
```

Öffnet ein eigenes WLAN, wenn kein bekanntes in Reichweite ist, z. B. unterwegs.

## Weitere Schritte

| Schritt | Wofür |
| --- | --- |
| `boot` | schnellerer Start (Bluetooth, IPv6, Startmeldungen aus) |
| `kiosk` | Web-App auf einem angeschlossenen Bildschirm |
| `mpd` | mpd als Wiedergabe statt der eingebauten |
| `service` | Lauschkiste als Dienst beim Start |
