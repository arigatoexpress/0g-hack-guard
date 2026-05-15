# Telegram MIRA Opt-In Integration

`guard0.telegram_subscriptions` is a local-only registry slice for Telegram
opt-in. It does not import the live Telegram bot, send messages, call Telegram,
read environment variables, or persist secrets.

## Public API

```python
from guard0.telegram_subscriptions import (
    build_opt_in_record,
    build_telegram_registration_challenge,
    ensure_registration_token_not_replayed,
    public_opt_in_status,
    verify_telegram_registration_token,
)

challenge = build_telegram_registration_challenge(
    user_label="operator@example.com",
    secret=app_secret,
)

verified = verify_telegram_registration_token(
    token=challenge["token"],
    secret=app_secret,
)

verified = ensure_registration_token_not_replayed(
    verified,
    consumed_token_ids=already_consumed_token_ids,
)

record = build_opt_in_record(
    verified,
    telegram_user={"id": 123456789, "chat_id": "-1001234567890", "username": "operator"},
    scopes=["mira_alerts"],
)

public_status = public_opt_in_status(record)
```

## Flask Routes

The workbench exposes a demo-safe API surface:

| Method | Route | Behavior |
|---|---|---|
| `GET` | `/telegram` | Mobile-first Telegram Mini App shell. Works inside Telegram or as browser preview. |
| `GET` | `/api/telegram/status` | Reports registration, Mini App auth, Mira preview, and no-send safety posture. |
| `POST` | `/api/telegram/registrations` | Creates a local HMAC challenge and optional `start_payload`. No Telegram send. |
| `POST` | `/api/telegram/opt-ins` | Consumes a token/token id and creates a redacted opt-in record. |
| `POST` | `/api/telegram/webapp/verify` | Validates Telegram Mini App `initData` with `TELEGRAM_BOT_TOKEN`. |
| `GET` | `/api/telegram/miniapp/contract` | Returns required Mini App selectors, routes, Telegram Web App posture, and no-send safety. |
| `POST` | `/api/telegram/miniapp/session` | Detects browser preview versus Telegram launch and validates raw `initData` when present. |
| `POST` | `/api/telegram/miniapp/preview` | Builds one combined wallet-alert + Mira preview response for the Mini App. |
| `POST` | `/api/telegram/webhook` | Handles inbound `/start`, `/stop`, and Mira preview after secret-header verification. |
| `POST` | `/api/telegram/mira-preview` | Builds a deterministic Mira policy response preview. No Telegram send. |
| `POST` | `/api/telegram/wallet-alert-preview` | Builds a no-send wallet alert message preview with score, dedupe, cooldown, and source ids. |

For a real Telegram Mini App, send the raw
`window.Telegram.WebApp.initData` string to `/api/telegram/webapp/verify`.
The backend validates the HMAC signature before trusting the user identity.
Telegram's Mini App docs explicitly warn that `initDataUnsafe` is not trusted
until the raw `initData` is validated server-side:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

## Mini App Flow

The `/telegram` surface is a real Mini App candidate, not just a deep link to
the desktop workbench. It loads Telegram's `telegram-web-app.js`, calls
`ready()` / `expand()` when the host API is available, and uses the Telegram
Main Button only as a local "Preview alert" trigger. It does not call Telegram
message-delivery APIs from the browser.

Current Cloud Run preview URL:
`https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram`

Current Telegram bot:
`https://t.me/Raris0guardBot`

The intended flow is:

1. BotFather points the Mini App URL to the deployed `/telegram` route.
2. Telegram opens the Mini App and exposes raw `window.Telegram.WebApp.initData`.
3. The frontend POSTs that raw string to `/api/telegram/miniapp/session`.
4. The backend validates the HMAC with `TELEGRAM_BOT_TOKEN`.
5. The user previews a wallet intent through `/api/telegram/miniapp/preview`.
6. The response includes `walletAlert`, `mira`, a Telegram-safe message string,
   quality-gate metadata, and explicit `telegram_send=false`.

BotFather setup values:

- Web App URL: `https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram`
- Short description: `Pre-wallet firewall for AI-agent wallet intents.`
- Description: `0guard previews wallet risk, hack signatures, and Mira explanations before an agent reaches a signer. Preview only; no Telegram sends from the Mini App.`
- Production env is configured on Cloud Run via Secret Manager:
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET_TOKEN`, and
  `TELEGRAM_REGISTRATION_SECRET`. Do not commit or print those values.
- The bot menu button is configured as `Open 0guard` and launches the Mini App.
- The webhook is configured for message updates only and uses Telegram's
  `X-Telegram-Bot-Api-Secret-Token` header. The Flask route remains no-send.

## Production Smoke

Run the live bot/Mini App smoke from the repo root:

```bash
.venv/bin/python scripts/telegram_production_smoke.py --format markdown
```

The script reads the bot token and webhook secret from Secret Manager through
`gcloud` when local env vars are not set. It redacts token/user details and
checks:

- Cloud Run Telegram status and no-send flags.
- Browser-preview Mini App launch posture.
- Synthetic signed Telegram `initData` validation.
- Combined wallet-alert + Mira Mini App preview.
- Bot API readbacks for `getMe`, menu button, commands, and webhook health.
- Webhook route secret-header enforcement without sending Telegram messages.

Opening `/telegram` in a normal browser is still useful for judging and local
QA: it becomes `local_browser_preview`, keeps the same no-send contract, and
does not pretend that a Telegram user has been verified.

## Safety Notes

- Registration tokens are HMAC-SHA256 signed and expire after a bounded TTL.
- Default TTL is 900 seconds; maximum TTL is 3600 seconds.
- The Flask demo uses an ephemeral process-local registration secret unless
  `TELEGRAM_REGISTRATION_SECRET` is configured. Set the env var before using
  challenges across restarts or multiple replicas.
- Tokens are one-time-use by contract. Persist `verified["token_id"]` after
  successful opt-in and pass consumed ids to `ensure_registration_token_not_replayed`.
- `build_opt_in_record` stores Telegram identifiers for local registry use.
- `public_opt_in_status` redacts user labels, Telegram ids, chat ids, usernames,
  first/last names, and token ids before public display.
- No bot token, chat id, or other secret should be committed with this flow.
- Live Telegram sends remain outside this flow and still require
  `scripts/telegram_post.py --live-send-confirm SEND_TO_TELEGRAM_FROM_0GUARD`.
- Webhook handling requires `TELEGRAM_WEBHOOK_SECRET_TOKEN` and checks the
  `X-Telegram-Bot-Api-Secret-Token` header. The app does not call
  `setWebhook`; webhook registration remains an explicit operator action.

## Wallet Alert Quality Gate

`guard0.wallet_alerts` adds the Telegram Mini App alert layer. It validates an
EVM address, evaluates the current intent, attaches source/detector evidence,
and returns only high-signal direct wallet alerts. Emerging detector gaps are
kept as digest-only notes until a matching intent, calldata pattern, or source
signal makes them wallet-specific.

The quality policy requires direct wallet relevance, a source or detector id,
a dedupe key, cooldowns, and opt-in scope before a future live bot could send.
The current Flask and workbench routes always return `preview_no_send`.

## Mira Add-On Boundary

The current Mira integration is deterministic and local: `guard0.mira` turns a
0guard policy decision into a Telegram-safe explanation with no external LLM
call. That is deliberate for the hackathon submission because it is verifiable
and does not depend on a third-party key. A future external Mira adapter should
sit behind the same contract and keep the current fields:

- `schema="0guard.mira_preview.v1"`
- `delivery="preview_no_send"` until live sends are explicitly enabled
- `telegram_send=false` unless the separate live-send CLI path is reviewed
- `network_calls` truthfully set to the actual runtime behavior
