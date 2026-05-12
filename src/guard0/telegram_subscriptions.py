"""Local Telegram opt-in registration helpers.

This module intentionally does not import the live Telegram bot integration.
It only builds and verifies local HMAC registration challenges plus
JSON-serializable opt-in records that a caller may persist after consent.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
import time
from collections.abc import Iterable
from typing import Any

TOKEN_PREFIX = "g0tg"
TOKEN_VERSION = 1
TOKEN_TYPE = "0guard.telegram_registration.v1"
OPT_IN_RECORD_VERSION = "0guard.telegram_opt_in.v1"
DEFAULT_SCOPE = "mira_alerts"
MAX_TTL_SECONDS = 3600
MIN_SECRET_BYTES = 16
MAX_CLOCK_SKEW_SECONDS = 60

_SCOPE_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
_TOKEN_ID_RE = re.compile(r"^[a-f0-9]{64}$")


class TokenVerificationError(ValueError):
    """Raised when a registration token cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def build_telegram_registration_challenge(
    user_label: str,
    secret: str,
    ttl_seconds: int = 900,
    now: int | None = None,
) -> dict[str, Any]:
    """Build a bounded, signed, one-time Telegram registration challenge.

    The returned dict is JSON-serializable and safe to hand to app/front-end
    code. It performs no Telegram sends and makes no network calls.
    """

    issued_at = _coerce_now(now)
    ttl = _validate_ttl(ttl_seconds)
    label = _validate_user_label(user_label)
    secret_bytes = _coerce_secret(secret)
    expires_at = issued_at + ttl

    payload = {
        "aud": "telegram-opt-in",
        "exp": expires_at,
        "iat": issued_at,
        "nonce": secrets.token_urlsafe(24),
        "sub": label,
        "typ": TOKEN_TYPE,
        "v": TOKEN_VERSION,
    }
    payload_b64 = _b64encode_json(payload)
    signature = _sign(f"{TOKEN_PREFIX}.{payload_b64}", secret_bytes)
    token = f"{TOKEN_PREFIX}.{payload_b64}.{signature}"

    return {
        "version": TOKEN_TYPE,
        "token": token,
        "token_id": _token_id(token),
        "user_label": label,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "ttl_seconds": ttl,
        "one_time_use": True,
        "network_calls": False,
        "telegram_send": False,
    }


def verify_telegram_registration_token(
    token: str,
    secret: str,
    now: int | None = None,
) -> dict[str, Any]:
    """Verify a Telegram registration token and return JSON-safe claims."""

    observed_at = _coerce_now(now)
    secret_bytes = _coerce_secret(secret)
    prefix, payload_b64, signature = _split_token(token)

    expected_signature = _sign(f"{prefix}.{payload_b64}", secret_bytes)
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenVerificationError("bad_signature", "registration token signature mismatch")

    payload = _decode_payload(payload_b64)
    _validate_payload_shape(payload)

    issued_at = payload["iat"]
    expires_at = payload["exp"]
    if observed_at >= expires_at:
        raise TokenVerificationError("expired", "registration token has expired")
    if issued_at > observed_at + MAX_CLOCK_SKEW_SECONDS:
        raise TokenVerificationError("not_yet_valid", "registration token was issued in the future")
    if expires_at <= issued_at or expires_at - issued_at > MAX_TTL_SECONDS:
        raise TokenVerificationError("invalid_expiry", "registration token expiry is outside bounds")

    label = _validate_user_label(payload["sub"])
    return {
        "version": TOKEN_TYPE,
        "token_id": _token_id(token),
        "user_label": label,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "ttl_seconds": expires_at - issued_at,
        "verified_at": observed_at,
        "one_time_use": True,
        "replay_key": _token_id(token),
    }


def ensure_registration_token_not_replayed(
    verified: dict[str, Any],
    consumed_token_ids: Iterable[str],
) -> dict[str, Any]:
    """Fail if a verified token id has already been consumed by local state.

    This helper is intentionally storage-agnostic: callers can keep consumed
    token ids in a database, JSON file, or in-memory set and pass them here
    before creating an opt-in record.
    """

    checked = _validate_verified_claims(verified)
    token_id = checked["token_id"]
    if token_id in set(consumed_token_ids):
        raise TokenVerificationError("replayed_token", "registration token was already consumed")
    checked["replay_checked"] = True
    return checked


def build_opt_in_record(
    verified: dict[str, Any],
    telegram_user: dict[str, Any] | None = None,
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Build a local opt-in record from verified claims and optional Telegram user data."""

    claims = _validate_verified_claims(verified)
    normalized_user = _normalize_telegram_user(telegram_user)
    normalized_scopes = _normalize_scopes(scopes)
    record_seed = {
        "scopes": normalized_scopes,
        "telegram_user": normalized_user,
        "token_id": claims["token_id"],
        "user_label": claims["user_label"],
    }
    record_id = f"tgopt_{_stable_digest(record_seed)[:24]}"

    return {
        "version": OPT_IN_RECORD_VERSION,
        "record_id": record_id,
        "status": "opted_in",
        "user_label": claims["user_label"],
        "telegram_user": normalized_user,
        "scopes": normalized_scopes,
        "opted_in_at": claims["verified_at"],
        "challenge": {
            "token_id": claims["token_id"],
            "issued_at": claims["issued_at"],
            "expires_at": claims["expires_at"],
            "one_time_use": True,
        },
        "source": "local_telegram_registration_challenge",
        "network_calls": False,
        "telegram_send": False,
    }


def public_opt_in_status(record: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted public status view without chat or user identifiers."""

    if not isinstance(record, dict):
        raise ValueError("record must be a dict")

    telegram_user = record.get("telegram_user") or {}
    if not isinstance(telegram_user, dict):
        telegram_user = {}

    challenge = record.get("challenge") or {}
    if not isinstance(challenge, dict):
        challenge = {}

    return {
        "version": record.get("version", OPT_IN_RECORD_VERSION),
        "record_id": record.get("record_id"),
        "status": record.get("status", "unknown"),
        "user_label": _redact_identifier(record.get("user_label")),
        "telegram_user": {
            "id": _redact_identifier(telegram_user.get("id")),
            "chat_id": _redact_identifier(telegram_user.get("chat_id")),
            "username": _redact_identifier(telegram_user.get("username")),
            "first_name": _redact_identifier(telegram_user.get("first_name")),
            "last_name": _redact_identifier(telegram_user.get("last_name")),
            "is_bot": telegram_user.get("is_bot"),
            "language_code": telegram_user.get("language_code"),
        },
        "scopes": list(record.get("scopes") or []),
        "opted_in_at": record.get("opted_in_at"),
        "challenge": {
            "token_id": _redact_identifier(challenge.get("token_id")),
            "one_time_use": challenge.get("one_time_use", True),
        },
        "network_calls": False,
        "telegram_send": False,
    }


def _coerce_now(now: int | None) -> int:
    if now is None:
        return int(time.time())
    if isinstance(now, bool) or not isinstance(now, int):
        raise ValueError("now must be an integer Unix timestamp")
    if now < 0:
        raise ValueError("now must be non-negative")
    return now


def _validate_ttl(ttl_seconds: int) -> int:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
        raise ValueError("ttl_seconds must be an integer")
    if ttl_seconds < 1 or ttl_seconds > MAX_TTL_SECONDS:
        raise ValueError(f"ttl_seconds must be between 1 and {MAX_TTL_SECONDS}")
    return ttl_seconds


def _coerce_secret(secret: str) -> bytes:
    if not isinstance(secret, str):
        raise ValueError("secret must be a string")
    secret_bytes = secret.encode("utf-8")
    if len(secret_bytes) < MIN_SECRET_BYTES:
        raise ValueError(f"secret must be at least {MIN_SECRET_BYTES} bytes")
    return secret_bytes


def _validate_user_label(user_label: Any) -> str:
    if not isinstance(user_label, str):
        raise ValueError("user_label must be a string")
    label = user_label.strip()
    if not label or len(label) > 128:
        raise ValueError("user_label must be between 1 and 128 characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in label):
        raise ValueError("user_label must not contain control characters")
    return label


def _split_token(token: str) -> tuple[str, str, str]:
    if not isinstance(token, str) or not token:
        raise TokenVerificationError("malformed", "registration token must be a non-empty string")
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenVerificationError("malformed", "registration token must have three parts")
    prefix, payload_b64, signature = parts
    if prefix != TOKEN_PREFIX:
        raise TokenVerificationError("malformed", "registration token has an unknown prefix")
    if not payload_b64 or not signature:
        raise TokenVerificationError("malformed", "registration token has empty parts")
    return prefix, payload_b64, signature


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    if payload.get("typ") != TOKEN_TYPE:
        raise TokenVerificationError("wrong_type", "registration token has the wrong type")
    if payload.get("v") != TOKEN_VERSION:
        raise TokenVerificationError("wrong_version", "registration token has the wrong version")
    if payload.get("aud") != "telegram-opt-in":
        raise TokenVerificationError("wrong_audience", "registration token has the wrong audience")
    if not isinstance(payload.get("iat"), int) or isinstance(payload.get("iat"), bool):
        raise TokenVerificationError("malformed_payload", "registration token issued_at is invalid")
    if not isinstance(payload.get("exp"), int) or isinstance(payload.get("exp"), bool):
        raise TokenVerificationError("malformed_payload", "registration token expires_at is invalid")
    if not isinstance(payload.get("nonce"), str) or len(payload["nonce"]) < 24:
        raise TokenVerificationError("malformed_payload", "registration token nonce is invalid")
    try:
        _validate_user_label(payload.get("sub"))
    except ValueError as exc:
        raise TokenVerificationError(
            "malformed_payload",
            "registration token subject is invalid",
        ) from exc


def _validate_verified_claims(verified: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(verified, dict):
        raise ValueError("verified must be a dict")
    if verified.get("version") != TOKEN_TYPE:
        raise ValueError("verified claims have the wrong version")

    token_id = verified.get("token_id")
    if not isinstance(token_id, str) or not _TOKEN_ID_RE.fullmatch(token_id):
        raise ValueError("verified token_id is invalid")

    replay_key = verified.get("replay_key", token_id)
    if not isinstance(replay_key, str) or replay_key != token_id:
        raise ValueError("verified replay_key is invalid")

    claims = {
        "version": TOKEN_TYPE,
        "token_id": token_id,
        "replay_key": replay_key,
        "user_label": _validate_user_label(verified.get("user_label")),
        "issued_at": _coerce_claim_int(verified, "issued_at"),
        "expires_at": _coerce_claim_int(verified, "expires_at"),
        "ttl_seconds": _coerce_claim_int(verified, "ttl_seconds"),
        "verified_at": _coerce_claim_int(verified, "verified_at"),
        "one_time_use": _coerce_optional_bool(verified, "one_time_use", default=True),
    }
    if claims["expires_at"] <= claims["issued_at"]:
        raise ValueError("verified expiry is invalid")
    if claims["ttl_seconds"] != claims["expires_at"] - claims["issued_at"]:
        raise ValueError("verified ttl_seconds does not match expiry")
    return claims


def _coerce_claim_int(claims: dict[str, Any], key: str) -> int:
    value = claims.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"verified {key} is invalid")
    return value


def _coerce_optional_bool(claims: dict[str, Any], key: str, default: bool) -> bool:
    value = claims.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"verified {key} is invalid")
    return value


def _normalize_telegram_user(telegram_user: dict[str, Any] | None) -> dict[str, Any] | None:
    if telegram_user is None:
        return None
    if not isinstance(telegram_user, dict):
        raise ValueError("telegram_user must be a dict when provided")

    normalized: dict[str, Any] = {}
    for key in ("id", "chat_id", "username", "first_name", "last_name", "language_code"):
        if key in telegram_user and telegram_user[key] is not None:
            normalized[key] = _normalize_public_string(telegram_user[key], key)

    if "is_bot" in telegram_user and telegram_user["is_bot"] is not None:
        if not isinstance(telegram_user["is_bot"], bool):
            raise ValueError("telegram_user.is_bot must be a bool")
        normalized["is_bot"] = telegram_user["is_bot"]

    if not normalized:
        raise ValueError("telegram_user must contain at least one supported field")
    return normalized


def _normalize_public_string(value: Any, key: str) -> str:
    if isinstance(value, bool):
        raise ValueError(f"telegram_user.{key} must be a string or integer")
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str):
        raise ValueError(f"telegram_user.{key} must be a string or integer")
    text = value.strip()
    if not text or len(text) > 128:
        raise ValueError(f"telegram_user.{key} must be between 1 and 128 characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in text):
        raise ValueError(f"telegram_user.{key} must not contain control characters")
    return text


def _normalize_scopes(scopes: list[str] | None) -> list[str]:
    raw_scopes = [DEFAULT_SCOPE] if scopes is None else scopes
    if not isinstance(raw_scopes, list) or not raw_scopes:
        raise ValueError("scopes must be a non-empty list")

    normalized: list[str] = []
    seen: set[str] = set()
    for scope in raw_scopes:
        if not isinstance(scope, str):
            raise ValueError("scopes must contain only strings")
        cleaned = scope.strip()
        if not _SCOPE_RE.fullmatch(cleaned):
            raise ValueError("scopes must be 1-64 safe identifier characters")
        if cleaned not in seen:
            normalized.append(cleaned)
            seen.add(cleaned)
    return normalized


def _b64encode_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    return _b64encode_bytes(encoded)


def _b64encode_bytes(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _b64decode_text(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, binascii.Error) as exc:
        raise TokenVerificationError("malformed", "registration token contains bad base64") from exc


def _decode_payload(payload_b64: str) -> dict[str, Any]:
    try:
        payload = json.loads(_b64decode_text(payload_b64))
    except json.JSONDecodeError as exc:
        raise TokenVerificationError("malformed_payload", "registration token payload is not JSON") from exc
    if not isinstance(payload, dict):
        raise TokenVerificationError("malformed_payload", "registration token payload must be an object")
    return payload


def _sign(signing_input: str, secret_bytes: bytes) -> str:
    digest = hmac.new(secret_bytes, signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64encode_bytes(digest)


def _token_id(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _stable_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _redact_identifier(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return f"redacted:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"
