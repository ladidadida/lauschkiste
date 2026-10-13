# Hörbücher

Hörbücher sind Ordner in `library/audiobooks`, ein Ordner pro Buch ([Musik und Bibliothek](music.md)). Die Dateien sind
die Kapitel und werden in der Reihenfolge ihrer Namen gespielt (`2.mp3` vor `10.mp3`).

Ein Buch **macht dort weiter, wo es aufgehört hat**, ein paar Sekunden früher, damit man wieder hineinfindet. Die
Position wird beim Abspielen, beim Pausieren und beim Herunterfahren der Box gespeichert. Hat das letzte Kapitel bis zum
Ende gespielt, gilt das Buch als beendet und beginnt beim nächsten Mal von vorn. Kapitel laufen immer der Reihe nach,
egal was bei „zufällig“ und „wiederholen“ eingestellt ist.

## Auf einer Karte

Spiel das Buch ab und tippe im Player auf das Karten-Symbol, wie in [Deine erste Karte](../get-started/first-card.md),
oder wähle beim Registrieren in der Kartenliste *Hörbuch abspielen*. Wird die Karte des Buchs aufgelegt, das schon läuft,
ändert sich nichts; ein pausiertes Buch geht weiter. Mit einem Lesegerät, das die aufliegende Karte bemerkt, pausiert das
Wegnehmen der Karte, und das Wiederauflegen setzt fort ([Karten](cards.md#karten-die-auf-der-box-liegen-bleiben)).

Weitere Aktionen für Karten: `audiobooks.restart` (von vorn) und `audiobooks.set_finished` (als beendet markieren oder
nicht).

Wie weit ein Buch beim Fortsetzen zurückgeht, steht in `audiobooks.rewind_sec` (standardmäßig 10 Sekunden).

## Audiobookshelf

Das Plugin *Audiobookshelf* zeigt die Bücher eines [Audiobookshelf](https://www.audiobookshelf.org)-Servers neben den
lokalen und spielt sie vom Server. Die Position liegt auf dem Server: Ein Buch, das in der Audiobookshelf-App angefangen
wurde, geht auf der Box weiter und umgekehrt.

1. Erzeuge in Audiobookshelf einen API-Schlüssel (Einstellungen → API Keys) für den Benutzer, den die Box verwenden soll.
2. Öffne auf der Webseite Einstellungen → Plugins, schalte *Audiobookshelf* ein und trage die Adresse des Servers und den
   Schlüssel ein. Der Schlüssel liegt in einer Datei, die nur der Benutzer der Box lesen kann, und wird nie wieder
   angezeigt.
3. Die Bücher erscheinen unter Hörbücher. Auf einer Karte funktionieren sie wie lokale Bücher.

Ein Buch, das nicht heruntergeladen ist, braucht zum Abspielen den Server.

### Bücher herunterladen

Das Menü eines Audiobookshelf-Buchs hat **Auf die Box laden**. Die Dateien liegen in `cache/audiobookshelf` im
Lauschkiste-Home. Ein heruntergeladenes Buch spielt von der Box, auch wenn der Server da ist. Während etwas spielt, wird
der Download gebremst, damit der Ton nie stockt. Einstellungen → Bibliothek → Cache legt den Platz für alle Downloads fest
(standardmäßig 8 GB). Ist er voll und *Alte entfernen* an, werden die ältesten beendeten Downloads gelöscht; Bücher, die
gerade gehört werden, nie. Hat der Server ein Buch nach dem Download geändert, sagt die Liste das, und *Erneut laden*
holt die neue Fassung.

### Wenn der Server weg ist

Die Box spielt weiter: Die Bücherliste bleibt erhalten, heruntergeladene Bücher stehen oben, und die Position wird auf der
Box gespeichert und an den Server geschickt, sobald er wieder da ist. Wurde ein Buch zwischendurch auch woanders gehört,
gewinnt die weitere Position, und ein beendetes Buch bleibt beendet.
