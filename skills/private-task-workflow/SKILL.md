---
name: private-task-workflow
version: 1.0.0
description: |
  Workflow für private Aufgaben per Sprache/Text: Vorschlag → Bestätigung → 
  in Google Tasks speichern → Link senden. Nur für privates Umfeld.
triggers:
  - "Task"
  - "Aufgabe"
  - "Erinner mich"
  - "Termin Workflow privat"
tools:
  - exec
  - read
mutating: true
---

# Private Task Workflow

## Ziel
Evelyn kann private Aufgaben (nicht beruflich) per Sprachnachricht oder Text an den Agenten geben.
Der Agent macht einen Vorschlag (Liste, Titel, Fälligkeit) und speichert den Task erst NACH Bestätigung.
Nach dem Speichern wird der Link zum Task mitgeschickt.

## Voraussetzungen
- Zugriff auf Google Tasks (gog CLI mit Evelyns Account)
- Kenntnis der Task-Listen (siehe unten)

## Task-Listen

| Liste | ID |
|-------|----|
| Evelyn | `MTMyMDA1Mzc0ODcyODcyNzUxNzM6MDow` |
| Termine Family u E | `NnRzU2FicmZ6Qk5sSWY3RA` |
| Haus | `V2t0V3N5cUhJM3RQUDhDRA` |
| Einkaufen | `ZlJDaVFRRXZmVUhJTHRwTQ` |
| Inventuren | `MHhrTG41X1BHMmZXWDhwSg` |
| Finance | `TXJKNy1qY3YtdGVwbzR3Ug` |
| Verein | `dV8wZmhIeTZlR1czcVZReg` |
| Reise u Packen | `bjZRYzlNTWs0M0NrdlZ0bg` |

## Workflow

### Schritt 1: Aufgabe erfassen
Evelyn sagt/schreibt eine Aufgabe. Mögliche Formate:
- "Eine Task: [Titel], fällig [Datum], Liste [Liste]"
- "Task: [Titel], heute fällig"
- "Erinner mich an [Titel] bis [Datum]"
- Auch vage Angaben: "Fürs Haus: [Aufgabe], heute"

### Schritt 2: Analysieren & Vorschlag machen
Agent analysiert:
- **Liste**: Welche Task-Liste passt? (z.B. "Haus" bei Haus-Themen, "Einkaufen" bei Einkäufen)
- **Titel**: Präzise Zusammenfassung
- **Fälligkeit**: Heute, morgen, konkretes Datum, oder keine (falls unklar → nachfragen)

Dem User in übersichtlicher Form präsentieren.

### Schritt 3: Bestätigung einholen
Warten auf explizite Bestätigung ("Ja", "Passt", "Bestätigt", "OK", etc.).
Erst bei Bestätigung → Schritt 4.
Bei Korrekturwunsch → Vorschlag anpassen und erneut zeigen.

### Schritt 4: Task speichern (gog)
```bash
XDG_CONFIG_HOME="/data/.openclaw" gog tasks add "<listId>" \
  --title "<titel>" \
  --due <YYYY-MM-DD> \
  --account evelyn.angerer@gmail.com \
  --client personal
```
(Ohne Fälligkeit: `--due` weglassen)

### Schritt 5: Bestätigung + Link senden
Dem User bestätigen und **immer den Link zum Task mitsenden** (von gog als `link` zurückgegeben).

## Output Format
```
✅ **Gespeichert!**
📋 Liste: [Listenname]
📝 Titel: [Titel]
📅 Fällig: [Datum oder "keine"]
🔗 https://tasks.google.com/task/...
```

## Wichtige Regeln
1. **Niemals ohne Bestätigung speichern** – Vorschlag zeigen, auf Ja warten
2. Bei Unklarheit bei der Liste: nachfragen, nicht raten
3. Fälligkeit immer angeben oder explizit sagen "keine Fälligkeit"
4. **Immer den Task-Link mitsenden** nach dem Speichern
5. Nur für PRIVATE Aufgaben – berufliche Odoo-Themen gehören nicht hier rein