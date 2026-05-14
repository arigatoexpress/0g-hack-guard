"""Tests for crypto_hack_guard signature detection."""

from guard0.crypto_hack_guard import (
    check_crypto_hack_signatures,
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


def test_negative_amount_invariant_blocks():
    result = check_crypto_hack_signatures({
        "action": "donate negative amounts",
        "prompt_text": "Donation flow credits negative amounts without strict lower bounds.",
    })
    assert any("Negative amount" in b for b in result.blockers)
    assert "negative_amount_invariant" in result.signatures_matched


def test_accounting_numeric_and_gateway_invariants_warn():
    result = check_crypto_hack_signatures({
        "action": "settlement review",
        "prompt_text": (
            "BurnAddress accounting bug caused balance manipulation. "
            "A signedness mismatch in settlement math extracted excess collateral. "
            "GatewayEVM halted all cross-chain activity while nonce replay protection was patched."
        ),
    })
    assert any("Burn/mint" in w for w in result.warnings)
    assert any("Signedness" in w for w in result.warnings)
    assert any("Cross-chain gateway" in w for w in result.warnings)
    assert "token_accounting_invariant" in result.signatures_matched
    assert "numeric_type_invariant" in result.signatures_matched
    assert "cross_chain_gateway_invariant" in result.signatures_matched


def test_hot_wallet_opsec_warns():
    result = check_crypto_hack_signatures({
        "action": "hot wallet compromise",
        "prompt_text": "Hot wallet incident with unauthorized outbound transfers and weak HSM controls.",
    })
    assert any("Hot-wallet" in w for w in result.warnings)
    assert "hot_wallet_opsec_context" in result.signatures_matched
