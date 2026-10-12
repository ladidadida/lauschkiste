# Unterwegs: die Box öffnet ihr eigenes WLAN

Auf einer Reise, bei der Oma oder im Auto gibt es kein WLAN, das die Box kennt. Mit dem *Hotspot* öffnet die Box dann ein
eigenes WLAN. Du verbindest dein Handy damit und öffnest die Webseite wie gewohnt.

> [!IMPORTANT]
> Der Hotspot ändert, wie die Box das Netzwerk benutzt. Geht etwas schief, verlierst du die Verbindung zur Box und musst die
> SD-Karte in einen Computer stecken, um es zu reparieren. Stell erst sicher, dass sich die Box mit deinem Heim-WLAN
> verbindet, und schalte den Hotspot nicht ein, solange du die Box nur über WLAN erreichst und keinen zweiten Zugang hast
> (Bildschirm und Tastatur oder ein Kabel).

## Einschalten

```bash
lauschctl setup autohotspot
```

Der Schritt braucht ein Raspberry Pi OS mit NetworkManager (die Versionen Bookworm und Trixie). Er fragt nach einem Namen,
einem Passwort und einer Adresse für den Hotspot. Vorgaben:

| | Vorgabe |
| --- | --- |
| Name (SSID) | `Lauschkiste_<Name der Box>` |
| Passwort | `PlayItLoud!` (ändere es) |
| Adresse der Box | `10.0.0.1` |

## Benutzen

Findet die Box kein bekanntes WLAN (auch nach einem Neustart), öffnet sie nach kurzer Zeit den Hotspot. Verbinde dein Handy
mit dem Passwort und öffne `http://10.0.0.1`. Zu Hause verbindet sich die Box wieder von selbst mit deinem WLAN.

## Ein neues WLAN hinzufügen

Verbinde dich mit dem Hotspot, melde dich per SSH an der Box an (`ssh <benutzer>@10.0.0.1`) und füge das WLAN mit
`sudo raspi-config` hinzu (*System Options → Wireless LAN*).

## Ausschalten

```bash
sudo systemctl disable --now autohotspot.timer
```

Ohne ihn ist die Box nicht mehr erreichbar, wenn kein bekanntes WLAN in der Nähe ist.

## Wenn es nicht funktioniert

```bash
sudo systemctl status autohotspot.service
sudo journalctl -u autohotspot.service -n 50
```

Verbindet sich die Box nicht mit deinem Heim-WLAN, fällt sie auf den Hotspot zurück, damit du noch einen Zugang hast.
Prüfe dann die WLAN-Einstellungen.
