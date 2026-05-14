"""Tests for wallet alert quality gates and no-send previews."""

import json

import pytest

from guard0.wallet_alerts import (
    build_wallet_alert_preview,
    normalize_evm_address,
    wallet_alert_quality_policy,
)


ADDRESS = "0x885b0892D241Cb5033C9995e09cA521d54f936b5"


def test_wallet_alert_preview_promotes_deny_intent_without_sending():
    preview = build_wallet_alert_preview(
        ADDRESS,
        intent={
            "action": "approve",
            "mode": "live_transaction",
            "requires_signature": True,
            "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        },
        now="2026-05-14T12:00:00+00:00",
    )

    assert preview["schema"] == "0guard.wallet_alert_preview.v1"
    assert preview["mode"] == "preview_no_send"
    assert preview["wallet"]["address"] == normalize_evm_address(ADDRESS)
    assert preview["decision"]["decision"] == "deny"
    assert preview["decision"]["zeroG"]["anchor_requested"] is True
    assert preview["decision"]["zeroG"]["storage_requested"] is True
    assert preview["alertCount"] == 1
    alert = preview["alerts"][0]
    assert alert["score"] >= preview["qualityPolicy"]["minAlertScore"]
    assert alert["sendPolicy"]["telegramEligibleAfterOptIn"] is True
    assert alert["sendPolicy"]["wouldSendFromWorkbench"] is False
    assert "policy_engine" in alert["sourceIds"]
    assert "Unlimited" in preview["telegramPreview"]
    assert preview["safety"]["telegramSendEnabled"] is False
    assert preview["safety"]["transactionBroadcastingEnabled"] is False


def test_wallet_alert_preview_keeps_safe_readonly_check_as_digest_only():
    preview = build_wallet_alert_preview(
        ADDRESS,
        intent={
            "action": "read_balance",
            "mode": "simulation",
            "method": "eth_getBalance",
            "requires_signature": False,
        },
    )

    assert preview["decision"]["decision"] == "allow"
    assert preview["alertCount"] == 0
    assert preview["alerts"] == []
    assert preview["digestOnly"]
    assert "No direct wallet alert" in preview["telegramPreview"]
    assert preview["wallet"]["liveProbes"]["attempted"] == 0
    assert all(row["status"] == "not_checked" for row in preview["wallet"]["liveProbes"]["probes"])


def test_wallet_alert_preview_titles_accounting_invariant_alerts():
    preview = build_wallet_alert_preview(
        ADDRESS,
        intent={
            "action": "donate negative amounts",
            "mode": "live_transaction",
            "requires_signature": True,
            "prompt_text": "Donate negative amounts without strict lower bounds.",
        },
    )

    assert preview["decision"]["decision"] == "deny"
    assert preview["alerts"][0]["title"] == "Accounting-invariant exploit attempt"
    assert "Negative amount" in preview["alerts"][0]["whyItMatters"]


def test_wallet_alert_quality_policy_is_no_send_by_default():
    policy = wallet_alert_quality_policy()

    assert policy["schema"] == "0guard.wallet_alert_quality_policy.v1"
    assert policy["minAlertScore"] >= 0.7
    assert policy["workbenchSendEnabled"] is False
    assert policy["telegramSendEnabled"] is False
    assert "opt-in" in " ".join(policy["sendEligibilityRules"])


def test_wallet_alert_preview_rejects_bad_address_and_alert_limit():
    with pytest.raises(ValueError):
        build_wallet_alert_preview("not-an-address")
    with pytest.raises(ValueError):
        build_wallet_alert_preview(ADDRESS, max_alerts=0)
    with pytest.raises(ValueError):
        build_wallet_alert_preview(ADDRESS, max_alerts=21)


def test_wallet_alert_preview_does_not_expose_secrets():
    preview = build_wallet_alert_preview(
        ADDRESS,
        intent={
            "action": "scout",
            "prompt_text": "My private key is 0xabc123...",
        },
    )

    encoded = json.dumps(preview).lower()
    assert "private_key" not in encoded
    assert "seed phrase" not in encoded
    assert "telegram_send" not in encoded
