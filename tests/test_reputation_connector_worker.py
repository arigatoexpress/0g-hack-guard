"""Tests for live reputation connector workers."""

import json

import pytest

from guard0.reputation_connector_worker import (
    PHISHDESTROY_ACTIVE_DOMAINS_URL,
    phishdestroy_active_domains_snapshot,
    reputation_connector_snapshot,
)


def test_phishdestroy_snapshot_fetches_and_returns_derived_only(monkeypatch):
    def fake_fetch(url: str, *, timeout_seconds: float, max_bytes: int):
        assert url == PHISHDESTROY_ACTIVE_DOMAINS_URL
        assert timeout_seconds == 6.0
        assert max_bytes >= 1_000_000
        return {
            "ok": True,
            "statusCode": 200,
            "contentType": "application/json",
            "contentLength": 53,
            "etag": '"fixture"',
            "lastModified": None,
            "elapsedMs": 12,
            "body": json.dumps(
                [
                    "docs.0g.ai.evil.example",
                    "wallet-drainer.example",
                    "docs.0g.ai.evil.example",
                ]
            ).encode(),
            "error": None,
        }

    monkeypatch.setattr("guard0.reputation_connector_worker._fetch_url", fake_fetch)

    snapshot = phishdestroy_active_domains_snapshot(
        live=True,
        subject_url="https://docs.0g.ai.evil.example/claim",
    )

    assert snapshot["schema"] == "0guard.reputation_connector_snapshot.v1"
    assert snapshot["mode"] == "live_fetch_derived_only"
    assert snapshot["live"] is True
    assert snapshot["fetch"]["status"] == "ok"
    assert snapshot["fetch"]["parsedDomainCount"] == 2
    assert snapshot["fetch"]["sampledEvidenceCount"] == 1
    assert snapshot["subject"]["matchedInFeed"] is True
    assert snapshot["subject"]["rawDomainReturned"] is False
    assert snapshot["derivedEvidence"][0]["sourceId"] == "phishdestroy_destroylist"
    assert snapshot["derivedEvidence"][0]["verdict"] == "malicious"
    assert snapshot["reputationPreview"]["decision"]["decision"] == "deny"
    assert snapshot["snapshotReceipt"]["zeroGChainReady"] is True
    assert snapshot["rightsPolicy"]["rawDomainsReturned"] is False
    assert snapshot["safety"]["networkCalls"] is True
    assert snapshot["safety"]["rawPayloadsReturned"] is False
    encoded = json.dumps(snapshot)
    assert "docs.0g.ai.evil.example" not in encoded
    assert "wallet-drainer.example" not in encoded


def test_phishdestroy_snapshot_no_network_by_default():
    snapshot = phishdestroy_active_domains_snapshot(live=False, subject_url="docs.0g.ai")

    assert snapshot["mode"] == "live_fetch_disabled"
    assert snapshot["fetch"]["status"] == "live_fetch_disabled"
    assert snapshot["derivedEvidence"] == []
    assert snapshot["safety"]["networkCalls"] is False
    assert snapshot["safety"]["liveConnectorFetch"] is False


def test_reputation_connector_snapshot_rejects_unknown_source():
    with pytest.raises(ValueError, match="unsupported live connector"):
        reputation_connector_snapshot(source_id="not_real", live=False)
