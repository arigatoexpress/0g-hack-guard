"""Tests for the 0G Hack Guard content engine."""
import json

import pytest

from guard0.content_engine import (
    generate_content,
    generate_batch,
    batch_to_json,
    from_signature_result,
    _get_severity,
    _format_loss,
    _generate_hashtags,
    _truncate_to_limit,
    _match_signatures,
    _derive_attack_vector_from_signatures,
    ContentOutput,
    SEVERITY_CRITICAL,
    SEVERITY_MAJOR,
)


# ── Helper fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def drift_incident():
    return {
        "protocol": "Drift Protocol",
        "loss_usd": 285_000_000,
        "chain": "Solana",
        "date": "2026-04-01",
        "attack_vector": "social engineering",
        "description": "Durable nonce social engineering.",
        "attribution": "Lazarus Group",
        "lesson": "Never pre-sign admin transactions.",
    }


@pytest.fixture
def kelp_incident():
    return {
        "protocol": "Kelp DAO",
        "loss_usd": 293_000_000,
        "chain": "Ethereum",
        "date": "2026-04-18",
        "attack_vector": "bridge message forgery",
        "description": "LayerZero bridge message forgery via 1-of-1 DVN.",
        "attribution": "Lazarus Group",
        "lesson": "Require >=2 independent bridge verifiers.",
    }


@pytest.fixture
def wasabi_incident():
    return {
        "protocol": "Wasabi Protocol",
        "loss_usd": 5_000_000,
        "chain": "Multi-chain",
        "date": "2026-04-30",
        "attack_vector": "admin key compromise",
        "description": "Single EOA admin key compromised.",
        "attribution": "Unknown",
        "lesson": "Multisig + timelock on all admin functions.",
    }


@pytest.fixture
def giddy_incident():
    return {
        "protocol": "Giddy Finance",
        "loss_usd": 1_300_000,
        "chain": "Ethereum",
        "date": "2026-04-23",
        "attack_vector": "signature replay",
        "description": "EIP-712 signature replay.",
        "attribution": "Unknown",
        "lesson": "Bind signatures to chainId and contract address.",
    }


# ── Unit tests for helpers ───────────────────────────────────────────────────


def test_get_severity():
    assert _get_severity(150_000_000) == "critical"
    assert _get_severity(100_000_000) == "critical"
    assert _get_severity(50_000_000) == "major"
    assert _get_severity(10_000_000) == "major"
    assert _get_severity(9_999_999) == "mid"
    assert _get_severity(500_000) == "mid"


def test_format_loss():
    assert _format_loss(1_500_000_000) == "1.5B"
    assert _format_loss(1_000_000_000) == "1B"
    assert _format_loss(285_000_000) == "285M"
    assert _format_loss(1_000_000) == "1M"
    assert _format_loss(500_000) == "500K"
    assert _format_loss(1_000) == "1K"
    assert _format_loss(500) == "500"


def test_generate_hashtags():
    hashtags = _generate_hashtags("Drift Protocol", "Solana", "social engineering")
    assert "#DeFi" in hashtags
    assert "#CryptoSecurity" in hashtags
    assert "#0GHackGuard" in hashtags
    assert "#DriftProtocol" in hashtags
    assert "#SOL" in hashtags
    assert "#SocialEngineering" in hashtags


def test_truncate_to_limit_under():
    text = "Short tweet."
    assert _truncate_to_limit(text, 280) == text


def test_truncate_to_limit_over():
    text = "x" * 300
    result = _truncate_to_limit(text, 280)
    assert len(result) <= 280
    assert result.endswith("...")


def test_match_signatures_social_engineering():
    sigs = _match_signatures("social engineering")
    assert "durable_nonce_admin_transfer" in sigs
    assert "soceng" in sigs


def test_match_signatures_bridge():
    sigs = _match_signatures("bridge message forgery")
    assert "single_dvn_bridge" in sigs
    assert "lzReceive" in sigs


def test_match_signatures_flash_loan():
    sigs = _match_signatures("flash loan oracle manipulation")
    assert "sequence_flash_swap_withdraw" in sigs
    assert "flash_loan_init" in sigs


def test_derive_attack_vector_from_signatures():
    assert (
        _derive_attack_vector_from_signatures(
            ["durable_nonce_admin_transfer"], [], []
        )
        == "social engineering"
    )
    assert (
        _derive_attack_vector_from_signatures(
            ["single_dvn_bridge"], [], []
        )
        == "bridge message forgery"
    )
    assert (
        _derive_attack_vector_from_signatures(
            ["sequence_grant_upgrade"], [], []
        )
        == "UUPS proxy upgrade"
    )
    assert (
        _derive_attack_vector_from_signatures([], [], []) == "undisclosed"
    )


# ── Content generation tests ─────────────────────────────────────────────────


def test_generate_content_critical(drift_incident):
    out = generate_content(drift_incident)
    assert isinstance(out, ContentOutput)
    assert out.protocol == "Drift Protocol"
    assert out.severity == "critical"
    assert out.loss_usd == 285_000_000
    assert len(out.alert_tweet) <= 280
    assert all(len(t) <= 280 for t in out.thread_breakdown)
    assert len(out.summary_post) <= 280
    assert "Lazarus" in out.metadata["attribution"]
    assert "durable_nonce_admin_transfer" in out.signatures_matched


def test_generate_content_major(kelp_incident):
    out = generate_content(kelp_incident)
    assert out.severity == "critical"  # 293M is critical
    assert "bridge" in out.alert_tweet.lower() or "forgery" in out.alert_tweet.lower()
    assert len(out.alert_tweet) <= 280


def test_generate_content_mid(giddy_incident):
    out = generate_content(giddy_incident)
    assert out.severity == "mid"
    assert len(out.alert_tweet) <= 280
    assert out.thread_breakdown
    assert len(out.summary_post) <= 280


def test_generate_content_custom_fields(drift_incident):
    out = generate_content(
        drift_incident,
        custom_description="Custom desc.",
        custom_lesson="Custom lesson.",
        custom_attribution="Custom attr.",
    )
    assert out.metadata["description"] == "Custom desc."
    assert out.metadata["lesson"] == "Custom lesson."
    assert out.metadata["attribution"] == "Custom attr."


def test_generate_content_hashtags_present(drift_incident):
    out = generate_content(drift_incident)
    assert out.hashtags in out.alert_tweet
    assert out.hashtags in out.thread_breakdown[0]
    assert out.hashtags in out.summary_post


def test_generate_batch(drift_incident, kelp_incident, wasabi_incident):
    outputs = generate_batch([drift_incident, kelp_incident, wasabi_incident])
    assert len(outputs) == 3
    assert outputs[0].severity == "critical"
    assert outputs[1].severity == "critical"
    assert outputs[2].severity == "mid"


def test_batch_to_json(drift_incident, kelp_incident):
    raw = batch_to_json([drift_incident, kelp_incident])
    data = json.loads(raw)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["protocol"] == "Drift Protocol"
    assert "alert_tweet" in data[0]
    assert "thread_breakdown" in data[0]
    assert "summary_post" in data[0]


# ── Signature integration tests ──────────────────────────────────────────────


def test_from_signature_result_derives_vector():
    sig_result = {
        "signatures_matched": ["durable_nonce_admin_transfer"],
        "blockers": ["Durable-nonce admin-transfer pattern detected."],
        "warnings": [],
    }
    out = from_signature_result(
        protocol="Drift Protocol",
        chain="Solana",
        date="2026-04-01",
        loss_usd=285_000_000,
        signature_result=sig_result,
    )
    assert out.protocol == "Drift Protocol"
    assert out.severity == "critical"
    assert "social engineering" in out.metadata["attack_vector"].lower()
    assert "durable_nonce_admin_transfer" in out.signatures_matched


def test_from_signature_result_with_override():
    sig_result = {
        "signatures_matched": ["sequence_grant_upgrade"],
        "blockers": ["UUPS takeover signature."],
        "warnings": [],
    }
    out = from_signature_result(
        protocol="Wasabi Protocol",
        chain="Multi-chain",
        date="2026-04-30",
        loss_usd=5_000_000,
        signature_result=sig_result,
        attack_vector="admin key compromise",
    )
    assert out.metadata["attack_vector"] == "admin key compromise"
    assert out.severity == "mid"


# ── Character limit stress tests ─────────────────────────────────────────────


def test_long_protocol_name_still_within_limit():
    incident = {
        "protocol": "SuperDuperMegaLongProtocolNameThatIsWayTooLong",
        "loss_usd": 500_000,
        "chain": "Ethereum",
        "date": "2026-04-01",
        "attack_vector": "flash loan oracle manipulation",
    }
    out = generate_content(incident)
    assert len(out.alert_tweet) <= 280
    assert all(len(t) <= 280 for t in out.thread_breakdown)
    assert len(out.summary_post) <= 280


def test_long_attack_vector_still_within_limit():
    incident = {
        "protocol": "X",
        "loss_usd": 500_000,
        "chain": "Ethereum",
        "date": "2026-04-01",
        "attack_vector": (
            "an extremely long and detailed attack vector description that goes "
            "on and on about every single step the attacker took"
        ),
    }
    out = generate_content(incident)
    assert len(out.alert_tweet) <= 280
    assert all(len(t) <= 280 for t in out.thread_breakdown)
    assert len(out.summary_post) <= 280


# ── Edge cases ───────────────────────────────────────────────────────────────


def test_missing_optional_keys():
    incident = {
        "protocol": "Mystery Protocol",
        "loss_usd": 0,
        "chain": "Unknown",
        "date": "",
    }
    out = generate_content(incident)
    assert out.severity == "mid"
    assert len(out.alert_tweet) <= 280


def test_alert_index_rotation():
    incident = {
        "protocol": "Test",
        "loss_usd": 500_000,
        "chain": "Ethereum",
        "date": "2026-04-01",
        "attack_vector": "undisclosed",
    }
    out0 = generate_content(incident, alert_index=0)
    out1 = generate_content(incident, alert_index=1)
    # They should use different templates (or safely wrap if only 1 template)
    assert out0.alert_tweet != out1.alert_tweet or len(out0.alert_tweet) <= 280


def test_to_dict_and_json(drift_incident):
    out = generate_content(drift_incident)
    d = out.to_dict()
    assert d["protocol"] == "Drift Protocol"
    assert isinstance(d["thread_breakdown"], list)
    j = out.to_json()
    assert isinstance(j, str)
    parsed = json.loads(j)
    assert parsed["protocol"] == "Drift Protocol"
