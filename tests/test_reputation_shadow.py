"""Tests for the derived reputation shadow cache."""

from guard0.reputation_shadow import (
    build_reputation_shadow_cache,
    demo_reputation_shadow_payload,
)


def test_reputation_shadow_cache_composes_reviewed_payloads_without_raw_leakage():
    result = build_reputation_shadow_cache(demo_reputation_shadow_payload())

    assert result["schema"] == "0guard.reputation_shadow_cache.v1"
    assert result["mode"] == "derived_shadow_cache_no_fetch_no_raw_resale"
    assert result["sourceCount"] == 3
    assert result["acceptedPayloadCount"] == 3
    assert result["rejectedPayloadCount"] == 0
    assert result["derivedSignalCount"] == 3
    assert result["probePreview"]["decision"]["decision"] == "deny"
    assert result["cacheReceipt"]["zeroGChainReady"] is True
    assert result["cacheReceipt"]["liveAnchorPerformed"] is False
    assert result["sourceRights"]["rawPayloadsReturned"] is False
    assert result["sourceRights"]["rawPayloadResaleAllowed"] is False
    assert result["safety"]["networkCalls"] is False
    assert result["safety"]["telegramSendsEnabled"] is False
    assert result["safety"]["transactionSigningEnabled"] is False
    assert "docs.0g.ai.evil.example/claim" not in str(result)
    assert "docs.0g.ai.evil.example" not in str(result)


def test_reputation_shadow_cache_accepts_single_adapter_payload():
    result = build_reputation_shadow_cache(
        {
            "sourceId": "phishdestroy_destroylist",
            "subject": {"url": "https://support.0g.ai.evil.example"},
            "payload": {"active_domains": ["support.0g.ai.evil.example"]},
        }
    )

    assert result["sourceCount"] == 1
    assert result["sources"][0]["sourceId"] == "phishdestroy_destroylist"
    assert result["sources"][0]["decision"] == "deny"
    assert result["activationQueue"][0]["sourceId"] == "phishdestroy_destroylist"
    assert result["probePreview"]["decision"]["decision"] == "deny"
    assert "support.0g.ai.evil.example" not in str(result)


def test_reputation_shadow_cache_reports_rejected_payloads_safely():
    result = build_reputation_shadow_cache(
        {
            "subject": {"url": "https://docs.0g.ai.evil.example/claim"},
            "adapterPayloads": [
                {"sourceId": "cryptoscamdb", "payload": {"reported_count": 1}},
                {"sourceId": "not_real", "payload": {"url": "https://private.example/path"}},
            ],
        }
    )

    assert result["acceptedPayloadCount"] == 1
    assert result["rejectedPayloadCount"] == 1
    assert result["rejectedPayloads"] == [
        {
            "sourceId": "not_real",
            "accepted": False,
            "error": "unsupported sourceId: not_real",
        }
    ]
    assert "private.example" not in str(result)
