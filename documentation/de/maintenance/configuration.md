# Einstellungen und Dateien

Das meiste stellst du auf der Webseite ein (Einstellungen). Einiges ändert das Betriebssystem und erledigst du auf der Box mit
`lauschctl` ([Befehle](commands.md)). Der Rest steht in Dateien.

## Wo alles liegt

Alle Daten der Box liegen in einem Ordner, dem *Lauschkiste-Home*. `lauschctl home` gibt ihn aus. Auf einem Raspberry Pi ist
es `~/lauschkiste`.

```text
~/lauschkiste/
├── settings/    lauschkiste.yaml (Einstellungen), cards.yaml, rfid.yaml, secrets.yaml, logger.yaml
├── library/     music/ und audiobooks/
├── playlists/
├── logs/
└── cache/       Titelbilder, Downloads
```

Um die Box zu sichern, kopiere diesen Ordner.

## Eine einzelne Einstellung ändern

```bash
lauschctl config get volume.soft_max_volume
lauschctl config set volume.soft_max_volume 60
```

Schlüssel und Passwörter von Plugins (etwa der Audiobookshelf-Schlüssel) liegen getrennt in `secrets.yaml`, nur für den
Benutzer der Box lesbar: `lauschctl config set <schlüssel> --secret`. `lauschctl config get` zeigt sie nicht an.

## Die Datei bearbeiten

Die Datei `settings/lauschkiste.yaml` ist kommentiert. Halte Lauschkiste an, bevor du sie bearbeitest, damit es deine
Änderung nicht überschreibt:

```bash
systemctl --user stop lauschkiste
nano ~/lauschkiste/settings/lauschkiste.yaml
systemctl --user start lauschkiste
```

Relative Pfade in den Dateien gelten ab dem Lauschkiste-Home; absolute Pfade und Pfade, die mit `~/` beginnen, werden so
verwendet, wie sie sind.

## Eine andere Konfiguration ausprobieren

```bash
lauschkiste --conf /pfad/zu/andere.yaml
```

startet Lauschkiste in der Konsole mit einer anderen Datei, zum Beispiel, um eine niedrigere Höchstlautstärke zu testen.

## Plugins

Ein Plugin ergänzt Funktionen: Platinen-Unterstützung, Tasten, Leser, Verzeichnisse für Podcasts und Radio. Es läuft nur, wenn es
eingeschaltet ist, unter Einstellungen → Plugins oder mit `lauschctl plugin enable <name>`.

```bash
lauschctl plugin list                      # installierte Plugins und ob sie laufen
lauschctl plugin enable <name>
lauschctl plugin disable <name>
lauschctl plugin install <paket>           # ein Plugin von PyPI oder aus einer anderen Quelle
```

Installiere nur Plugins, denen du vertraust: Ein Plugin läuft mit den Rechten des Benutzers der Box.
