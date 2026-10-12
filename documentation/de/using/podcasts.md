# Podcasts

Ein Podcast ist ein Feed im Internet, der neue Folgen bekommt. Die Box streamt die Folgen; zum Abspielen braucht sie also
Internet, außer du lädst sie herunter.

## Abonnieren

Öffne in der Bibliothek **Podcasts** und tippe auf **Podcast abonnieren**:

- **Suchen.** Mit dem Plugin *Podcast-Verzeichnisse* (Einstellungen → Plugins) durchsucht der Dialog Apple Podcasts,
  fyyd (ein deutsches Verzeichnis) und, mit einem kostenlosen Schlüssel, Podcast Index. Tippe einen Namen ein oder lass das
  Feld leer, um die beliebten zu sehen, und abonniere mit einem Tipp. Jedes Verzeichnis hat in den Einstellungen des
  Plugins einen Schalter; was du eintippst, geht an die eingeschalteten Verzeichnisse.
- **Per Adresse.** Kennst du die Adresse des Feeds, nimm *Per Adresse hinzufügen*.

Jede Folge macht dort weiter, wo sie aufgehört hat, und gilt als gehört, sobald sie bis zum Ende gespielt wurde.

## Auf einer Karte

Spiel eine Folge ab und tippe im Player auf das Karten-Symbol, oder wähle beim Registrieren in der Kartenliste *Podcast
abspielen*. Ohne Folge spielt die Karte die neueste noch nicht gehörte Folge (oder die neueste, wenn alle gehört sind).
Mit einer gewählten Folge spielt sie immer diese.

## Folgen herunterladen

Das Menü einer Folge hat **Auf die Box laden**. Eine heruntergeladene Folge spielt ohne Internet und macht dort weiter,
wo du sie angehalten hast. Downloads teilen sich die Platzeinstellungen unter Einstellungen → Bibliothek → Cache; ist
*Alte entfernen* an, werden bei vollem Speicher zuerst gehörte Folgen gelöscht. Wer einen Podcast abbestellt, entfernt auch
seine heruntergeladenen Folgen.

## Von und zu anderen Apps

Das Menü neben *Podcast abonnieren* importiert und exportiert eine **OPML-Datei**, das Listenformat der Podcast-Apps. Um
von AntennaPod umzuziehen, exportiere dort deine Abos (Einstellungen → Import/Export → OPML-Export) und wähle *Aus OPML-Datei
importieren*. Podcasts, denen du schon folgst, werden übersprungen.

## Einstellungen

| Einstellung | Bedeutung | Standard |
| --- | --- | --- |
| `podcasts.refresh_minutes` | einen Feed neu laden, wenn seine Folgen älter sind | 60 |
| `podcasts.max_episodes` | gespeicherte Folgen pro Podcast | 100 |
| `podcasts.rewind_sec` | so weit beim Fortsetzen zurückgehen | 10 |
