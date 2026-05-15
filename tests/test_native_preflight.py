"""Tests for the unified native preflight surface."""

from guard0.native_preflight import build_native_preflight, hackathon_strategy


def test_native_preflight_denies_live_ika_sweep_before_signer():
    result = build_native_preflight(
        {
            "surface": "ika_dwallets",
            "sourceProject": "ikavery",
            "operation": "sweep",
            "chain": "solana:devnet",
            "liveSigning": True,
            "intentText": "Autonomous agent proposes a recovery sweep through a dWallet signer.",
        }
    )

    assert result["schema"] == "0guard.native_preflight.v1"
    assert result["decision"] == "deny"
    assert result["receipt"]["zeroGStorageReady"] is True
    assert result["receipt"]["liveUploadPerformed"] is False
    assert result["safety"]["transactionSigningEnabled"] is False
    assert {component["id"] for component in result["components"]} >= {
        "core_policy",
        "ika_preflight",
        "external_guardrail",
    }


def test_native_preflight_reviews_ton_without_address_and_allows_read_only_evm():
    ton = build_native_preflight(
        {
            "surface": "ton",
            "operation": "preview_wallet",
            "chain": "ton:mainnet",
            "intentText": "Preview Telegram wallet risk before any wallet prompt.",
        }
    )
    evm = build_native_preflight(
        {
            "surface": "evm",
            "operation": "read_status",
            "chain": "eip155:8453",
            "intent": {"mode": "preview"},
        }
    )

    assert ton["decision"] == "review"
    assert any(component["id"] == "ton_risk_passport" for component in ton["components"])
    assert evm["decision"] == "allow"
    assert evm["safety"]["bridgingEnabled"] is False


def test_hackathon_strategy_is_0g_first_and_source_cited():
    strategy = hackathon_strategy()

    assert strategy["schema"] == "0guard.hackathon_strategy.v1"
    assert strategy["opportunities"][0]["id"] == "0g_apac_final_review"
    assert strategy["thesis"]["0gFirst"].startswith("0G remains")
    assert all(opportunity["sources"] for opportunity in strategy["opportunities"])
    assert strategy["safety"]["moneyMovementEnabled"] is False
