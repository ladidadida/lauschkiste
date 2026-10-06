# Bibliothek

## Aufbau

Die Bibliothek ist nach Inhalten geordnet:

| Reiter | Inhalt |
| --- | --- |
| Weiterhören | angefangene Hörbücher und Podcasts mit neuen Folgen |
| Musik | alle Alben; unter „Ordner“ die Dateien in `library/music` |
| Hörbücher | alle Hörbücher mit Fortschritt; unter „Ordner“ die Dateien in `library/audiobooks` |
| Radio | Internet-Radiosender |
| Podcasts | abonnierte Podcasts mit ihren Folgen |

## Hochladen

Unter Musik → Ordner bzw. Hörbücher → Ordner auf „Hochladen“ tippen und Dateien oder ganze Ordner wählen (bis 1 GiB je Datei). Am Computer kannst du Dateien auch einfach in die Liste ziehen.

- **Musik:** ein Ordner je Album. Titel, Interpret und Cover kommen aus den Dateien oder aus einem Bild im Ordner (`cover.jpg`).
- **Hörbücher:** ein Ordner je Hörbuch. Die Dateien sind die Kapitel und laufen in Dateinamen-Reihenfolge (`2` vor `10`).

Neue Dateien erscheinen nach ein paar Sekunden von selbst; der Aktualisieren-Knopf startet das Einlesen sofort.

## Netzlaufwerk (Samba) {#samba}

Für große Sammlungen lässt sich die Bibliothek als Netzlaufwerk im Windows-Explorer oder macOS-Finder öffnen. Samba wird einmalig auf der Box installiert ([Befehle auf der Box](/help/lauschctl?section=samba)), danach schaltest du die Freigabe unter Einstellungen → Bibliothek ein.

### Benutzer und Passwort

- **Benutzername** ist der Benutzer, unter dem Lauschkiste auf der Box läuft, also der, mit dem du dich auch per SSH anmeldest (z. B. `pi`). Einen anderen Benutzer gibt es nicht; die Einstellungsseite zeigt den Namen an.
- **Passwort** ist ein eigenes Samba-Passwort, unabhängig vom Login-Passwort der Box. Du setzt oder änderst es unter Einstellungen → Bibliothek → „Neues Samba-Passwort“ (mindestens 8 Zeichen). Das neue Passwort ersetzt das alte sofort.

### Verbinden

| Rechner | So geht's |
| --- | --- |
| Windows | Im Explorer in die Adresszeile `\\<name-der-box>\lauschkiste` eingeben |
| macOS | Finder → Gehe zu → Mit Server verbinden → `smb://<name-der-box>/lauschkiste` |
| Linux | Im Dateimanager `smb://<name-der-box>/lauschkiste` öffnen |

Beim ersten Verbinden fragt der Rechner nach Benutzername und Passwort; „Kennwort speichern“ erspart die Eingabe beim nächsten Mal. Statt des Namens geht auch die IP-Adresse (Einstellungen → Status).

## Radio

Unter Radio → „Sender hinzufügen“ einen Namen und die Stream-Adresse eintragen. Auch `.m3u`- und `.pls`-Links von Sender-Webseiten funktionieren.

## Podcasts

Unter Podcasts → „Podcast abonnieren“ die Adresse des RSS-Feeds eintragen (nicht die der Webseite). Folgen werden gestreamt, die Box braucht dafür Internet. „Neueste ungehörte Folge abspielen“ eignet sich gut für eine Karte.
