# Telegram Inline-Buttons funktionieren nicht

## Problem
Der Bot (evelynator_bot) kann **keine Inline-Buttons (Inline-Keyboards)** an Nutzer ausliefern. Die Config ist korrekt gesetzt, aber die API liefert die Buttons nicht aus.

## Status
- ✅ `channels.telegram.capabilities.inlineButtons = "dm"` ist korrekt in der Config gesetzt
- ❌ Buttons kommen trotzdem nicht beim iOS/Weg-Client an
- ❌ Nachrichten mit Buttons werden nur als Text gesendet (deliveryKind=text)

## Log-Evidenz
Im Log erscheint:
```
fetch fallback: primary connection path failed; trying alternative Telegram API IP
(codes=none, reason=request-timeout)
```

Und nach dem Config-Hot-Reload:
```
⚠️ 🔌 Gateway: channels.telegram.capabilities failed
```

## Mögliche Ursachen

### 1. Netzwerk-Zeitüberschreitung (wahrscheinlich)
Der Server hat **request-timeout** zur Telegram-API (`api.telegram.org`). Das deutet auf:
- Firewall/Routing-Probleme
- Gedrosselte oder instabile Verbindung zu Telegram
- DNS-Problem auf dem Host

**Check:** `curl -s -o /dev/null -w "%{http_code}" https://api.telegram.org/bot<TOKEN>/getMe` von der Host-Maschine aus

### 2. Lösung: apiRoot setzen
Falls die direkte Verbindung zu `api.telegram.org` blockiert ist, kann ein **selbst-gehosteter Telegram Bot API Server** (tdlib) oder ein **alternativer API-Endpunkt** über `channels.telegram.apiRoot` gesetzt werden.

### 3. Lösung: Proxy
Der Telegram-Channel unterstützt Proxy-Konfiguration unter `channels.telegram.proxy`.

## Ansprechpartner
- **Bot:** @evelynator_bot
- **Betroffener User:** Telegram ID 105690365 (Evelyn Angerer-Strubreiter)
- **Config-Pfad:** `/data/.openclaw/openclaw.json` → `channels.telegram.capabilities.inlineButtons`

## Hinweis
Die Config-Änderung (`inlineButtons: "dm"`) kann **nicht über die Gateway-API** geändert werden (protected path). Nur durch **direkte Bearbeitung der JSON-Datei** + Reload/Restart.

---

## Update 2026-08-24 (00:00): Neue Diagnose

**Alter Befund überholt:** Buttons werden inzwischen korrekt **zugestellt** (Inline-Keyboards rendern im Client, Config `inlineButtons: "dm"` aktiv). Das ursprüngliche Netzwerk-Timeout war transient.

**Das eigentliche Problem:** Button-Klicks (`callback_query`) kommen nie beim Gateway/Agenten an.

Live-Test 2026-08-24 00:01:
- Evelyn hat mehrfach Buttons gedrückt (Spielhalle-Nachricht msg 517 + Test msg 510)
- Danach Text „ok" geschickt → Log-Check: **0 Callback-Events** in openclaw-2026-08-23.log und openclaw-2026-08-24.log
- Auch beim Agenten kam kein `callback_data: <value>` Text an (Doku-Verhalten: „Callback clicks not claimed … are passed to the agent as text")
- Gegenprobe: Eine **Nachrichten-Reaktion** (❤) wurde gleichzeitig korrekt zugestellt und verarbeitet → Polling/Inbound funktioniert grundsätzlich, auch für Non-Message-Updates (`message_reaction`)

Code-Check (Version 2026.7.1 / 2d2ddc4):
- Handler existiert: `bot.on("callback_query", …)` in `telegram-ingress-spool-Bp2o1VK_.js`, beantwortet Query via `answerCallbackQuery` und reicht unbeanspruchte Callbacks als Text durch
- `resolveTelegramAllowedUpdates()` = grammY `DEFAULT_UPDATE_TYPES` (+`message_reaction`,+`channel_post`) → enthält `callback_query`

Offene Verdachtsmomente:
1. Stilles Droppen im Ingress (UpdateTracker/Dedupe) vor dem Handler-Dispatch
2. Versions-Bug → **OpenClaw-Update prüfen** (`npm i -g openclaw@latest` bzw. Update-Flow)
3. Telegram-seitig: `getUpdates` mit veraltetem `allowed_updates`-Set (letzter Aufruf gewinnt global)

Workaround bis Fix: Buttons nur als Dekoration nutzen; Interaktion per Text („1"/„2"/„3") oder Bot-Commands.
