# Wenn etwas nicht klappt

Geh von oben nach unten vor. Die meisten Probleme löst einer der ersten Schritte.

## 1. Was sagt die Einrichtung?

```bash
lauschctl setup --check
```

listet jeden Einrichtungsschritt als *ok* oder *to do* auf. Führe für einen Schritt mit *to do* `lauschctl setup <schritt>`
aus, oder `lauschctl setup` für alle. Die Schritte ändern nur, was fehlt; sie zu wiederholen schadet nicht.

## 2. Läuft Lauschkiste?

```bash
systemctl --user status lauschkiste
```

Läuft es nicht, starte es mit `systemctl --user start lauschkiste`. Hält es wieder an, lies das Log (unten).

## 3. Funktioniert der Ton?

Siehe [Kein Ton?](../using/sound.md#kein-ton).

## 4. Die Webseite öffnet sich nicht

- Ist die Box im selben WLAN wie dein Gerät? Probier die Adresse statt des Namens: Such sie in deinem Router, oder melde dich
  per SSH an und führe `hostname -I` aus.
- Ohne Port 80 braucht die Adresse `:5556`: `http://<name>:5556`.
- Nach einem Neustart braucht die Box eine Minute.
- Eine Karte oder die Aktion `system.say_my_ip` lässt die Box ihre IP-Adresse vorlesen.

## 5. Das Log lesen

```bash
journalctl --user -b -u lauschkiste          # alles seit dem letzten Start
```

Lauschkiste schreibt auch Dateien in den Ordner `logs` seines Home (`lauschctl home`):

| Datei | Inhalt |
| --- | --- |
| `app.log` | vollständige Debug-Meldungen des aktuellen Laufs |
| `errors.log` | nur Warnungen und Fehler |

Der vorherige Lauf bleibt als `app.log.1` erhalten. Dieselben Logs kannst du im Browser unter `http://<name>/logs` lesen.
Prüfe immer das Datum der Datei: Vielleicht liest du eine alte.

Um die Meldungen live zu sehen, halte den Dienst an und starte Lauschkiste in der Konsole:

```bash
systemctl --user stop lauschkiste
lauschkiste -vv
```

Beende es mit Strg-C und starte danach den Dienst wieder.

## 6. Leser und Karten

- Der Leser wird von `lauschctl setup rfid` gefunden; schließe USB-Leser an, *bevor* du es ausführst.
- Eine Karte, die die Box nicht kennt, zeigt im Player **Registrieren**. Zeigt sich nichts, arbeitet der Leser nicht: Starte
  `lauschkiste -vv` und halte eine Karte darauf.
- Karten der falschen Frequenz werden nicht gelesen. Siehe [RFID-Leser](../hardware/readers.md).

## 7. Immer noch festgefahren?

Frag in den [Issues](https://github.com/ladidadida/lauschkiste/issues) des Projekts und gib die Ausgabe von
`lauschctl setup --check`, `lauschctl plugin list` und die letzten Zeilen von `errors.log` an.
