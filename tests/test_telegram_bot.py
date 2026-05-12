"""Tests for telegram_bot module."""
import hashlib
import hmac
import json
import os
from urllib.parse import urlencode

import pytest

from guard0.telegram_bot import (
    TelegramConfig,
    TelegramWebAppAuthError,
    validate_webapp_init_data,
)


def signed_init_data(
    fields: dict[str, str],
    bot_token: str = "123456:ABCDEF",
) -> str:
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    signature = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": signature})


def test_config_from_env_missing():
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        os.environ.pop(key, None)
    with pytest.raises(RuntimeError):
        TelegramConfig.from_env()


def test_config_from_env_ok():
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
    os.environ["TELEGRAM_CHAT_ID"] = "-1001234567890"
    cfg = TelegramConfig.from_env()
    assert cfg.bot_token == "test_token"
    assert cfg.chat_id == "-1001234567890"
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    os.environ.pop("TELEGRAM_CHAT_ID", None)


def test_config_defaults():
    cfg = TelegramConfig(bot_token="x", chat_id="y")
    assert cfg.parse_mode == "HTML"
    assert cfg.disable_web_page_preview is True


def test_validate_webapp_init_data_ok():
    init_data = signed_init_data(
        {
            "auth_date": "1710000000",
            "query_id": "AAExample",
            "user": json.dumps(
                {
                    "id": 12345,
                    "first_name": "Ari",
                    "username": "arigatoexpress",
                    "allows_write_to_pm": True,
                },
                separators=(",", ":"),
            ),
        }
    )

    data = validate_webapp_init_data(init_data, "123456:ABCDEF", now=1710000100)

    assert data["auth_date"] == 1710000000
    assert data["query_id"] == "AAExample"
    assert data["user"]["id"] == 12345
    assert data["user"]["allows_write_to_pm"] is True
    assert "hash" not in data


def test_validate_webapp_init_data_rejects_tamper():
    init_data = signed_init_data({"auth_date": "1710000000", "user": '{"id":12345}'})
    tampered = init_data.replace("12345", "99999")

    with pytest.raises(TelegramWebAppAuthError, match="Invalid Telegram initData hash"):
        validate_webapp_init_data(tampered, "123456:ABCDEF", now=1710000100)


def test_validate_webapp_init_data_rejects_stale_payload():
    init_data = signed_init_data({"auth_date": "1710000000", "user": '{"id":12345}'})

    with pytest.raises(TelegramWebAppAuthError, match="Stale Telegram initData"):
        validate_webapp_init_data(init_data, "123456:ABCDEF", now=1710087001)


def test_validate_webapp_init_data_rejects_future_payload():
    init_data = signed_init_data({"auth_date": "1710001000", "user": '{"id":12345}'})

    with pytest.raises(TelegramWebAppAuthError, match="Future Telegram initData"):
        validate_webapp_init_data(init_data, "123456:ABCDEF", now=1710000000)


def test_validate_webapp_init_data_rejects_missing_hash():
    with pytest.raises(TelegramWebAppAuthError, match="Missing Telegram initData hash"):
        validate_webapp_init_data("auth_date=1710000000", "123456:ABCDEF", now=1710000000)
