# Ton und Bluetooth

Die Box spielt über den Tonausgang des Raspberry Pi: die Kopfhörerbuchse, einen USB-Lautsprecher, HDMI, eine Soundkarte
auf dem Pin-Header ([Soundkarten](../hardware/sound-cards.md)) oder Bluetooth. Der Ton läuft über PipeWire, das das
aktuelle Raspberry Pi OS mitbringt.

Lauschkiste kennt **zwei Ausgänge**: den *primären*, der nach jedem Start da sein muss (dein Lautsprecher oder deine
Soundkarte), und einen optionalen *sekundären* für Bluetooth-Kopfhörer oder einen Bluetooth-Lautsprecher. Auf der Webseite
schaltest du zwischen ihnen um.

## Kein Ton?

Prüfe auf der Box (per SSH anmelden, siehe [Installieren](../get-started/install.md#2-an-der-box-anmelden)):

```bash
wpctl status                                       # listet die Ausgänge („Sinks“), der mit Stern ist der Standard
wpctl set-default <id>                             # einen anderen zum Standard machen
alsamixer                                          # Lautstärke der Soundkarte (Esc beendet)
pw-play /usr/share/sounds/alsa/Front_Center.wav    # einen Testton abspielen
```

Spielt der Testton, aber Lauschkiste ist stumm, schau unter Einstellungen → Wiedergabe und Audio und auf die
Lautstärkegrenze. Bleibt schon der Testton stumm, liegt das Problem an der Soundkarte, nicht an Lauschkiste.

## Die Ausgänge wählen

```bash
lauschctl setup audio
```

listet die Ausgänge der Box auf und fragt, welcher primär und welcher sekundär sein soll. Ausgänge von Soundkarten heißen
nach der Karte (zum Beispiel „HiFiBerry DAC+“). Ohne diesen Schritt nimmt die Box den Standardausgang des Systems.

## Bluetooth-Kopfhörer oder -Lautsprecher

Einmal koppeln, dann das Gerät als sekundären Ausgang eintragen.

```bash
bluetoothctl
```

Versetze die Kopfhörer in den Kopplungsmodus, dann in `bluetoothctl`:

```text
scan on          warten, bis dein Gerät erscheint, und seine Adresse notieren (C4:FB:20:63:C0:FE)
scan off
pair C4:FB:20:63:C0:FE
trust C4:FB:20:63:C0:FE
connect C4:FB:20:63:C0:FE
exit
```

Meckert `bluetoothctl` wegen Berechtigungen, starte es mit `sudo`. Nach ein paar Sekunden sollte `wpctl status` das Gerät als
Ausgang listen (`bluez_output...`); teste es mit `pw-play`. Wenn nicht, schalte die Kopfhörer aus und wieder ein. Starte dann
`lauschctl setup audio` noch einmal und wähle die Kopfhörer als sekundären Ausgang.

Bluetooth ist standardmäßig an; antworte in `lauschctl setup` nicht mit *ja* auf „Also switch Bluetooth off“.

## Tasten an Bluetooth-Kopfhörern

Die Tasten für Wiedergabe, Weiter, Zurück und Lautstärke der Kopfhörer erscheinen als Eingabegeräte. Damit die Box darauf
reagiert, setze `input.media_keys: true` in den Einstellungen (standardmäßig aus, damit eine Tastatur an einem
Desktop-Computer nicht übernommen wird). Die Tasten lösen die passenden Aktionen aus (Pause, Weiter, Lautstärke). Andere Tasten
und USB-Taster stehen unter [Tasten und Drehregler](../hardware/buttons.md).

Um von einer Karte oder einer Taste zwischen Lautsprecher und Kopfhörern umzuschalten, nimm die Aktion
`volume.toggle_output`.

## Lautstärke

- Der Regler im Player stellt die Lautstärke ein.
- `volume.soft_max_volume` (Standard 70) ist die höchste einstellbare Lautstärke, ein Schutz für die Ohren. Du änderst sie
  auf der Webseite unter Einstellungen → Wiedergabe und Audio.
- `volume.startup_volume` (Standard 40) ist die Lautstärke nach dem Start.
