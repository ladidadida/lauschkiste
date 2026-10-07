# Wenn etwas nicht klappt

## Kein Ton

- Lautstärke im Player und die maximale Lautstärke unter Einstellungen → Wiedergabe & Audio prüfen.
- Unter Einstellungen → Wiedergabe & Audio den richtigen Audio-Ausgang wählen.
- Soundkarte und Ausgänge richtest du auf der Box ein, siehe [Befehle auf der Box](/help/lauschctl?section=audio).

## Eine Karte reagiert nicht

- Läuft ein Lesegerät? Einstellungen → Karten zeigt die Lesegeräte. Keins da: [Lesegerät einrichten](/help/lauschctl?section=reader).
- Ist die Karte angelernt? Unbekannte Karten zeigt der Player mit „Anlernen“ an.
- Zeigt die Kartenliste bei der Karte eine Warnung, ist ihre Aktion gerade nicht verfügbar, z. B. weil ein Plugin aus ist oder ein Album gelöscht wurde.

## Neue Dateien erscheinen nicht

In der Bibliothek auf Aktualisieren tippen. Musik gehört nach `library/music`, Hörbücher nach `library/audiobooks`.

## Die Web-App ist nicht erreichbar

- Die Box braucht ein paar Sekunden nach dem Einschalten.
- Adresse: `http://<name-der-box>` (mit `lauschctl setup port`, auf dem Raspberry Pi Standard), sonst `http://<name-der-box>:5556`, oder die IP-Adresse (Einstellungen → Status, oder per Karte „IP-Adresse ansagen“).

## Lauschkiste neu starten

Einstellungen → System → „Jetzt neu starten“ startet nur Lauschkiste neu. Hilft das nicht: die Box neu starten (gleiche Seite).

## Protokolle

Auf der Box liegen die Protokolle in `logs/` im Lauschkiste-Verzeichnis (`lauschctl home` zeigt, wo); `errors.log` enthält nur Fehler.
