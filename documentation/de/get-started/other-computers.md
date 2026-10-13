# Auf PC, Laptop oder Mini-PC

Lauschkiste ist nicht an den Raspberry Pi gebunden. Es läuft auf jedem 64-Bit-PC (x64) mit Linux. So wird aus Dingen, die
du vielleicht schon hast, eine Box:

- ein **alter Laptop**, der Bildschirm, Tastatur, Lautsprecher und Akku gleich mitbringt,
- ein **Mini-PC** (neu oder gebraucht), klein, leise und gebraucht oft günstig,
- dein **Arbeitsrechner**, um Lauschkiste auszuprobieren, bevor du etwas kaufst oder baust.

## Was geht

Alles, was keine Pi-Hardware braucht: die Webseite, die Bibliothek, Radio, Podcasts, Hörbücher, Zeitlimits, Bluetooth und
RFID-Leser, die per USB angeschlossen werden. Es fehlen die Teile, die an die Pins und die Startkonfiguration des Pi
gebunden sind: Leser und Soundkarten, die du an die GPIO-Leiste verdrahtest, das pHAT BEAT, der OnOff SHIM und Ähnliches.
`lauschctl setup` fragt zuerst *What kind of machine is this?* („Welche Art Maschine ist das?“) und lässt die Fragen weg, die zur Antwort nicht passen.

Der Ton kommt aus dem, was der Computer hat: seinen Lautsprechern, einer Kopfhörerbuchse, einem USB-Lautsprecher oder
Bluetooth.

## Installieren

Du brauchst ein Linux auf Debian- oder Ubuntu-Basis (Debian, Ubuntu, Linux Mint und ähnliche). Dann sind die Schritte die
von [Installieren](install.md), nur ohne SD-Karte:

1. Installiere das Linux wie gewohnt auf dem Computer (eine Server- oder Minimalinstallation genügt, ein Desktop ist auch
   in Ordnung).
2. Öffne dort ein Terminal oder melde dich per `ssh` an und füge die Installationszeile aus
   [Installieren](install.md#3-installieren) ein.
3. Führ `lauschctl setup` aus. Die erste Frage ist *What kind of machine is this?* („Welche Art Maschine ist das?“). Für einen
   Computer gibt es zwei Antworten:
   - *PC or laptop, just trying it out* („PC oder Laptop, nur zum Ausprobieren“): Außerhalb von Lauschkiste wird nichts am
     System verändert, kein Port 80, kein Samba, keine Änderung an Anmeldung oder Start, kein Kiosk, kein Upgrade. Auf einem
     Computer, der kein Pi ist, ist das vorgewählt. Das ist die richtige Wahl für deinen Arbeitsrechner.
   - *PC, laptop or mini PC as a box of its own* („PC, Laptop oder Mini-PC als eigene Box“): für einen Computer, der eine
     Lauschkiste ist. Das Setup darf dann Port 80, Samba, eine Login-Meldung, ein System-Upgrade, den WLAN-Hotspot und den
     Kiosk-Bildschirm anbieten (dafür richtet es auch die Konsolen-Anmeldung ein).

   Die übrigen Antworten auf einem Computer:
   - *Start Lauschkiste at boot* ist bei einem Test standardmäßig *Nein*; für eine Box, die von selbst startet, antworte *Ja*.
   - Danach kommen die Fragen zu dem, was angeschlossen ist (ein USB-Leser braucht nichts; antworte bei
     *Configure an RFID reader now* mit *Ja*).
4. Öffne `http://<name>.local` oder `http://<IP-Adresse>:5556` vom Handy oder vom selben Computer aus.

Bei einem anderen Linux (Fedora, Arch, ...) warnt der Installer nur: Installiere Python 3 mit Header-Dateien, einen
C-Compiler, `curl`, die PortAudio-Bibliothek und `alsa-utils` vorher selbst.

## Windows und macOS

Für sie gibt es noch keinen Installer. Um Lauschkiste auf einem Arbeitsrechner mit Windows oder macOS auszuprobieren,
nimm ein Linux in einer virtuellen Maschine; der Ton aus einer virtuellen Maschine braucht etwas Sorgfalt, beurteile also
die Klangqualität nicht danach.

## Was getestet ist

Die Entwicklung läuft auf einem x64-Linux, und jede Änderung installiert die Pakete in einer frischen Umgebung auf x64 und
startet sie. Einen Computer so als Alltagsbox für Kinder zu betreiben, mit RFID-Leser und allem, ist weniger getestet als
der Pi: Sag uns, was du erlebst.

Weiter: [Installieren](install.md).
