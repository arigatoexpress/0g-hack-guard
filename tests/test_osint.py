"""Tests for rights-aware OSINT source and signal surfaces."""

import json

from guard0.osint import (
    hackathon_submission_brief,
    load_source_registry,
    osint_readiness,
    osint_signals,
    signature_map,
    source_registry_public,
)


def test_source_registry_exposes_rights_metadata_without_raw_payloads():
    registry = load_source_registry()
    public = source_registry_public()

    assert registry["schema"] == "0guard.osint_source_registry.v1"
    assert public["schema"] == "0guard.osint_source_registry.v1"
    assert public["sourceCount"] >= 8
    assert public["rightsPolicy"]["rawPayloadResaleAllowed"] is False
    source_ids = {source["id"] for source in public["sources"]}
    assert "defillama_hacks" in source_ids
    assert "chainalysis_blog_rss" in source_ids
    assert "forta_labelled_datasets" in source_ids


def test_osint_readiness_can_run_without_live_network():
    readiness = osint_readiness(live=False)

    assert readiness["schema"] == "0guard.osint_readiness.v1"
    assert readiness["live"] is False
    assert readiness["attemptedLiveChecks"] == 0
    assert readiness["readinessRatio"] is None
    assert readiness["safety"]["readOnly"] is True
    assert readiness["safety"]["rawPayloadsReturned"] is False
    assert all(source["status"] == "not_checked" for source in readiness["sources"])


def test_osint_signals_live_disabled_reports_catalog_status_only():
    signals = osint_signals(live=False, limit=5)

    assert signals["schema"] == "0guard.osint_signals.v1"
    assert signals["live"] is False
    assert signals["signalCount"] == 0
    assert signals["safety"]["rawPayloadsReturned"] is False
    assert any(item["status"] == "live_fetch_disabled" for item in signals["sourceStatus"])
    encoded = json.dumps(signals)
    assert "private_key" not in encoded.lower()


def test_signature_map_explains_coverage_gaps():
    mapping = signature_map()

    assert mapping["schema"] == "0guard.signature_map.v1"
    assert mapping["incidentCount"] == 28
    assert mapping["matchedCount"] >= 12
    assert mapping["gapCount"] >= 1
    assert mapping["topGaps"]
    drift = next(row for row in mapping["rows"] if row["protocol"] == "Drift Protocol")
    assert drift["matched"] is True
    assert drift["gap"] is None
    undisclosed = next(row for row in mapping["rows"] if row["attackVector"] == "undisclosed")
    assert undisclosed["matched"] is False
    assert undisclosed["recommendedDetector"]


def test_hackathon_submission_brief_is_operator_ready():
    brief = hackathon_submission_brief()

    assert brief["schema"] == "0guard.hackathon_submission_brief.v1"
    assert brief["project"]["name"] == "0guard"
    assert brief["deadline"]["submissionDeadline"] == "2026-05-16T23:59:00+08:00"
    assert brief["dataProduct"]["incidentCount"] == 28
    assert brief["dataProduct"]["sourceRegistryCount"] >= 8
    assert any("Deploy PolicyReceiptAnchor" in item for item in brief["operatorRequired"])
    assert any("Do not claim live mainnet writes" in item for item in brief["claimsToAvoid"])
