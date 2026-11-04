# value-investor-skill

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md)

## Ist diese Aktie ihren aktuellen Kurs wert?

Untersuche das Geschäft, prüfe die Bewertungsannahmen und sieh, was der Kurs voraussetzt. Ein Recherche-Skill für deinen KI-Assistenten, veröffentlicht von **[AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=de_methodology)**.

[Demo im Browser ausprobieren](https://ahasignals.com/value-investor-skill/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=de_demo) · [Vorher-nachher-Beispiel](docs/demo.md) · [MIT-Lizenz](LICENSE)

![Eine fiktive Aktie zu 40 Dollar: gleicher Kurs, unterschiedliche Annahmen](assets/demo.svg)

### Mit Claude, GPT, DeepSeek, Grok, Gemini oder Kimi starten

Füge die [kopierfertigen Recherche-Anweisungen](prompts/START_HERE.md) in Claude, ChatGPT, DeepSeek, Grok, Gemini oder Kimi ein und bitte um eine Antwort auf Deutsch. Kein Terminal nötig. Für Claude Code gibt es ein Plugin, für Codex eine lokale Installation. [Anleitung nach App](docs/hosts.md). Welche Werkzeuge ausgeführt werden können, hängt von deiner App ab.

### In einer Minute ausprobieren

Python 3.9 oder neuer. Für diese **fiktive Offline-Demo** brauchst du keine pip-Pakete, API-Schlüssel, kostenpflichtigen Marktdaten oder Modellaufrufe.

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/investor.py demo --out output/demo
```

Öffne `output/demo/before/research.html` und `output/demo/after/research.html`. Unter Windows kannst du `py -3` statt `python3` verwenden. Für einen weiteren Durchlauf wählst du ein neues Ausgabeverzeichnis. Vorhandene Forschungsaufzeichnungen werden nicht überschrieben.

### Skill installieren

```bash
python3 scripts/install.py --host codex
# Claude Code:
python3 scripts/install.py --host claude
```

Lade die Skills deines Assistenten neu und frage:

> Nutze value-investor-skill, um dieses Unternehmen anhand von Primärquellen zu untersuchen. Erkläre auf Deutsch, welche Annahmen den aktuellen Kurs rechtfertigen, welche Belege sie stützen und welche Gegenbelege die Einschätzung ändern würden. Erfinde keine fehlenden Daten.

Dein Assistent benötigt Quellenzugriff oder von dir bereitgestellte Dokumente. Kosten und Nutzungsbedingungen des KI-Hosts und der Datenanbieter gelten weiterhin. Der Installer überschreibt keine vorhandene Installation.

### Was setzt ein Kurs von 40 Dollar voraus?

Die folgenden Werte sind fiktive Barwertannahmen je Aktie.

| Günstiges Szenario | Ungünstiges Szenario | Gewicht des günstigen Szenarios, das 40 Dollar ergibt |
| ---: | ---: | ---: |
| 80 Dollar | 20 Dollar | 33,3 % |
| 60 Dollar | 20 Dollar | 50,0 % |

Jede Zeile ist eine eigene Zwei-Zustands-Rechnung. **Diese Gewichte sind weder Ereigniswahrscheinlichkeiten noch ein Konfidenzintervall.** Die nächste Frage lautet: Welche Belege stützen 80 statt 60 Dollar?

Wird in der Demo der Beleg für den angenommenen Markteinführungszeitpunkt zurückgezogen, erhalten die davon abhängigen Werte den Status `NEEDS_REVIEW`. Neue Zahlen werden zurückgehalten. Die ursprüngliche Untersuchung und nicht betroffene Szenarien bleiben erhalten.

### Was AhaSignals einbringt

- Marktpreis und Szenarioökonomie bleiben getrennt. Ein anderer Kurs ändert nicht die eingegebenen Unternehmenswerte.
- Veröffentlichungs- und Beobachtungszeitpunkt werden unterschieden; Abhängigkeiten von Quellen bleiben sichtbar.
- Barmittel, Schulden, künftige Kosten, neues Kapital und neue Aktien fließen gemeinsam in die Berechnung je Aktie ein.
- Überarbeitungen erzeugen neue Versionen, ohne frühere Einschätzungen zu überschreiben.
- Ohne validierte Wahrscheinlichkeit bleibt der Status `NOT_ESTIMATED`; eine Anlageempfehlung wird nicht ausgegeben (`NO_QUOTE`).

Diese Version bietet Szenariorechnungen und Forschungsaufzeichnungen. Sie liefert keine automatische Analyse des gesamten Aktienmarkts, keine kalibrierten Prognosen, keine persönliche Anlageberatung und keine Handelsausführung. Eingegebene Quelldaten werden strukturell geprüft, nicht automatisch auf ihren Wahrheitsgehalt authentifiziert.

### Weiterforschen

[Eingabeformat](references/input-contract.md) · [Forschungsverfahren](references/research-protocol.md) · [Quellen und Überarbeitungen bei AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=de_methodology) · [Übersetzung korrigieren](https://github.com/AhaSignals/value-investor-skill/issues)

Dies ist eine deutschsprachige Einführung. CLI, erzeugte Berichte und die technische Spezifikation sind auf Englisch. Die Sprache der KI-Antwort hängt vom Host ab. Hinweise zur Übersetzung sind willkommen.

AhaSignals ist ein unabhängiger Herausgeber von Forschungsinhalten. Nur für Forschung und Bildung, keine Anlage- oder Handelsempfehlung. Namen Dritter dienen der Quellen- oder Kompatibilitätsangabe und bedeuten keine Verbindung oder Unterstützung. Code und eigene fiktive Daten stehen unter MIT; Rechte an fremden Quelldokumenten werden nicht eingeräumt.
