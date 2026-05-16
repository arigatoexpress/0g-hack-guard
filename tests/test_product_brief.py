"""Tests for the plain-English 0guard product brief."""

from guard0.product_brief import product_brief


def test_product_brief_explains_live_system_without_live_actions():
    brief = product_brief()

    assert brief["schema"] == "0guard.product_brief.v1"
    assert brief["name"] == "0guard"
    assert "pre-wallet firewall" in brief["oneLiner"]
    assert len(brief["plainEnglish"]) >= 5
    systems = {item["id"]: item for item in brief["builtSystems"]}
    assert {
        "intent_firewall",
        "incident_intelligence",
        "reputation_probe",
        "telegram_mini_app",
        "0g_receipts",
        "developer_kit",
        "cross_ecosystem_guardrails",
    } <= set(systems)
    assert systems["incident_intelligence"]["proof"]["coverageRatio"] == 1.0
    assert brief["liveProof"]["miniApp"].endswith("/telegram")
    assert brief["socialPositioning"]["xThreadFile"].endswith("_x_thread.json")
    assert brief["safety"]["readOnly"] is True
    assert brief["safety"]["socialPostingEnabled"] is False
    assert brief["safety"]["transactionSigningEnabled"] is False
