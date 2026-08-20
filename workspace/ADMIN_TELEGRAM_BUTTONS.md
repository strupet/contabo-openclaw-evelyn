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
