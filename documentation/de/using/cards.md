# Karten

Eine Karte startet eine *Aktion*: ein Album abspielen, ein Hörbuch fortsetzen, einen Sender einstellen, lauter machen, die
Box ausschalten. Karten werden auf der Webseite registriert; du musst keine Dateien bearbeiten.

## Eine Karte registrieren

- **Am einfachsten:** etwas abspielen, im Player auf das **Karten-Symbol** tippen, die Karte auf das Lesegerät halten.
- **Eine Karte, die die Box nicht kennt:** Hältst du sie auf das Lesegerät, zeigt der Player **Registrieren**.
- **Aus der Liste:** Einstellungen → Karten → Kartenliste → **+**, Karte auf das Lesegerät halten, wählen, was sie tut.

Während du registrierst, startet eine Karte, die schon belegt ist, nicht.

## Was eine Karte kann

| Aktion | Was passiert |
| --- | --- |
| Musik abspielen | ein Album, ein Ordner oder ein Lied |
| Hörbuch abspielen | dort weitermachen, wo das Kind aufgehört hat, oder von vorn |
| Radio abspielen | ein Sender |
| Podcast abspielen | die neueste noch nicht gehörte Folge oder eine bestimmte |
| Ton und Lautstärke | lauter, leiser, Pause, weiter, zurück, zufällig, wiederholen |
| Timer und System | Einschlaf-Timer, die IP-Adresse vorlesen, ausschalten |
| Zeitlimits | Extra-Zeit für heute, siehe [Zeitlimits](time-limits.md) |

Eine Karte für Erwachsene, zum Beispiel „ausschalten“, bewahrst du am besten dort auf, wo die Kinder sie nicht finden.

## Dieselbe Karte noch einmal

Wird eine **Ordner-Karte** noch einmal aufgelegt, während ihr Ordner läuft, kann die Box etwas anderes tun, als von vorn
zu beginnen: pausieren und weiterspielen, das nächste Lied spielen oder neu starten. Das stellst du unter
Einstellungen → Karten ein (*Gleiche Karte erneut aufgelegt*). Hörbuch-Karten setzen immer fort.

## Karten, die auf der Box liegen bleiben

Manche Lesegeräte merken, wann die Karte aufliegt und wann sie weggenommen wird. Mit so einem Lesegerät verhält sich die
Box wie eine Figur auf einem Lautsprecher: **Die Musik spielt, solange die Karte aufliegt, und pausiert, wenn sie
weggenommen wird.** Schalte für das Lesegerät *Auflegen statt Wischen* ein und wähle die Aktion für das Wegnehmen, zum
Beispiel *Pause*. Die Aktion ist für alle Karten dieses Lesegeräts gleich. Legst du eine Hörbuch-Karte wieder auf, geht das
Buch weiter. Welche Lesegeräte das können, steht unter
[RFID-Leser](../hardware/readers.md#welche-leser-eine-aufliegende-karte-bemerken).

Eine einzelne Karte lässt sich mit `ignore_card_removal_action: true` in ihrem Eintrag in `cards.yaml` von der Aktion beim
Wegnehmen ausnehmen (nützlich für Karten wie „Timer starten“), und `ignore_same_id_delay: true` lässt sie sich wiederholen,
solange sie auf dem Lesegerät liegt (eine „nächstes Lied“-Karte).

## Wo die Karten gespeichert sind

Die Karten stehen in `settings/cards.yaml`, ein Eintrag pro Karte. Die Webseite schreibt sie; du kannst sie auch
bearbeiten. Die Kartennummer muss in Anführungszeichen stehen:

```yaml
'0001':
  action: player.pause
'0002':
  action: player.play_card
  args:
    folder: pfad/zum/ordner
```

Alle Aktionen mit ihren Argumenten listet die laufende Box unter `http://<name>/api/v1/actions` auf. Häufige:
`player.play_card`, `player.play_album`, `audiobooks.play`, `radio.play`, `podcasts.play`, `player.toggle`,
`player.next`, `player.prev`, `player.shuffle`, `player.repeat`, `volume.change_volume`, `system.say_my_ip`,
`hardware.shutdown`.

## Nicht alle Karten funktionieren

Lesegeräte lesen Karten einer Frequenz (125 kHz oder 13,56 MHz), und manche kennen nur bestimmte Kartentypen. Siehe
[RFID-Leser](../hardware/readers.md).
