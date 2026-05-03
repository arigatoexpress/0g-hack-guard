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

import os
import time
from dataclasses import dataclass
from typing import Any

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
