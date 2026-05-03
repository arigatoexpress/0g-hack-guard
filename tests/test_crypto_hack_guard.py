"""Tests for crypto_hack_guard signature detection."""
import pytest

from guard0.crypto_hack_guard import (
    check_crypto_hack_signatures,
    KNOWN_MALICIOUS_ADDRESSES,
)


def test_safe_readonly_intent():
    result = check_crypto_hack_signatures({
        "action": "read_balance",
        "mode": "simulation",
        "calldata": "0x70a08231000000000000000000000000a0b86a33e6776808dc56eb68bb0a0f74ff38ffff",
    })
    assert not result.blockers
    assert not result.warnings


def test_known_malicious_address():
    addr = "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab"
    result = check_crypto_hack_signatures({
        "action": "transfer",
        "target_contract": addr,
    })
    assert any("malicious" in b.lower() for b in result.blockers)
    assert addr.lower() in [i.lower() for i in result.iocs_hit]


def test_critical_selector_transfer_ownership():
    result = check_crypto_hack_signatures({
        "action": "upgrade",
        "calldata": "0xf2fde38b000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    })
    assert any("transferOwnership" in b for b in result.blockers)
    assert any("critical_selector" in s for s in result.signatures_matched)


def test_unlimited_approval():
    result = check_crypto_hack_signatures({
        "action": "approve",
        "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    })
    assert any("Unlimited" in b for b in result.blockers)


def test_durable_nonce_soceng():
    result = check_crypto_hack_signatures({
        "action": "sign",
        "prompt_text": "Please pre-sign this durable nonce transaction to transfer admin powers.",
    })
    assert any("durable-nonce" in b.lower() for b in result.blockers)


def test_drain_language():
    result = check_crypto_hack_signatures({
        "action": "emergency_withdraw",
        "prompt_text": "Drain all funds from the vault immediately.",
    })
    assert any("Drain" in b for b in result.blockers)


def test_approve_transfer_sequence():
    result = check_crypto_hack_signatures({
        "action": "batch",
        "steps": [
            {"action": "approve", "calldata": "0x095ea7b3..."},
            {"action": "transferFrom", "calldata": "0x23b872dd..."},
        ],
    })
    assert any("approve → transfer" in b for b in result.blockers)


def test_flash_loan_init():
    result = check_crypto_hack_signatures({
        "action": "flashLoan",
        "calldata": "0xab9c4b5d...",
    })
    assert any("Flash-loan" in w for w in result.warnings)
