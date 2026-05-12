"""Tests for local Telegram opt-in registration helpers."""

import json

import pytest

from guard0.telegram_subscriptions import (
    MAX_TTL_SECONDS,
    TokenVerificationError,
    build_opt_in_record,
    build_telegram_registration_challenge,
    ensure_registration_token_not_replayed,
    public_opt_in_status,
    verify_telegram_registration_token,
)


SECRET = "local-test-secret-with-at-least-16-bytes"


def test_registration_challenge_round_trip_is_json_serializable():
    challenge = build_telegram_registration_challenge("ari-local", SECRET, now=1_700_000_000)

    assert challenge["version"] == "0guard.telegram_registration.v1"
    assert challenge["user_label"] == "ari-local"
    assert challenge["ttl_seconds"] == 900
    assert challenge["expires_at"] == 1_700_000_900
    assert challenge["one_time_use"] is True
    assert challenge["network_calls"] is False
    assert challenge["telegram_send"] is False
    json.dumps(challenge)

    verified = verify_telegram_registration_token(
        challenge["token"],
        SECRET,
        now=1_700_000_001,
    )

    assert verified["user_label"] == "ari-local"
    assert verified["token_id"] == challenge["token_id"]
    assert verified["ttl_seconds"] == 900
    assert verified["verified_at"] == 1_700_000_001
    assert verified["replay_key"] == verified["token_id"]
    assert "token" not in verified
    json.dumps(verified)


def test_registration_tokens_expire_at_the_boundary():
    challenge = build_telegram_registration_challenge("expiry-check", SECRET, ttl_seconds=30, now=100)

    assert verify_telegram_registration_token(challenge["token"], SECRET, now=129)["token_id"]
    with pytest.raises(TokenVerificationError) as excinfo:
        verify_telegram_registration_token(challenge["token"], SECRET, now=130)
    assert excinfo.value.code == "expired"


def test_registration_tokens_are_unique_and_replay_check_is_local():
    first = build_telegram_registration_challenge("same-user", SECRET, now=200)
    second = build_telegram_registration_challenge("same-user", SECRET, now=200)
    assert first["token_id"] != second["token_id"]

    verified = verify_telegram_registration_token(first["token"], SECRET, now=201)
    checked = ensure_registration_token_not_replayed(verified, consumed_token_ids=set())
    assert checked["replay_checked"] is True

    with pytest.raises(TokenVerificationError) as excinfo:
        ensure_registration_token_not_replayed(
            verified,
            consumed_token_ids={verified["token_id"]},
        )
    assert excinfo.value.code == "replayed_token"


def test_registration_token_rejects_tampering_and_malformed_input():
    challenge = build_telegram_registration_challenge("tamper-check", SECRET, now=300)
    prefix_and_payload = challenge["token"].rsplit(".", 1)[0]

    with pytest.raises(TokenVerificationError) as excinfo:
        verify_telegram_registration_token(f"{prefix_and_payload}.tampered", SECRET, now=301)
    assert excinfo.value.code == "bad_signature"

    with pytest.raises(TokenVerificationError) as excinfo:
        verify_telegram_registration_token("not-a-token", SECRET, now=301)
    assert excinfo.value.code == "malformed"

    with pytest.raises(TokenVerificationError) as excinfo:
        verify_telegram_registration_token(
            challenge["token"],
            "different-local-secret-with-enough-bytes",
            now=301,
        )
    assert excinfo.value.code == "bad_signature"


def test_registration_challenge_rejects_unsafe_inputs():
    with pytest.raises(ValueError):
        build_telegram_registration_challenge("", SECRET)
    with pytest.raises(ValueError):
        build_telegram_registration_challenge("bad\nlabel", SECRET)
    with pytest.raises(ValueError):
        build_telegram_registration_challenge("short-secret", "tiny")
    with pytest.raises(ValueError):
        build_telegram_registration_challenge("bad-ttl", SECRET, ttl_seconds=0)
    with pytest.raises(ValueError):
        build_telegram_registration_challenge(
            "bad-ttl",
            SECRET,
            ttl_seconds=MAX_TTL_SECONDS + 1,
        )
    with pytest.raises(ValueError):
        build_telegram_registration_challenge("bad-now", SECRET, now=-1)


def test_opt_in_record_serializes_and_public_status_redacts_identifiers():
    challenge = build_telegram_registration_challenge("ari@example.com", SECRET, now=400)
    verified = verify_telegram_registration_token(challenge["token"], SECRET, now=401)
    record = build_opt_in_record(
        verified,
        telegram_user={
            "id": 123456789,
            "chat_id": "-1001234567890",
            "username": "cryptoboss",
            "first_name": "Ari",
            "last_name": "Builder",
            "language_code": "en",
            "is_bot": False,
        },
        scopes=["mira_alerts", "mira_alerts", "security.digest"],
    )

    assert record["version"] == "0guard.telegram_opt_in.v1"
    assert record["status"] == "opted_in"
    assert record["user_label"] == "ari@example.com"
    assert record["telegram_user"]["chat_id"] == "-1001234567890"
    assert record["telegram_user"]["id"] == "123456789"
    assert record["scopes"] == ["mira_alerts", "security.digest"]
    assert record["challenge"]["token_id"] == verified["token_id"]
    assert record["network_calls"] is False
    assert record["telegram_send"] is False
    json.dumps(record)

    public = public_opt_in_status(record)
    public_json = json.dumps(public, sort_keys=True)
    assert "ari@example.com" not in public_json
    assert "-1001234567890" not in public_json
    assert "123456789" not in public_json
    assert "cryptoboss" not in public_json
    assert "Ari" not in public_json
    assert "Builder" not in public_json
    assert public["telegram_user"]["language_code"] == "en"
    assert public["network_calls"] is False
    assert public["telegram_send"] is False
    json.dumps(public)


def test_opt_in_record_rejects_malformed_inputs():
    challenge = build_telegram_registration_challenge("malformed-record", SECRET, now=500)
    verified = verify_telegram_registration_token(challenge["token"], SECRET, now=501)

    with pytest.raises(ValueError):
        build_opt_in_record({})
    with pytest.raises(ValueError):
        build_opt_in_record(verified, telegram_user="not-a-dict")
    with pytest.raises(ValueError):
        build_opt_in_record(verified, telegram_user={})
    with pytest.raises(ValueError):
        build_opt_in_record(verified, telegram_user={"id": object()})
    with pytest.raises(ValueError):
        build_opt_in_record(verified, telegram_user={"id": 123}, scopes=[])
    with pytest.raises(ValueError):
        build_opt_in_record(verified, telegram_user={"id": 123}, scopes=["bad scope"])
    with pytest.raises(ValueError):
        public_opt_in_status("not-a-record")
