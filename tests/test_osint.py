"""Tests for rights-aware OSINT source and signal surfaces."""

import json

from guard0.osint import (
    hackathon_submission_brief,
    incident_provenance_matrix,
    load_source_registry,
    osint_readiness,
    osint_signals,
    signature_map,
    source_registry_public,
)


DEFILLAMA_SAMPLE_RECORDS = [
    {
        "date": 1775001600,
        "name": "Drift Trade",
        "amount": 285_000_000,
        "chain": ["Solana"],
        "classification": "Infrastructure",
        "technique": "Compromised Admin + Fake Token Price Manipulation",
        "targetType": "DeFi Protocol",
        "bridgeHack": False,
    },
    {
        "date": 1776470400,
        "name": "Kelp",
        "amount": 293_000_000,
        "chain": ["Ethereum", "Base"],
        "classification": "Protocol Logic",
        "technique": "LayerZero OFT bridge exploit",
        "targetType": "DeFi Protocol",
        "bridgeHack": True,
    },
    {
        "date": 1777507200,
        "name": "Wasabi Perps",
        "amount": 5_500_000,
        "chain": ["Ethereum", "Base", "Berachain", "Blast"],
        "classification": "Infrastructure",
        "technique": "Admin Key Compromised",
        "targetType": "DeFi Protocol",
        "bridgeHack": False,
    },
]


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


def test_incident_provenance_matrix_correlates_source_records():
    matrix = incident_provenance_matrix(defillama_records=DEFILLAMA_SAMPLE_RECORDS)

    assert matrix["schema"] == "0guard.incident_provenance_matrix.v1"
    assert matrix["live"] is False
    assert matrix["sourceStatus"]["status"] == "injected_records"
    assert matrix["coverage"]["incidentCount"] == 28
    assert matrix["coverage"]["withMatchedEvidence"] == 3
    assert matrix["coverage"]["highConfidenceEvidenceCount"] >= 2
    assert matrix["safety"]["rawPayloadsReturned"] is False

    drift = next(row for row in matrix["rows"] if row["protocol"] == "Drift Protocol")
    assert drift["status"] == "source_linked"
    assert drift["evidence"][0]["matchedName"] == "Drift Trade"
    assert drift["evidence"][0]["confidence"] >= 0.85
    assert drift["evidence"][0]["recordHash"]

    denaria = next(row for row in matrix["rows"] if row["protocol"] == "Denaria Finance")
    assert denaria["status"] == "aggregate_only"
    assert denaria["evidence"] == []
    assert "trusted incident writeup" in denaria["recommendedNextStep"]


def test_incident_provenance_matrix_uses_reviewed_cache_without_network():
    matrix = incident_provenance_matrix()

    assert matrix["schema"] == "0guard.incident_provenance_matrix.v1"
    assert matrix["sourceStatus"]["status"] == "reviewed_cache"
    assert matrix["sourceStatus"]["evidenceMode"] == "reviewed_derived_cache"
    assert matrix["coverage"]["withMatchedEvidence"] >= 20
    assert matrix["coverage"]["aggregateOnlyCount"] <= 8
    assert matrix["safety"]["rawPayloadsReturned"] is False

    silo = next(row for row in matrix["rows"] if row["protocol"] == "Silo V2")
    assert silo["status"] == "aggregate_only"
    drift = next(row for row in matrix["rows"] if row["protocol"] == "Drift Protocol")
    assert drift["evidence"][0]["cacheReviewStatus"] == "derived_pending_human_promotion"


def test_hackathon_submission_brief_is_operator_ready():
    brief = hackathon_submission_brief()

    assert brief["schema"] == "0guard.hackathon_submission_brief.v1"
    assert brief["project"]["name"] == "0guard"
    assert brief["deadline"]["submissionDeadline"] == "2026-05-16T23:59:00+08:00"
    assert brief["dataProduct"]["incidentCount"] == 28
    assert brief["dataProduct"]["sourceRegistryCount"] >= 8
    assert brief["trackRecommendation"]["primary"].startswith("Track 5")
    assert brief["submissionRequirements"]["publicXPost"]["mandatory"] is True
    assert "#0GHackathon" in brief["submissionRequirements"]["publicXPost"]["requiredHashtags"]
    assert any("proof trails" in item for item in brief["competitivePositioning"])
    assert any("Deploy PolicyReceiptAnchor" in item for item in brief["operatorRequired"])
    assert any("Do not claim live mainnet writes" in item for item in brief["claimsToAvoid"])
