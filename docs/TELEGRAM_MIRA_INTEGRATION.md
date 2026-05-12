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
| `GET` | `/api/telegram/status` | Reports registration, Mini App auth, Mira preview, and no-send safety posture. |
| `POST` | `/api/telegram/registrations` | Creates a local HMAC challenge and optional `start_payload`. No Telegram send. |
| `POST` | `/api/telegram/opt-ins` | Consumes a token/token id and creates a redacted opt-in record. |
| `POST` | `/api/telegram/webapp/verify` | Validates Telegram Mini App `initData` with `TELEGRAM_BOT_TOKEN`. |
| `POST` | `/api/telegram/webhook` | Handles inbound `/start`, `/stop`, and Mira preview after secret-header verification. |
| `POST` | `/api/telegram/mira-preview` | Builds a deterministic Mira policy response preview. No Telegram send. |

For a real Telegram Mini App, send the raw
`window.Telegram.WebApp.initData` string to `/api/telegram/webapp/verify`.
The backend validates the HMAC signature before trusting the user identity.
Telegram's Mini App docs explicitly warn that `initDataUnsafe` is not trusted
until the raw `initData` is validated server-side:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

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
