# Die Befehle

Zwei Befehle erledigen alles auf der Box. Melde dich per SSH an und tippe sie in ein Terminal; jeder erklärt sich selbst mit
`--help`.

## `lauschctl`: die Box einrichten und verwalten

| Befehl | Was er tut |
| --- | --- |
| `lauschctl setup` | richtet die Box Schritt für Schritt ein und stellt Fragen; `--yes` übernimmt frühere Antworten |
| `lauschctl setup <schritt>` | führt einen Schritt aus; `--list` listet die Schritte, `--check` meldet nur, was fehlt |
| `lauschctl update` | installiert eine neuere Version |
| `lauschctl uninstall` | entfernt, was Lauschkiste angelegt hat, und sich selbst zuletzt |
| `lauschctl config get\|set <schlüssel> [wert]` | liest und ändert eine einzelne Einstellung |
| `lauschctl plugin list\|enable\|disable\|install` | verwaltet Plugins |
| `lauschctl home` | gibt den Ordner mit den Daten und die benutzte Einstellungsdatei aus |

### Die Einrichtungsschritte

`lauschctl setup` geht in zwei Teilen vor: erst das Gerät (welche Art Maschine das ist) und seine Optionen, dann das, was
angeschlossen ist (die Peripherie), und deren Optionen. Jeder Schritt schaut zuerst nach und ändert nur, was fehlt; einen zu wiederholen ist also unbedenklich.

| Schritt | Wofür |
| --- | --- |
| `device` | welche Art Maschine das ist; bestimmt, was die anderen Schritte anbieten |
| `packages` | die Systempakete, die Lauschkiste braucht (und auf Wunsch ein Systemupgrade) |
| `hardware` | die Soundkarte auf der Stiftleiste (Raspberry Pi) |
| `plugins` | schaltet die Plugins ein, die die Antworten verlangen |
| `service` | Lauschkiste als Dienst, der mit der Box startet |
| `port` | die Webseite auf Port 80, damit die Adresse kein `:5556` braucht |
| `audio` | wählt die Audioausgänge ([Ton](../using/sound.md)) |
| `samba` | die Bibliothek als Netzwerkordner ([Musik](../using/music.md)) |
| `rfid` | der RFID-Leser ([RFID-Leser](../hardware/readers.md)) |
| `kiosk` | die Webseite auf einem angeschlossenen Bildschirm ([Bildschirm](../hardware/screen.md)) |
| `autohotspot` | das eigene WLAN der Box ([Unterwegs](../using/wifi-hotspot.md)) |
| `boot` | ruhiger Start, Bluetooth optional aus |
| `welcome` | die Meldung bei der Anmeldung |
| `extra_plugins` | installiert Plugins von PyPI, GitHub (`github:owner/repo@tag`) oder per URL, auch für eigene Hardware |
| `peripherals` | was angeschlossen ist: pHAT BEAT, Ein-Aus-Taste, Akkuüberwachung, Tasten und Drehregler, und deine eigene |
| `peripheral_options` | die Optionen des Angeschlossenen (z. B. der Akku-Sensor) |
| `raspi` | schreibt Soundkarte und Pins in die Startkonfiguration (danach neu starten) |

## `lauschkiste`: der Server

`lauschkiste` ist das Programm, das spielt. Auf einer Box läuft es als Dienst, der mit der Box startet; du rufst es selten
selbst auf. Um zu sehen, was es tut, halte den Dienst an und starte es in der Konsole:

```bash
systemctl --user stop lauschkiste
lauschkiste -vv           # mehr Meldungen; Strg-C beendet es
systemctl --user start lauschkiste
```

Den Dienst steuerst du mit `systemctl --user start|stop|restart|status lauschkiste`.
