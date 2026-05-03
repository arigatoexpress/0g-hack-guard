"""Tests for telegram_bot module."""
import os
import pytest

from guard0.telegram_bot import TelegramConfig


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
