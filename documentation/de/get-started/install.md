# Installieren

Das dauert etwa eine halbe Stunde, das meiste davon Warten. Bei jedem Schritt steht, was du sehen solltest, wenn es
geklappt hat.

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

| Frage | Antwort |
| --- | --- |
| Upgrade all operating system packages now | *Nein* reicht für den Anfang. |
| Which sound card sits on the header | Hast du eine Soundkarte auf den Pi gesteckt, wähle sie (HiFiBerry-Platinen werden erkannt). Sonst *none*. |
| Is a pHAT BEAT, power button or battery monitor attached | *Nein*, außer du hast sie. |
| Start Lauschkiste at boot, without anyone logging in | *Ja*. Dann startet die Box von selbst, sobald du den Strom anschließt. |
| Serve the web app on port 80 | *Ja*. Die Adresse ist dann einfach `http://<name>.local`. |
| Configure an RFID reader now | *Ja*, und wähle deinen Leser. Ein USB-Leser ist am einfachsten, siehe [RFID-Leser](../hardware/readers.md). |
| Share the library on the network via Samba | *Nein* fürs Erste. Musik kannst du auch auf der Webseite hochladen, siehe [Musik](../using/music.md). |
| Show the web app on an attached display | *Nein*, außer du hast einen Bildschirm angeschlossen: [Ein Bildschirm an der Box](../hardware/screen.md). |
| WiFi hotspot when no known WiFi is in range | *Nein* fürs Erste: [Unterwegs](../using/wifi-hotspot.md). |
| Quiet boot | *Nein*. Es blendet nur Startmeldungen aus. |

Die Fragen erscheinen auf Englisch. Einige Schritte ändern die Startkonfiguration. Am Ende sagt dir `lauschctl setup`, ob
ein Neustart nötig ist:

```bash
sudo reboot
```

## 5. Prüfen

Warte eine Minute und öffne dann `http://<name>.local` in einem Browser auf deinem Computer oder Handy. Du solltest die
Lauschkiste-Webseite mit dem Player sehen. Hast du Port 80 nicht gewählt, hänge `:5556` an die Adresse.

Klappt es nicht, führ `lauschctl setup --check` aus: Es zeigt, was fehlt. Mehr unter
[Wenn etwas nicht klappt](../maintenance/troubleshooting.md).

Weiter: [Deine erste Karte](first-steps.md).
