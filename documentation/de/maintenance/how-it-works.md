# Wie es funktioniert

Ein kurzer Rundgang, damit Einstellungen und Meldungen Sinn ergeben.

## Die Teile auf der Box

1. **Der Lauschkiste-Dienst** spielt die Musik, kennt die Karten und die Bibliothek, steuert Lautstärke und Zeitlimits und
   liefert die Webseite aus. Er läuft als *Benutzerdienst* mit dem Namen `lauschkiste`, weil er mit dem Tonsystem deiner
   Anmelde-Sitzung sprechen muss.
2. **Das Tonsystem (PipeWire)** gehört zum aktuellen Raspberry Pi OS. Es lässt viele Arten von Tonhardware gleich
   funktionieren und erlaubt Lauschkiste, zwischen Ausgängen umzuschalten (Lautsprecher, Bluetooth).
3. **Die Webseite** liefert Lauschkiste selbst aus, ohne zusätzlichen Webserver. Öffne `http://<name>` (Port 80) oder
   `http://<name>:5556`.
4. **Die Befehle** `lauschkiste` (der Server) und `lauschctl` (Einrichtung und Verwaltung).

## Kern und Plugins

Der **Kern** ist alles, was auf jedem Rechner Sinn ergibt: der Player, die Bibliothek, Karten und die Lesegeräte, Lautstärke,
Timer, Zeitlimits und die Webseite. Er ist immer da. Er läuft auf jedem Linux-Computer, nicht nur auf einem Raspberry Pi.

**Plugins** ergänzen, was von Hardware oder anderen Diensten abhängt: Raspberry-Pi-Unterstützung, Tasten, Akku,
RFID-Lesertreiber, Samba, die Audiobookshelf-Anbindung, Podcast- und Radio-Verzeichnisse. Ein Plugin läuft nur, wenn es
eingeschaltet ist (Einstellungen → Plugins). Startet eines nicht, läuft Lauschkiste weiter; die Webseite und
`lauschctl plugin list` sagen, warum.

## Aktionen

Alles, was die Box kann, ist eine **Aktion** mit einem Namen wie `player.toggle` oder `volume.change_volume`. Karten, Tasten,
Timer, die Webseite und „gleiche Karte noch einmal“ lösen Aktionen aus; die Webseite zeigt, welche es gibt, und unter
`http://<name>/api/v1/actions` stehen sie in einer Liste. Darum kann eine Taste tun, was eine Karte tut.

## Ereignisse

Die Box meldet, was passiert, als Ereignisse (`player.status`, eine Karte wurde gelesen, ...). Die Webseite hört sie ab,
darum aktualisiert sie sich von selbst. Für eigene Werkzeuge gibt `lauschctl debug sniff` sie aus.

## Wo es weitergeht

Die [Entwickler-Dokumentation](../../developers/README.md) (Englisch) erklärt den Code, die Plugin-Schnittstelle und die
REST-Schnittstelle.
