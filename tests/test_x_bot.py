"""Tests for guard0.x_bot."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from guard0.x_bot import (
    DeletedTweet,
    XBot,
    XBotConfigError,
    XMediaTweet,
    XBotPostError,
    XBotRateLimitError,
    PostedTweet,
    ThreadResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_env():
    """Ensure X env vars are clean between tests."""
    for key in (
        "X_CONSUMER_KEY",
        "X_CONSUMER_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
    ):
        os.environ.pop(key, None)
    yield
    for key in (
        "X_CONSUMER_KEY",
        "X_CONSUMER_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
    ):
        os.environ.pop(key, None)


@pytest.fixture
def fake_creds():
    return {
        "consumer_key": "ck",
        "consumer_secret": "cs",
        "access_token": "at",
        "access_token_secret": "ats",
    }


@pytest.fixture
def mock_tweepy():
    """Patch both tweepy.Client and tweepy.API/tweepy.OAuth1UserHandler."""
    with patch("guard0.x_bot.tweepy.Client") as MockClient, \
         patch("guard0.x_bot.tweepy.API") as MockAPI, \
         patch("guard0.x_bot.tweepy.OAuth1UserHandler") as MockAuth:

        client_instance = MagicMock()
        api_instance = MagicMock()
        auth_instance = MagicMock()

        MockClient.return_value = client_instance
        MockAPI.return_value = api_instance
        MockAuth.return_value = auth_instance

        yield {
            "Client": MockClient,
            "API": MockAPI,
            "OAuth1UserHandler": MockAuth,
            "client": client_instance,
            "api": api_instance,
        }


# ---------------------------------------------------------------------------
# Configuration / construction
# ---------------------------------------------------------------------------

def test_from_env_success(fake_creds):
    os.environ.update(
        {
            "X_CONSUMER_KEY": fake_creds["consumer_key"],
            "X_CONSUMER_SECRET": fake_creds["consumer_secret"],
            "X_ACCESS_TOKEN": fake_creds["access_token"],
            "X_ACCESS_TOKEN_SECRET": fake_creds["access_token_secret"],
        }
    )
    bot = XBot.from_env()
    assert bot is not None


def test_from_env_missing():
    with pytest.raises(XBotConfigError) as exc_info:
        XBot.from_env()
    assert "Missing environment variables" in str(exc_info.value)


def test_init_missing_creds():
    with pytest.raises(XBotConfigError):
        XBot(consumer_key="", consumer_secret="s", access_token="t", access_token_secret="ts")


# ---------------------------------------------------------------------------
# Single tweet posting
# ---------------------------------------------------------------------------

def test_post_tweet_success(mock_tweepy, fake_creds):
    mock_tweepy["client"].create_tweet.return_value = MagicMock(data={"id": "12345"})

    bot = XBot(**fake_creds)
    result = bot.post_tweet("Hello 0G!")

    assert isinstance(result, PostedTweet)
    assert result.tweet_id == "12345"
    assert result.text == "Hello 0G!"
    mock_tweepy["client"].create_tweet.assert_called_once_with(text="Hello 0G!")


def test_post_tweet_with_media(mock_tweepy, fake_creds, tmp_path: Path):
    media_file = tmp_path / "pic.png"
    media_file.write_bytes(b"fake_png")

    mock_media = MagicMock()
    mock_media.media_id_string = "media_42"
    mock_tweepy["api"].media_upload.return_value = mock_media
    mock_tweepy["client"].create_tweet.return_value = MagicMock(data={"id": "67890"})

    bot = XBot(**fake_creds)
    result = bot.post_tweet("Look at this.", media_paths=[media_file])

    assert result.tweet_id == "67890"
    mock_tweepy["api"].media_upload.assert_called_once_with(filename=str(media_file))
    mock_tweepy["client"].create_tweet.assert_called_once_with(
        text="Look at this.", media_ids=["media_42"]
    )


def test_post_tweet_media_missing(mock_tweepy, fake_creds):
    bot = XBot(**fake_creds)
    with pytest.raises(XBotPostError, match="Media file not found"):
        bot.post_tweet("Oops", media_paths=["/nonexistent/file.png"])


# ---------------------------------------------------------------------------
# Thread posting
# ---------------------------------------------------------------------------

def test_post_thread_success(mock_tweepy, fake_creds):
    mock_tweepy["client"].create_tweet.side_effect = [
        MagicMock(data={"id": "1"}),
        MagicMock(data={"id": "2"}),
        MagicMock(data={"id": "3"}),
    ]

    bot = XBot(**fake_creds)
    thread = bot.post_thread(["First", "Second", "Third"])

    assert isinstance(thread, ThreadResult)
    assert len(thread.tweets) == 3
    assert thread.tweets[0].tweet_id == "1"
    assert thread.tweets[1].tweet_id == "2"
    assert thread.tweets[2].tweet_id == "3"

    calls = mock_tweepy["client"].create_tweet.call_args_list
    assert calls[0].kwargs["text"] == "First"
    assert calls[1].kwargs["text"] == "Second"
    assert calls[1].kwargs["in_reply_to_tweet_id"] == "1"
    assert calls[2].kwargs["text"] == "Third"
    assert calls[2].kwargs["in_reply_to_tweet_id"] == "2"


def test_post_thread_empty(mock_tweepy, fake_creds):
    bot = XBot(**fake_creds)
    with pytest.raises(XBotPostError, match="empty thread"):
        bot.post_thread([])


# ---------------------------------------------------------------------------
# Media cleanup manifest helpers
# ---------------------------------------------------------------------------

def test_list_media_tweets_reads_media_bearing_timeline(mock_tweepy, fake_creds):
    mock_tweepy["client"].get_me.return_value = MagicMock(data={"id": "user-1"})
    mock_tweepy["client"].get_users_tweets.return_value = MagicMock(
        data=[
            {
                "id": "111",
                "text": "with media",
                "created_at": "2026-05-14T19:00:00Z",
                "attachments": {"media_keys": ["3_abc"]},
            },
            {"id": "222", "text": "plain", "attachments": {}},
        ],
        includes={
            "media": [
                {
                    "media_key": "3_abc",
                    "type": "photo",
                    "url": "https://pbs.twimg.com/media/example.jpg",
                }
            ]
        },
        meta={},
    )

    bot = XBot(**fake_creds)
    tweets = bot.list_media_tweets(max_results=100, pages=1)

    assert tweets == [
        XMediaTweet(
            tweet_id="111",
            text="with media",
            created_at="2026-05-14T19:00:00Z",
            media_keys=["3_abc"],
            media_types=["photo"],
            media_urls=["https://pbs.twimg.com/media/example.jpg"],
        )
    ]
    mock_tweepy["client"].get_me.assert_called_once_with(user_auth=True)
    mock_tweepy["client"].get_users_tweets.assert_called_once()
    assert mock_tweepy["client"].get_users_tweets.call_args.args == ("user-1",)
    assert mock_tweepy["client"].get_users_tweets.call_args.kwargs["user_auth"] is True
    assert "attachments.media_keys" in mock_tweepy["client"].get_users_tweets.call_args.kwargs[
        "expansions"
    ]


def test_delete_tweets_uses_explicit_user_auth(mock_tweepy, fake_creds):
    mock_tweepy["client"].delete_tweet.side_effect = [
        MagicMock(data={"deleted": True}),
        MagicMock(data={"deleted": True}),
    ]

    bot = XBot(**fake_creds)
    results = bot.delete_tweets(["111", "222"])

    assert results == [
        DeletedTweet(tweet_id="111", deleted=True),
        DeletedTweet(tweet_id="222", deleted=True),
    ]
    assert mock_tweepy["client"].delete_tweet.call_args_list[0].args == ("111",)
    assert mock_tweepy["client"].delete_tweet.call_args_list[0].kwargs["user_auth"] is True


# ---------------------------------------------------------------------------
# Retry / rate-limit handling
# ---------------------------------------------------------------------------

def test_post_tweet_retries_on_500(mock_tweepy, fake_creds):
    """Transient 500 errors should be retried with backoff."""
    from tweepy.errors import HTTPException
    from requests import Response

    resp = Response()
    resp.status_code = 503

    mock_tweepy["client"].create_tweet.side_effect = [
        HTTPException(resp),
        MagicMock(data={"id": "99"}),
    ]

    bot = XBot(**fake_creds, max_retries=3, backoff_base=0.01)
    result = bot.post_tweet("Retry me")

    assert result.tweet_id == "99"
    assert mock_tweepy["client"].create_tweet.call_count == 2


def test_post_tweet_rate_limit_exhausted(mock_tweepy, fake_creds):
    """If all retries are exhausted on 429, raise XBotRateLimitError."""
    from tweepy.errors import TooManyRequests
    from requests import Response

    resp = Response()
    resp.status_code = 429
    resp.headers["x-rate-limit-reset"] = "0"

    mock_tweepy["client"].create_tweet.side_effect = TooManyRequests(resp)

    bot = XBot(**fake_creds, max_retries=2, backoff_base=0.01)
    with pytest.raises(XBotRateLimitError):
        bot.post_tweet("Rate limited")


def test_post_tweet_4xx_not_retried(mock_tweepy, fake_creds):
    """Non-retryable 4xx errors should fail fast."""
    from tweepy.errors import HTTPException
    from requests import Response

    resp = Response()
    resp.status_code = 403

    mock_tweepy["client"].create_tweet.side_effect = HTTPException(resp)

    bot = XBot(**fake_creds, max_retries=3)
    with pytest.raises(XBotPostError, match="403"):
        bot.post_tweet("Forbidden")

    mock_tweepy["client"].create_tweet.assert_called_once()
