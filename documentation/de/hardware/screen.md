# Ein Bildschirm an der Box

Ein kleiner Bildschirm (ein Raspberry-Pi-Display, ein HDMI-Bildschirm) kann die Webseite des Players an der Box zeigen,
sodass kein Handy nötig ist. Es ist dieselbe Webseite im Vollbild. Eine reduzierte Ansicht für Kinder ist geplant (siehe
[Plan](../../developers/kiosk.md)); vorerst zeigt der Bildschirm alles, auch die Einstellungen.

## Einschalten

```bash
lauschctl setup kiosk
```

(oder in `lauschctl setup` die Frage „Show the web app full-screen on an attached display“ mit *ja* beantworten). Der Schritt
installiert eine minimale Grafikumgebung (X-Server, den Fenstermanager openbox und den Browser Chromium, keinen vollen
Desktop), meldet sich auf der ersten Konsole selbst an und startet nach dem Hochfahren den Browser im Vollbild. Starte die
Box neu. Ein Raspberry Pi 3 oder besser wird empfohlen; auf einer Zero ist ein Browser langsam.

## Den Bildschirm ausschalten, wenn ihn niemand benutzt

Nach 5 Minuten ohne Berührung wird der Bildschirm dunkel. Eine Berührung schaltet ihn wieder ein, und sie weckt nur den
Bildschirm: In der Webseite wird dadurch nichts gedrückt. Die Musik spielt weiter; nur der Bildschirm schläft. Das spart
Strom und schont den Bildschirm bei einer Box, die den ganzen Tag läuft.

Die Zeit änderst du auf der Webseite unter Einstellungen → System → *Switch the screen off after (minutes)*; bei `0`
bleibt der Bildschirm an. Die Änderung gilt sofort. Das geht bei Bildschirmen, deren Hintergrundbeleuchtung Lauschkiste
steuern darf, etwa dem offiziellen Raspberry-Pi-Touch-Display. Die meisten HDMI-Bildschirme haben das nicht und bleiben an.

Die Aktionen `display.sleep` und `display.wake` schalten den Bildschirm aus und ein, zum Beispiel von einer Karte oder
einer Taste aus.

## Bleibt der Bildschirm schwarz

- Prüfe, ob die Webseite selbst von einem anderen Gerät funktioniert.
- Ein Bildschirm, der durch den Zeitgeber oben ausgeschaltet wurde, sieht auch schwarz aus: Berühre ihn.
- Der Browser heißt auf Raspberry Pi OS bis Bookworm `chromium-browser`, ab Trixie `chromium`. Der Schritt wählt den
  richtigen; führ ihn nach einem Systemupdate noch einmal aus.
- Führ `lauschctl setup --check` aus: Es listet auf, was am Kiosk nicht stimmt.
- Ein Touchscreen funktioniert wie eine Maus. Ist die Berührung gespiegelt oder gedreht, ist das eine Einstellung des
  Display-Treibers, nicht von Lauschkiste.

## Ausschalten

`lauschctl uninstall` entfernt die Kiosk-Einträge. Willst du ihn nur ausschalten, entferne die Zeile, die Chromium startet,
aus `/etc/xdg/openbox/autostart`, und die Konsolen-Anmeldung in `/etc/systemd/system/getty@tty1.service.d/autologin.conf`.
