"""Tests for converting live OSINT signals into detector candidates."""

import pytest

from guard0.live_detector_candidates import live_detector_candidates


SAMPLE_SIGNALS = {
    "schema": "0guard.osint_signals.v1",
    "live": True,
    "signalCount": 2,
    "sourceStatus": [
        {
            "sourceId": "defillama_hacks",
            "adapter": "defillama_hacks",
            "status": "ok",
        }
    ],
    "signals": [
        {
            "schema": "0guard.osint_signal.v1",
            "sourceId": "defillama_hacks",
            "sourceLink": "https://defillama.com/hacks",
            "recordHash": "a" * 64,
            "observedAt": "2026-05-12",
            "signalType": "crypto_incident",
            "title": "Aurellion",
            "amountUsd": 456000,
            "chains": ["Arbitrum"],
            "classification": "Protocol Logic",
            "technique": "Uninitialized Proxy Exploit",
            "targetType": "RWA",
            "bridgeHack": False,
        },
        {
            "schema": "0guard.osint_signal.v1",
            "sourceId": "defillama_hacks",
            "sourceLink": "https://defillama.com/hacks",
            "recordHash": "b" * 64,
            "observedAt": "2026-05-15",
            "signalType": "crypto_incident",
            "title": "Thorchain DEX",
            "amountUsd": 10000000,
            "chains": ["Bitcoin", "Ethereum", "Base"],
            "classification": "Protocol Logic",
            "technique": "Vault Churn Address Poisoning",
            "targetType": "DeFi Protocol",
            "bridgeHack": True,
        },
    ],
}


def test_live_detector_candidates_turn_public_signals_into_reviewable_work():
    packet = live_detector_candidates(live=True, limit=5, signals_payload=SAMPLE_SIGNALS)

    assert packet["schema"] == "0guard.detector_candidates.v1"
    assert packet["live"] is True
    assert packet["mode"] == "source_signal_to_regression_candidate"
    assert packet["signalCount"] == 2
    assert packet["candidateCount"] == 2
    assert packet["highPriorityCount"] == 2
    assert packet["safety"]["rawPayloadsReturned"] is False
    assert packet["safety"]["transactionSigningEnabled"] is False
    assert packet["safety"]["candidatePromotionAutomatic"] is False
    assert any("regression test" in gate for gate in packet["promotionGate"])

    aurellion = next(candidate for candidate in packet["candidates"] if candidate["title"] == "Aurellion")
    assert aurellion["priority"] == "high"
    assert aurellion["chainFocus"] == {
        "name": "Arbitrum",
        "caip2": "eip155:42161",
        "recognized": True,
    }
    assert aurellion["families"][0]["id"] == "proxy_initialization_guard"
    assert aurellion["preflightSeed"]["action"] == "admin_call"
    assert aurellion["preflightSeed"]["requires_signature"] is True
    assert aurellion["currentSignaturePreview"]["decision"] in {"allow", "review", "deny"}
    assert aurellion["rawPayloadReturned"] is False
    assert aurellion["nextRegressionTest"].startswith(
        "test_live_candidate_proxy_initialization_guard_"
    )

    thorchain = next(candidate for candidate in packet["candidates"] if candidate["title"] == "Thorchain DEX")
    assert thorchain["priority"] == "critical"
    family_ids = {family["id"] for family in thorchain["families"]}
    assert "address_poisoning_flow_guard" in family_ids
    assert thorchain["preflightSeed"]["source_record_hash"] == "b" * 64


def test_live_detector_candidates_skip_irrelevant_research_links():
    packet = live_detector_candidates(
        live=False,
        signals_payload={
            "schema": "0guard.osint_signals.v1",
            "live": False,
            "signalCount": 1,
            "sourceStatus": [],
            "signals": [
                {
                    "sourceId": "chainalysis_blog_rss",
                    "observedAt": "2026-05-16T00:00:00Z",
                    "signalType": "research_link",
                    "title": "Policy update unrelated to threat detection",
                    "link": "https://example.test/post",
                    "securityRelevant": False,
                }
            ],
        },
    )

    assert packet["candidateCount"] == 0
    assert packet["candidates"] == []


def test_live_detector_candidates_reject_bad_limits():
    with pytest.raises(ValueError, match="limit must be between 1 and 50"):
        live_detector_candidates(limit=0)
