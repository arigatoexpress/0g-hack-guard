"""Tests for next-hackathon integration plans."""

from guard0.hackathon_integrations import (
    arbitrum_integration_plan,
    metamask_integration_plan,
    next_hackathon_plan,
)


def test_next_hackathon_plan_is_source_cited_and_no_side_effects():
    plan = next_hackathon_plan()

    assert plan["schema"] == "0guard.next_hackathon_plan.v1"
    assert plan["opportunities"][0]["id"] == "arbitrum_open_house_london_online_buildathon"
    assert plan["opportunities"][0]["timing"]["submissionDeadline"] == "2026-06-14"
    assert any("MetaMask" in opportunity["name"] for opportunity in plan["opportunities"])
    assert all(opportunity["officialSources"] for opportunity in plan["opportunities"])
    assert plan["safety"]["transactionSigningEnabled"] is False
    assert plan["safety"]["moneyMovementEnabled"] is False


def test_arbitrum_plan_uses_catalog_targets_and_keeps_0g_anchor():
    plan = arbitrum_integration_plan()

    assert plan["schema"] == "0guard.arbitrum_integration_plan.v1"
    ids = {network["id"] for network in plan["networks"]}
    assert {"arbitrum_one", "arbitrum_nova", "arbitrum_sepolia"} <= ids
    assert any("0G proof context" in step for step in plan["demoPath"])
    assert plan["safety"]["bridgingEnabled"] is False


def test_metamask_plan_is_pre_signer_not_wallet_claim():
    plan = metamask_integration_plan()

    assert plan["schema"] == "0guard.metamask_integration_plan.v1"
    assert "not a wallet" in plan["positioning"]
    layer_ids = {layer["id"] for layer in plan["integrationLayers"]}
    assert {"connect_wrapper", "snap_transaction_signature_insights"} <= layer_ids
    assert any("expiry" in control for control in plan["minimumControls"])
    assert plan["safety"]["transactionSigningEnabled"] is False
