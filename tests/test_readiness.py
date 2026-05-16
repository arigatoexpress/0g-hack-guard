"""Tests for the operational readiness profile."""

from guard0.readiness import production_readiness


def test_production_readiness_is_honest_and_non_mutating(monkeypatch):
    monkeypatch.delenv("ZGG_CHAIN_RPC", raising=False)
    monkeypatch.delenv("ZGG_CHAIN_ID", raising=False)
    monkeypatch.delenv("ZGG_RECEIPT_CONTRACT", raising=False)

    result = production_readiness()

    assert result["schema"] == "0guard.readyz.v1"
    assert result["mode"] == "operational_readiness_no_side_effects"
    assert result["readiness"] == "production_review"
    checks = {check["id"]: check for check in result["checks"]}
    assert checks["mainnet_verifier_profile"]["status"] == "review"
    assert checks["mainnet_proof_file"]["status"] == "ok"
    assert checks["detector_coverage"]["status"] == "ok"
    assert checks["reputation_shadow_cache"]["status"] == "ok"
    assert checks["telegram_state_store"]["status"] == "review"
    assert result["safety"]["networkCalls"] is False
    assert result["safety"]["transactionSigningEnabled"] is False
    assert result["operatorPromotions"][0]["env"]["ZGG_CHAIN_ID"] == "16661"


def test_production_readiness_detects_mainnet_runtime_env(monkeypatch):
    monkeypatch.setenv("ZGG_CHAIN_RPC", "https://evmrpc.0g.ai")
    monkeypatch.setenv("ZGG_CHAIN_ID", "16661")
    monkeypatch.setenv("ZGG_RECEIPT_CONTRACT", "0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc")

    result = production_readiness()
    checks = {check["id"]: check for check in result["checks"]}

    assert checks["mainnet_verifier_profile"]["status"] == "ok"
    assert checks["mainnet_verifier_profile"]["detail"]["receiptContractConfigured"] is True
    assert result["readiness"] == "production_review"


def test_production_readiness_detects_file_backed_telegram_store(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_OPT_IN_STORE_PATH", str(tmp_path / "telegram-opt-ins.json"))

    result = production_readiness()
    checks = {check["id"]: check for check in result["checks"]}

    assert checks["telegram_state_store"]["status"] == "ok"
    assert checks["telegram_state_store"]["detail"]["storeMode"] == "local_json"
    assert checks["telegram_state_store"]["detail"]["persistentStoreConfigured"] is True
