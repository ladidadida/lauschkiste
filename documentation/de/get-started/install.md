# Installieren

Das dauert etwa eine halbe Stunde, das meiste davon Warten. Bei jedem Schritt steht, was du sehen solltest, wenn es
geklappt hat. Diese Seite beschreibt einen Raspberry Pi; auf einem PC oder Laptop siehe
[Auf PC, Laptop oder Mini-PC](other-computers.md).

## 1. Die SD-Karte beschreiben

1. Lade den [Raspberry Pi Imager](https://www.raspberrypi.com/software/) herunter und starte ihn.
2. Wähle dein Pi-Modell und das System **Raspberry Pi OS Lite** (64 Bit). „Lite“ heißt: ohne Desktop, und genau das
   will die Box.
3. Wähle die SD-Karte und klicke auf weiter. Wenn er nach Anpassungen fragt, wähle **Einstellungen bearbeiten** und gib
   ein:
   - einen **Namen** für die Box (zum Beispiel `lauschkiste`),
   - einen **Benutzernamen und ein Passwort** (schreib sie auf),
   - dein **WLAN** mit Passwort,
   - und unter *Dienste* schalte **SSH** mit Passwort ein.
4. Beschreibe die Karte. Steck sie in den Pi, schließ den Strom an und warte etwa zwei Minuten.

## 2. An der Box anmelden

Öffne auf deinem Computer ein Terminal (unter Windows: *PowerShell*) und tippe, mit deinem Benutzernamen und dem Namen
der Box:

```bash
ssh <benutzer>@<name>.local
```

Antworte auf die Frage nach dem Fingerabdruck mit *yes* und gib dann dein Passwort ein. Du siehst eine Eingabezeile wie
`pi@lauschkiste:~ $`. Wird der Name nicht gefunden, such die Adresse der Box in deinem Router und nimm sie statt
`<name>.local`.

## 3. Installieren

> [!IMPORTANT]
> **Administratorrechte (`sudo`) sind nötig.** Der Installer und `lauschctl setup` installieren Systempakete, richten Dienste
> ein und ändern die Boot-Konfiguration, und dafür nutzen sie `sudo`. Der Benutzer, mit dem du dich anmeldest, muss es
> verwenden dürfen; auf Raspberry Pi OS ist das beim Benutzer aus dem Imager so. Verlangt `sudo` ein Passwort, fragen der
> Installer und das Setup einmal am Anfang danach (es ist das Passwort dieses Benutzers und wird nicht gespeichert). Ohne
> `sudo`-Rechte brechen sie mit einer Meldung ab, bevor sie etwas ändern.

Füge diese Zeile ein und drücke Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash
```

Das installiert ein paar Grundpakete und Lauschkiste selbst. Am Ende steht dort *Lauschkiste is installed*. Öffne eine
neue Shell (oder tippe `source ~/.profile`), damit die neuen Befehle gefunden werden.

## 4. Die Box einrichten

```bash
lauschctl setup
```

`lauschctl setup` stellt dir nacheinander ein paar Fragen. Mit Enter nimmst du den Vorschlag in Klammern. Bist du dir
nicht sicher, nimm ihn: Du kannst `lauschctl setup` jederzeit noch einmal starten, um etwas zu ändern. Ist deine
Verbindung wackelig, starte es in `screen` oder `tmux`.

| Frage | Auf Deutsch | Antwort |
| --- | --- | --- |
| What kind of machine is this? | Welche Art Maschine ist das? | *Raspberry Pi* auf einem Pi. Auf einem Computer: [Auf PC, Laptop oder Mini-PC](other-computers.md). |
| Upgrade all operating system packages now (takes a while)? | Alle Pakete des Betriebssystems jetzt aktualisieren (dauert eine Weile)? | *Nein* reicht für den Anfang. |
| Which sound card sits on the header? | Welche Soundkarte steckt auf der Stiftleiste? | Hast du eine Soundkarte auf den Pi gesteckt, wähle sie (HiFiBerry-Platinen werden erkannt). Sonst *none*. |
| Use 'Pimoroni pHAT BEAT' / 'Power button' / 'Battery' / 'GPIO buttons and knobs'? | Pimoroni pHAT BEAT / Ein-Aus-Taste / Akku / GPIO-Tasten und Drehregler benutzen? | *Nein*, außer du hast sie. Diese Fragen kommen nach denen zur Box selbst, zusammen mit deinen eigenen Hardware-Plugins. |
| Start Lauschkiste at boot, without anyone logging in? | Lauschkiste beim Hochfahren starten, ohne dass sich jemand anmeldet? | *Ja*. Dann startet die Box von selbst, sobald du den Strom anschließt. |
| Serve the web app on port 80, so its address needs no ":5556"? | Die Webseite auf Port 80 anbieten, damit die Adresse kein „:5556“ braucht? | *Ja*. Die Adresse ist dann einfach `http://<name>.local`. |
| Configure an RFID reader now? | Jetzt einen RFID-Leser einrichten? | *Ja*, und wähle deinen Leser. Ein USB-Leser ist am einfachsten, siehe [RFID-Leser](../hardware/readers.md). |
| Share the library (music and audiobooks) on the network via Samba (Windows/macOS file sharing)? | Die Bibliothek (Musik und Hörbücher) über Samba im Netzwerk freigeben (Windows-/macOS-Dateifreigabe)? | *Nein* fürs Erste. Musik kannst du auch auf der Webseite hochladen, siehe [Musik](../using/music.md). |
| Show the web app full-screen on an attached display after boot? | Die Webseite nach dem Hochfahren im Vollbild auf einem angeschlossenen Bildschirm zeigen? | *Nein*, außer du hast einen Bildschirm angeschlossen: [Ein Bildschirm an der Box](../hardware/screen.md). |
| Open a WiFi hotspot when no known WiFi is in range? | Einen WLAN-Hotspot öffnen, wenn kein bekanntes WLAN in Reichweite ist? | *Nein* fürs Erste: [Unterwegs](../using/wifi-hotspot.md). |
| Make the boot quiet (no boot messages or logo, a few first-boot services off)? | Den Start leise machen (keine Startmeldungen oder Logo, einige Dienste des ersten Starts aus)? | *Nein*. Es blendet nur Startmeldungen aus. |

Die Fragen erscheinen auf Englisch; die deutsche Übersetzung steht daneben. Einige Schritte ändern die Startkonfiguration. Am Ende sagt dir `lauschctl setup`, ob
ein Neustart nötig ist:

```bash
sudo reboot
```

## 5. Prüfen

Warte eine Minute und öffne dann `http://<name>.local` in einem Browser auf deinem Computer oder Handy. Du solltest die
Lauschkiste-Webseite mit dem Player sehen. Hast du Port 80 nicht gewählt, hänge `:5556` an die Adresse.

Klappt es nicht, führ `lauschctl setup --check` aus: Es zeigt, was fehlt. Mehr unter
[Wenn etwas nicht klappt](../maintenance/troubleshooting.md).

Weiter: [Die Box läuft: und jetzt?](first-steps.md).
