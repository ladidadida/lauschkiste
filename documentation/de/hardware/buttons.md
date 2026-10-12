# Tasten und Drehregler

Tasten, Drehregler und eine LED lassen die Box ohne die Webseite bedienen: Lautstärke, Weiter, Pause. Alles, was eine Taste
tut, ist eine *Aktion*, dieselben Aktionen, die Karten benutzen ([Karten](../using/cards.md)).

## Tasten an den Pins (GPIO)

Tasten, Drehregler und eine Status-LED an den Pins des Pi sind das Plugin *Tasten, Drehregler, LED* (`gpio_controls`).
Schalte es unter Einstellungen → Plugins ein; die Webseite installiert, was es braucht. Richte dort dann die Tasten ein. Du
wählst Pins aus der Liste der freien Pins, und Einstellungen → Hardware zeigt, welcher Pin wofür benutzt wird.

In der Einstellungsdatei sieht das so aus:

```yaml
plugins:
  gpio_controls:
    buttons:
      next:
        pin: GPIO5                  # so, wie die Platine ihn nennt; beim Pi auch 5 oder pin29
        on_press: {action: player.next}
      play:
        pin: GPIO6
        on_press: {action: player.toggle}
        on_hold: {action: hardware.shutdown}
        hold_time: 3                # Sekunden für on_hold
        pull_up: true               # die Taste verbindet den Pin mit Masse
    rotary_encoders:
      volume:
        pin_a: GPIO17
        pin_b: GPIO27
        clockwise: {action: volume.change_volume, args: {step: 2}}
        counter_clockwise: {action: volume.change_volume, args: {step: -2}}
    status_led: GPIO25              # an, solange Lauschkiste läuft
```

Mit `on_hold` löst ein kurzer Druck `on_press` beim Loslassen aus, ein langer nur `on_hold`. Eine Taste, deren Pin schon von
etwas anderem belegt ist, wird übersprungen (das Log sagt es), die übrigen funktionieren weiter.

## USB-Taster, Joysticks und Tastaturen

Jedes Gerät, das Linux als Eingabegerät sieht, kann Aktionen auslösen: USB-Taster, ein Joystick, eine Tastatur, auch ein
Gamecontroller. Ordne die Tasten in den Einstellungen zu:

```yaml
input:
  devices:
    joystick:
      device_name: DragonRise Inc.   Generic   USB
      exact: false                 # false: der Name muss nur enthalten sein
      keys:
        BTN_TRIGGER: {action: player.toggle}
        BTN_THUMB: {action: player.next}
        BTN_TOP: {action: volume.change_volume, args: {step: 5}}
```

Den Namen des Geräts und seine Tasten findest du, indem du auf der Box `python -m evdev.evtest` ausführst und die Tasten
drückst. Die Namen sind `KEY_*` oder `BTN_*`; Zahlen gehen auch. Der Benutzer, unter dem Lauschkiste läuft, muss in der
Gruppe `input` sein. Ein später angestecktes Gerät wird von selbst gefunden.

Die Tasten von Bluetooth-Kopfhörern funktionieren mit `input.media_keys: true`, siehe [Ton und Bluetooth](../using/sound.md).
