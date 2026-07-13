## AlphaClaw Harness

AlphaClaw is the setup and management harness that runs alongside OpenClaw. It provides a web-based Setup UI and manages environment variables, channel connections, Google Workspace integration, and the gateway lifecycle.

AlphaClaw UI: `http://100.112.242.78:8811`

Do not deflect actionable requests to the Setup UI. If a command or tool is available to you (including OpenClaw CLI commands), execute it yourself first; share Setup UI links only as optional guidance or when the user explicitly asks to do it manually.

### Tabs

| Tab       | URL                          | What it helps with                                                                                                                                                                         |
| --------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| General   | `http://100.112.242.78:8811#general`   | Gateway status & restart, channel health (Telegram/Discord), pending pairings, feature health (Embeddings/Audio), Google Workspace connection, repo auto-sync schedule, OpenClaw dashboard |
| Watchdog  | `http://100.112.242.78:8811#watchdog`  | Gateway watchdog lifecycle, crash-loop visibility, restart diagnostics, and auto-repair feature                                                                                            |
| Providers | `http://100.112.242.78:8811#providers` | AI provider credentials (Anthropic, OpenAI, Gemini, Mistral, Voyage, Groq, Deepgram), feature capabilities, Codex OAuth                                                                    |
| Envars    | `http://100.112.242.78:8811#envars`    | View/edit/add environment variables (saved to `/data/.env`), gateway restart to apply changes                                                                                              |
| Webhooks  | `http://100.112.242.78:8811#webhooks`  | Webhook endpoint visibility, create flow, request history, and gateway delivery debugging                                                                                                  |
| Browse    | `http://100.112.242.78:8811#browse`    | File browser and editor rooted at `.openclaw`, markdown preview/edit flow, and git-aware save workflow                                                                                     |

### Environment variables

Changes to env vars are made through the **Envars** tab (`http://100.112.242.78:8811#envars`). After saving, a gateway restart may be required to pick up the changes — the UI prompts for this automatically. Do not edit `/data/.env` directly; use the Setup UI so changes are validated and the gateway restart is handled.

### Persistent storage

This deployment runs in an ephemeral container. `/tmp` and other temp locations do not survive redeploys.

Anything persistent must live under `/data/.openclaw`.

For plugins and local tooling:

- Prefer normal `openclaw plugins install <spec>` flows for durable installs.
- If you need to stage a local plugin or helper files first, put them under `/data/.openclaw/...`, not `/tmp/...`.
- Do not leave durable `plugins.load.paths` entries pointing at temp directories.

### Google Workspace

Google Workspace is connected via the **General** tab (`http://100.112.242.78:8811#general`). The user provides OAuth client credentials from Google Cloud Console, then authorizes access to the services they need (Gmail, Calendar, Drive, Sheets, Docs, Tasks, Contacts, Meet). Connected accounts and `gog` CLI usage are covered by the gog-cli skill.

## Telegram Formatting

- **Links:** Use markdown syntax `[text](URL)` — HTML `<a href>` does NOT render

## Webhooks

You can create webhooks yourself or the user can create them through the AlphaClaw UI.

Webhook transform files must follow this convention:

- Path: hooks/transforms/{hook-name}/{hook-name}-transform.mjs
- Signature: export default async function transform(payload, context)
- Webhook data is at payload.payload (nested)
- Never create transform files outside of hooks/transforms/
- When modifying a transform, read the existing file first


## Available Google Accounts

No Google accounts are currently configured.
