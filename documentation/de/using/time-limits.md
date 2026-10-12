# Zeitlimits

Lauschkiste kann das Hören in Grenzen halten: **Ruhezeiten**, in denen nichts spielt, und eine **tägliche Hörzeit**. Es ist
aus, bis du es einschaltest: Einstellungen → Wiedergabe und Audio → Zeitlimits → *Zeitlimits verwenden*.

## Ruhezeiten

Eine Liste von Zeiten, in denen nichts spielt, jeweils mit Anfang, Ende und den Tagen, für die sie gilt (jeden Tag, Montag
bis Freitag, Samstag und Sonntag). Der Standardeintrag ist die Nacht von 19:30 bis 07:00. Ein Eintrag, der über Mitternacht
geht, gehört zu dem Tag, an dem er beginnt: „Montag bis Freitag“ gilt von Freitagabend bis Samstagmorgen, aber nicht für
den Samstagabend.

Was in der Ruhezeit gestartet wird, hört sofort auf, und der Player zeigt „Ruhezeit bis 07:00“.

## Tägliche Hörzeit

Die Minuten, in denen etwas spielt, werden pro Tag gezählt (Pausieren zählt nicht) und beginnen um Mitternacht neu.

| Einstellung | Bedeutung | Standard |
| --- | --- | --- |
| `daily_limit_minutes` | die Grenze pro Tag, 0 für keine | 120 |
| `weekend_limit_minutes` | eine andere Grenze für Samstag und Sonntag | keine |
| `warn_minutes` | ein Warnton so lange vor dem Ende, 0 für keinen | 5 |
| `fade_seconds` | der Ton blendet über diese Zeit aus, wenn die Grenze erreicht ist | |

Ist die Zeit aufgebraucht, blendet der Ton aus und der Player hält an. Spielt man am selben Tag noch einmal, hört es sofort
wieder auf.

## Extra-Zeit für Erwachsene

Die Aktion `time_limits.allow` gibt für heute Minuten dazu und hebt die Ruhezeit für diese Zeit auf. Du rufst sie auf der
Webseite auf oder registrierst eine Karte mit der Aktion `time_limits.allow` und dem Argument `minutes` (zum Beispiel 30)
und bewahrst sie dort auf, wo die Kinder sie nicht finden. `time_limits.reset_today` zählt den Tag von null.

## Was es nicht kann

- **Es ist keine Sperre.** Wer die Webseite öffnen kann oder die Karte kennt, kann Zeit hinzufügen oder die Limits
  ausschalten. Es hilft bei Absprachen in der Familie; ein entschlossenes Kind hält es nicht auf.
- **Es braucht die richtige Uhrzeit.** Die Box hat keine eigene Uhr und bezieht die Zeit aus dem Netzwerk. Ist die Zeit nicht
  synchronisiert (zum Beispiel im Auto ohne WLAN), gelten Ruhezeiten *nicht*, weil man der Zeit nicht trauen kann; der
  Player sagt das. Die tägliche Hörzeit zählt Spielzeit und funktioniert auch ohne Uhr.
