"""Tests for incident-data loading, validation, and detection coverage."""

from guard0.incident_data import (
    detection_coverage,
    filter_incidents,
    incident_summary,
    load_incident_dataset,
    validate_incident_dataset,
)


def test_incident_dataset_validates_cleanly():
    dataset = load_incident_dataset()
    report = validate_incident_dataset(dataset)

    assert report.ok is True
    assert report.incident_count == 28
    assert report.total_loss_usd == 634_862_000
    assert report.computed_loss_usd == report.total_loss_usd
    assert len(report.fingerprint) == 64
    assert report.errors == ()
    assert report.warnings == ("2 incident records missing per-incident source_urls",)

    drift = next(item for item in dataset["incidents"] if item["protocol"] == "Drift Protocol")
    assert drift["source_urls"] == ["https://defillama.com/hacks"]
    assert drift["derived_source_evidence"][0]["source_id"] == "defillama_hacks"


def test_incident_summary_exposes_top_losses_and_counts():
    summary = incident_summary()

    assert summary["schema"] == "0guard.incident_summary.v1"
    assert summary["validation"]["ok"] is True
    assert summary["stats"]["incidentCount"] == 28
    assert summary["stats"]["topLosses"][0]["protocol"] == "Kelp DAO"
    assert summary["stats"]["topLosses"][1]["protocol"] == "Drift Protocol"
    assert summary["stats"]["topLosses"][1]["source_urls"] == ["https://defillama.com/hacks"]
    assert summary["stats"]["attackVectorCounts"]["undisclosed"] >= 1


def test_filter_incidents_limits_and_filters():
    ethereum = filter_incidents(chain="Ethereum", min_loss_usd=100_000, limit=3)

    assert len(ethereum) == 3
    assert all(item["chain"] == "Ethereum" for item in ethereum)
    assert ethereum[0]["loss_usd"] >= ethereum[-1]["loss_usd"]
    assert ethereum[0]["derived_source_evidence"][0]["record_hash"]


def test_detection_coverage_runs_dataset_through_signature_engine():
    coverage = detection_coverage()

    assert coverage["schema"] == "0guard.detection_coverage.v1"
    assert coverage["incidentCount"] == 28
    assert coverage["coveredCount"] >= 18
    assert 0 < coverage["coverageRatio"] <= 1
    drift = next(row for row in coverage["coverage"] if row["incident"]["protocol"] == "Drift Protocol")
    assert drift["matched"] is True
    assert drift["blockerCount"] >= 1
