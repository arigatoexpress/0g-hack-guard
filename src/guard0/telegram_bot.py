"""
Telegram Bot Integration — Threat Intel Broadcast
==================================================
Mirrors the X bot to broadcast hack alerts, threads, and summaries
to Telegram channels or groups.

Usage:
    export TELEGRAM_BOT_TOKEN=...
    export TELEGRAM_CHAT_ID=...
    python scripts/telegram_post.py --text "Alert!"
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

import requests

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str
    parse_mode: str = "HTML"
    disable_web_page_preview: bool = True

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            raise RuntimeError(
                "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars. "
                "Get a token from @BotFather on Telegram."
            )
        return cls(bot_token=token, chat_id=chat_id)


class TelegramWebAppAuthError(ValueError):
    """Raised when Telegram Mini App init data is missing, stale, or invalid."""


def parse_webapp_init_data(init_data: str) -> dict[str, Any]:
    """Parse Telegram Mini App initData after validation has succeeded."""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    for key in ("user", "receiver", "chat"):
        if key in parsed:
            try:
                parsed[key] = json.loads(parsed[key])
            except json.JSONDecodeError as exc:
                raise TelegramWebAppAuthError(f"Invalid Telegram initData {key} JSON") from exc
    return parsed


def validate_webapp_init_data(
    init_data: str,
    bot_token: str,
    *,
    max_age_seconds: int = 86_400,
    now: int | None = None,
) -> dict[str, Any]:
    """Validate Telegram Mini App initData using Telegram's HMAC-SHA256 scheme."""
    if not init_data:
        raise TelegramWebAppAuthError("Missing Telegram initData")
    if not bot_token:
        raise TelegramWebAppAuthError("Missing Telegram bot token")

    pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    fields: dict[str, str] = {}
    received_hash = ""
    for key, value in pairs:
        if key == "hash":
            received_hash = value
        else:
            fields[key] = value

    if not received_hash:
        raise TelegramWebAppAuthError("Missing Telegram initData hash")
    if "auth_date" not in fields:
        raise TelegramWebAppAuthError("Missing Telegram initData auth_date")

    try:
        auth_date = int(fields["auth_date"])
    except ValueError as exc:
        raise TelegramWebAppAuthError("Invalid Telegram initData auth_date") from exc

    current_time = int(time.time()) if now is None else now
    if max_age_seconds >= 0 and current_time - auth_date > max_age_seconds:
        raise TelegramWebAppAuthError("Stale Telegram initData")
    if auth_date - current_time > 60:
        raise TelegramWebAppAuthError("Future Telegram initData")

    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise TelegramWebAppAuthError("Invalid Telegram initData hash")

    parsed = parse_webapp_init_data(init_data)
    parsed["auth_date"] = auth_date
    parsed.pop("hash", None)
    return parsed


def _api_url(config: TelegramConfig, method: str) -> str:
    return f"{TELEGRAM_API_BASE.format(token=config.bot_token)}/{method}"


def send_message(
    text: str,
    config: TelegramConfig | None = None,
    reply_markup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a plain text or HTML message to the configured chat."""
    cfg = config or TelegramConfig.from_env()
    payload = {
        "chat_id": cfg.chat_id,
        "text": text,
        "parse_mode": cfg.parse_mode,
        "disable_web_page_preview": cfg.disable_web_page_preview,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    resp = requests.post(_api_url(cfg, "sendMessage"), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_thread(
    messages: list[str],
    config: TelegramConfig | None = None,
) -> list[dict[str, Any]]:
    """Send a threaded sequence of messages (as separate messages)."""
    cfg = config or TelegramConfig.from_env()
    results: list[dict[str, Any]] = []
    for msg in messages:
        result = send_message(msg, config=cfg)
        results.append(result)
        time.sleep(0.8)  # respect rate limits (~30 msg/sec)
    return results


def send_photo(
    photo_path: str,
    caption: str = "",
    config: TelegramConfig | None = None,
) -> dict[str, Any]:
    """Send a photo with optional caption."""
    cfg = config or TelegramConfig.from_env()
    url = _api_url(cfg, "sendPhoto")
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {
            "chat_id": cfg.chat_id,
            "caption": caption,
            "parse_mode": cfg.parse_mode,
        }
        resp = requests.post(url, data=data, files=files, timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_me(config: TelegramConfig | None = None) -> dict[str, Any]:
    """Health check: get bot info."""
    cfg = config or TelegramConfig.from_env()
    resp = requests.get(_api_url(cfg, "getMe"), timeout=10)
    resp.raise_for_status()
    return resp.json()
