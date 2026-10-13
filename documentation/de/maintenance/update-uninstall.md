# Aktualisieren und entfernen

## Aktualisieren

Melde dich per SSH an der Box an und führe aus:

```bash
lauschctl update --check     # gibt es eine neuere Version?
lauschctl update             # installieren, Einrichtung erneut anwenden, Lauschkiste neu starten
```

`lauschctl update` richtet sich danach, wie Lauschkiste installiert wurde: Von PyPI aktualisiert es von PyPI, von
Release-Paketen (`--from github`) nimmt es das neueste Release, und ein Quell-Checkout (`--from source`) holt seinen Branch.
`--version <version>` wählt eine bestimmte Version. Plugins, die du selbst installiert hast, bleiben.

Danach läuft die Einrichtung mit deinen früheren Antworten noch einmal (zum Beispiel, um die Dienstdefinition zu
aktualisieren), und ein laufendes Lauschkiste wird neu gestartet. Musik, Einstellungen und Karten liegen im
Lauschkiste-Home und werden nicht angefasst.

> [!NOTE]
> Boxen mit einer Version vor 0.1.0a7 lassen sich nicht mit `lauschctl update` aktualisieren: Die Plugins sind in zwei
> Pakete umgezogen (`lauschkiste-plugins`, `lauschkiste-plugins-raspberry-pi`), und das alte Programm kennt das nicht.
> Führe stattdessen einmal den Installer aus (`curl -fsSL https://raw.githubusercontent.com/ladidadida/lauschkiste/main/install.sh | bash`)
> und danach `lauschctl setup`. Einstellungen, Karten und Bibliothek bleiben. Ab 0.1.0a7 funktioniert `lauschctl update`
> wie beschrieben.
>
> Einstellungen oder Karten aus Phoniebox 2.x lassen sich nicht übernehmen; installiere Lauschkiste auf einer frischen SD-Karte.

## Entfernen

```bash
lauschctl uninstall --check   # was würde entfernt, und was bleibt
lauschctl uninstall           # entfernen; fragt, bevor es deine Daten löscht
```

Es entfernt, was Lauschkiste selbst angelegt hat: seine Dienste, die Weiterleitung von Port 80, die Anmeldemeldung, die
Kiosk- und Samba-Einträge, die Zeilen, die der Installer in dein Shell-Profil geschrieben hat, und zuletzt Lauschkiste mit
seinen Befehlen. Deine Daten (Musik, Einstellungen, Karten) bleiben, außer du antwortest *ja* oder gibst `--remove-data` an.
Ein Quell-Checkout wird nicht gelöscht.

Was zum System gehört, bleibt, und der Befehl listet es auf, mit dem Hinweis, wie du es von Hand zurücknimmst:
Systempakete (`apt remove`), Starteinstellungen (Soundkarten-Zeilen, ruhiger Start), Netzwerkeinstellungen (Hotspot,
Konsolen-Anmeldung) und der Samba-Benutzer.
