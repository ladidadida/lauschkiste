# Ein-Aus-Taste und Akku

> Beide Teile beschreiben Hardware, die in diesem Projekt **noch nicht an echter Hardware getestet** wurde.

## Ein-Aus-Taste (Pimoroni OnOff SHIM)

Das OnOff SHIM schaltet den Pi mit einem Tastendruck ein, fährt ihn mit dem nächsten sauber herunter und trennt dann den
Strom. In Lauschkiste ist es das Plugin *Ein-Aus-Taste* mit der Vorgabe *Pimoroni OnOff SHIM* (Taste an GPIO17,
Abschalten über GPIO4). Ein Pimoroni-Skript ist nicht nötig.

1. Antworte in `lauschctl setup` auf „Is a power button attached“ mit *ja* (oder schalte das Plugin unter
   Einstellungen → Plugins ein und starte neu).
2. `lauschctl setup raspi`, dann Neustart. Das fügt `dtoverlay=gpio-poweroff,gpiopin=4,active_low=1` zur
   Startkonfiguration hinzu, was den Strom trennt, sobald das System angehalten ist.

Ein Druck fährt Lauschkiste herunter wie eine Ausschalt-Karte: Die Wiedergabe stoppt, die Positionen werden gespeichert, der
Abschaltton spielt, dann hält der Pi an und das SHIM schaltet ihn aus. Andere Ein-Aus-Taster funktionieren genauso mit der
Hardware *Eigene Pins*.

### Das SHIM getrennt verdrahten

Das SHIM hat einen 12-poligen Header, der gelötet werden muss. Um Pins für anderes zu sparen, kannst du es getrennt
verdrahten:

| Name auf der Platine | Pin der Platine | Pin am Raspberry Pi | Name |
| --- | --- | --- | --- |
| 3.3V | 1 | 1, 17 | 3V3 |
| 5V | 2 | 2 | 5V |
| 5V | 4 | 4 | 5V |
| GND | 6 | 6, 9, 20, 25 | Masse |
| GPLCLK0 | 7 | 7 | GPIO4 |
| GPIO17 | 11 | 11 | GPIO17 |

Mehr unter [pinout.xyz](https://pinout.xyz/pinout/onoff_shim).

## Akkuüberwachung

Das Plugin *Akku* liest einen Akkusensor an I²C, zeigt den Ladestand unter Einstellungen → Status, führt eine Aktion aus, wenn
der Akku schwach wird (zum Beispiel einen Warnton), und fährt die Box sauber herunter, bevor er leer ist. Beantworte die Frage
nach einer Akkuüberwachung in `lauschctl setup`; der Pi schaltet I²C ein (`lauschctl setup raspi`, dann Neustart).

| Treiber | Sensor | Ladestand aus |
| --- | --- | --- |
| `max17048` | MAX17048-Ladestandsmesser (Adafruit-, SparkFun-LiPo-Platinen), Adresse 0x36 | dem Messer |
| `ina219` | INA219-Strom- und Spannungssensor | der Spannung (`empty_voltage` bis `full_voltage`) |
| `simulator` | keiner, entlädt sich langsam | der Spannung |

```yaml
plugins:
  battery:
    driver: max17048
    i2c_bus: 1                 # SDA ist GPIO2, SCL GPIO3
    warning_voltage: 3300      # Millivolt: führt warning_action einmal aus
    shutdown_voltage: 3000     # Millivolt: fährt die Box herunter
    warning_action: {action: jingle.play, args: {sound: /pfad/zu/akku-schwach.wav}}
```
