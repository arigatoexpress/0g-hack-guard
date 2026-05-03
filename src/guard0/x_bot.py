"""X (Twitter) API v2 bot integration for 0G Hack Guard.

Supports posting single tweets, threaded tweets (tweet storms), and media uploads.
Uses OAuth 1.0a User Context via Tweepy for v2 tweet creation and v1.1 media upload.

Authentication
==============
X API v2 requires OAuth 1.0a User Context to create or delete tweets on behalf of
a user. OAuth 2.0 App-Only (bearer token) is read-only for most tweet endpoints.
OAuth 2.0 Authorization Code with PKCE is possible but requires a web callback flow;
for a backend bot we recommend OAuth 1.0a with statically provisioned access tokens.

Media upload still uses the v1.1 ``media/upload`` endpoint, which Tweepy exposes
through ``API.media_upload``. The returned ``media_id_string`` is then attached to
a v2 ``Client.create_tweet`` call via ``media_ids``.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tweepy
from tweepy.errors import HTTPException, TooManyRequests

logger = logging.getLogger(__name__)

DEFAULT_MAX_TWEET_LEN = 280
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 2.0  # seconds


@dataclass(frozen=True)
class PostedTweet:
    """Result of a successful tweet post."""

    tweet_id: str
    text: str
    media_keys: list[str] | None = None


@dataclass(frozen=True)
class ThreadResult:
    """Result of posting a thread."""

    tweets: list[PostedTweet]


class XBotError(Exception):
    """Base exception for XBot errors."""


class XBotConfigError(XBotError):
    """Raised when required configuration is missing or invalid."""


class XBotRateLimitError(XBotError):
    """Raised when rate limited after all retries exhausted."""


class XBotPostError(XBotError):
    """Raised when a post fails for a non-recoverable reason."""


class XBot:
    """Production-ready X API v2 wrapper for 0G Hack Guard.

    Parameters
    ----------
    consumer_key:
        X API OAuth 1.0a Consumer Key.
    consumer_secret:
        X API OAuth 1.0a Consumer Secret.
    access_token:
        X API OAuth 1.0a Access Token.
    access_token_secret:
        X API OAuth 1.0a Access Token Secret.
    wait_on_rate_limit:
        Whether Tweepy should automatically sleep when a v2 rate limit is hit.
    max_retries:
        Number of times to retry on transient errors (e.g. 503, 429 when
        ``wait_on_rate_limit`` is False).
    backoff_base:
        Base seconds for exponential backoff between retries.
    """

    def __init__(
        self,
        *,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
        wait_on_rate_limit: bool = True,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
    ) -> None:
        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            raise XBotConfigError("All four OAuth 1.0a credentials are required.")

        self._client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=wait_on_rate_limit,
            return_type=tweepy.Response,
        )

        # v1.1 API is needed for media upload.
        auth = tweepy.OAuth1UserHandler(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        self._api = tweepy.API(auth)

        self._max_retries = max_retries
        self._backoff_base = backoff_base

    # ------------------------------------------------------------------ #
    # Convenience factory
    # ------------------------------------------------------------------ #

    @classmethod
    def from_env(cls, **kwargs: Any) -> "XBot":
        """Create an ``XBot`` from environment variables.

        Expected variables::

            X_CONSUMER_KEY
            X_CONSUMER_SECRET
            X_ACCESS_TOKEN
            X_ACCESS_TOKEN_SECRET
        """
        required = [
            "X_CONSUMER_KEY",
            "X_CONSUMER_SECRET",
            "X_ACCESS_TOKEN",
            "X_ACCESS_TOKEN_SECRET",
        ]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise XBotConfigError(f"Missing environment variables: {', '.join(missing)}")

        return cls(
            consumer_key=os.getenv("X_CONSUMER_KEY", ""),
            consumer_secret=os.getenv("X_CONSUMER_SECRET", ""),
            access_token=os.getenv("X_ACCESS_TOKEN", ""),
            access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
            **kwargs,
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def post_tweet(
        self,
        text: str,
        *,
        media_paths: list[str | Path] | None = None,
        reply_to: str | None = None,
    ) -> PostedTweet:
        """Post a single tweet, optionally with media and/or as a reply.

        Parameters
        ----------
        text:
            Tweet text (max 280 characters for standard accounts).
        media_paths:
            Local file paths of images or GIFs to attach.
        reply_to:
            Tweet ID to reply to (used internally for threading).

        Returns
        -------
        PostedTweet
        """
        if len(text) > DEFAULT_MAX_TWEET_LEN:
            logger.warning("Tweet text exceeds %d chars (%d); X may reject it.",
                           DEFAULT_MAX_TWEET_LEN, len(text))

        media_ids = self._upload_media(media_paths) if media_paths else None

        payload: dict[str, Any] = {"text": text}
        if media_ids:
            payload["media_ids"] = media_ids
        if reply_to:
            payload["in_reply_to_tweet_id"] = reply_to

        resp = self._call_v2_with_retry(self._client.create_tweet, **payload)

        tweet_id = resp.data["id"]  # type: ignore[index]
        logger.info("Posted tweet id=%s reply_to=%s media_ids=%s",
                    tweet_id, reply_to, media_ids)

        return PostedTweet(
            tweet_id=str(tweet_id),
            text=text,
            media_keys=[str(m) for m in media_ids] if media_ids else None,
        )

    def post_thread(self, tweets: list[str], *, media_paths: list[str | Path] | None = None) -> ThreadResult:
        """Post a threaded tweet storm.

        Parameters
        ----------
        tweets:
            Ordered list of tweet texts. Each tweet after the first replies
            to the previous one.
        media_paths:
            Media to attach to the *first* tweet only. If you need media on
            individual tweets, call ``post_tweet`` repeatedly yourself.

        Returns
        -------
        ThreadResult
        """
        if not tweets:
            raise XBotPostError("Cannot post an empty thread.")

        results: list[PostedTweet] = []
        reply_to: str | None = None

        for idx, text in enumerate(tweets):
            tweet_media = media_paths if idx == 0 else None
            posted = self.post_tweet(text, media_paths=tweet_media, reply_to=reply_to)
            results.append(posted)
            reply_to = posted.tweet_id
            # Small sleep to be a polite API citizen between thread posts.
            if idx < len(tweets) - 1:
                time.sleep(0.5)

        logger.info("Posted thread with %d tweets. Root=%s", len(results), results[0].tweet_id)
        return ThreadResult(tweets=results)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _upload_media(self, media_paths: list[str | Path]) -> list[str]:
        """Upload local media files via v1.1 and return media IDs."""
        media_ids: list[str] = []
        for path in media_paths:
            p = Path(path)
            if not p.exists():
                raise XBotPostError(f"Media file not found: {p}")
            try:
                media = self._api.media_upload(filename=str(p))
                media_ids.append(media.media_id_string)
                logger.debug("Uploaded media %s -> id=%s", p, media.media_id_string)
            except HTTPException as exc:
                raise XBotPostError(f"Failed to upload media {p}: {exc}") from exc
        return media_ids

    def _call_v2_with_retry(self, method, *args, **kwargs):
        """Call a Tweepy v2 method with exponential backoff on 429/5xx."""
        last_exception: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return method(*args, **kwargs)
            except TooManyRequests as exc:
                last_exception = exc
                # If wait_on_rate_limit is True Tweepy usually handles this,
                # but we still guard against edge cases.
                reset_time = self._extract_reset_time(exc) or (self._backoff_base * (2 ** attempt))
                logger.warning("Rate limited on attempt %d/%d. Sleeping %.1fs…",
                               attempt, self._max_retries, reset_time)
                time.sleep(reset_time)
            except HTTPException as exc:
                last_exception = exc
                if exc.response.status_code >= 500:  # type: ignore[union-attr]
                    sleep_for = self._backoff_base * (2 ** attempt)
                    logger.warning("Server error %s on attempt %d/%d. Retrying in %.1fs…",
                                   exc.response.status_code, attempt, self._max_retries, sleep_for)
                    time.sleep(sleep_for)
                else:
                    # 4xx (other than 429) is not retryable.
                    raise XBotPostError(f"X API error {exc.response.status_code}: {exc}") from exc
            except Exception as exc:
                raise XBotPostError(f"Unexpected error calling X API: {exc}") from exc

        raise XBotRateLimitError(
            f"Rate limited or server error after {self._max_retries} retries."
        ) from last_exception

    @staticmethod
    def _extract_reset_time(exc: TooManyRequests) -> float | None:
        """Try to read X-Rate-Limit-Reset header from a 429 response."""
        try:
            reset_ts = int(exc.response.headers.get("x-rate-limit-reset", 0))  # type: ignore[union-attr]
            if reset_ts:
                return max(reset_ts - time.time(), 1.0)
        except Exception:
            pass
        return None
