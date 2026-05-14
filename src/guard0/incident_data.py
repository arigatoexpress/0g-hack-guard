"""Validated incident-data flows for 0guard."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from guard0.crypto_hack_guard import check_crypto_hack_signatures

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INCIDENT_DATA_PATH = REPO_ROOT / "data" / "april_2026_incidents.json"
DATASET_SCHEMA = "0guard.incident_dataset.v1"
SUMMARY_SCHEMA = "0guard.incident_summary.v1"
COVERAGE_SCHEMA = "0guard.detection_coverage.v1"

REQUIRED_INCIDENT_FIELDS = {
    "id",
    "date",
    "protocol",
    "loss_usd",
    "chain",
    "attack_vector",
    "description",
    "attribution",
    "lesson",
}


@dataclass(frozen=True)
class DataValidationReport:
    schema: str
    ok: bool
    incident_count: int
    total_loss_usd: int
    computed_loss_usd: int
    fingerprint: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "incidentCount": self.incident_count,
            "totalLossUsd": self.total_loss_usd,
            "computedLossUsd": self.computed_loss_usd,
            "fingerprint": self.fingerprint,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def load_incident_dataset(path: str | Path | None = None) -> dict[str, Any]:
    """Load the incident dataset from disk."""
    dataset_path = Path(path) if path else DEFAULT_INCIDENT_DATA_PATH
    with dataset_path.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)
    if not isinstance(dataset, dict):
        raise ValueError("incident dataset must be a JSON object")
    return dataset


def validate_incident_dataset(dataset: dict[str, Any]) -> DataValidationReport:
    """Validate incident data shape, totals, and provenance hints."""
    errors: list[str] = []
    warnings: list[str] = []

    meta = dataset.get("meta")
    incidents = dataset.get("incidents")
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
        meta = {}
    if not isinstance(incidents, list):
        errors.append("incidents must be a list")
        incidents = []

    seen_ids: set[int] = set()
    computed_loss = 0
    missing_source_url_count = 0
    for index, incident in enumerate(incidents):
        prefix = f"incidents[{index}]"
        if not isinstance(incident, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = sorted(REQUIRED_INCIDENT_FIELDS - set(incident))
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")

        incident_id = incident.get("id")
        if isinstance(incident_id, bool) or not isinstance(incident_id, int):
            errors.append(f"{prefix}.id must be an integer")
        elif incident_id in seen_ids:
            errors.append(f"{prefix}.id is duplicated: {incident_id}")
        else:
            seen_ids.add(incident_id)

        _validate_incident_date(incident.get("date"), f"{prefix}.date", errors)

        for field in ("protocol", "chain", "attack_vector", "description", "attribution", "lesson"):
            value = incident.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")

        loss = incident.get("loss_usd")
        if isinstance(loss, bool) or not isinstance(loss, int) or loss < 0:
            errors.append(f"{prefix}.loss_usd must be a non-negative integer")
        else:
            computed_loss += loss

        if not incident.get("source_urls"):
            missing_source_url_count += 1

    meta_count = meta.get("total_incidents")
    if meta_count is not None and meta_count != len(incidents):
        errors.append(f"meta.total_incidents={meta_count} does not match {len(incidents)} records")

    meta_loss = meta.get("total_loss_usd", 0)
    if isinstance(meta_loss, bool) or not isinstance(meta_loss, int) or meta_loss < 0:
        errors.append("meta.total_loss_usd must be a non-negative integer")
        meta_loss = 0
    elif meta_loss != computed_loss:
        errors.append(f"meta.total_loss_usd={meta_loss} does not match computed {computed_loss}")

    source_text = meta.get("source")
    source_urls = meta.get("source_urls")
    if not isinstance(source_text, str) or not source_text.strip():
        warnings.append("meta.source should name upstream sources")
    if not isinstance(source_urls, list) or not source_urls:
        warnings.append("meta.source_urls missing; provenance is aggregate-only")
    if missing_source_url_count:
        warnings.append(
            f"{missing_source_url_count} incident records missing per-incident source_urls"
        )

    fingerprint = dataset_fingerprint(dataset)
    return DataValidationReport(
        schema=DATASET_SCHEMA,
        ok=not errors,
        incident_count=len(incidents),
        total_loss_usd=int(meta_loss or 0),
        computed_loss_usd=computed_loss,
        fingerprint=fingerprint,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def incident_summary(dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build read-only incident summary stats and validation posture."""
    loaded = dataset or load_incident_dataset()
    incidents = list(loaded.get("incidents") or [])
    validation = validate_incident_dataset(loaded)

    return {
        "schema": SUMMARY_SCHEMA,
        "validation": validation.to_dict(),
        "meta": loaded.get("meta", {}),
        "stats": {
            "incidentCount": len(incidents),
            "totalLossUsd": sum(int(item.get("loss_usd", 0)) for item in incidents),
            "averageLossUsd": _safe_average([int(item.get("loss_usd", 0)) for item in incidents]),
            "chainCounts": _sorted_counter(incident.get("chain", "Unknown") for incident in incidents),
            "attackVectorCounts": _sorted_counter(
                incident.get("attack_vector", "unknown") for incident in incidents
            ),
            "attributionCounts": _sorted_counter(
                incident.get("attribution", "Unknown") for incident in incidents
            ),
            "topLosses": [
                _public_incident_fields(incident)
                for incident in sorted(incidents, key=lambda item: item.get("loss_usd", 0), reverse=True)[:5]
            ],
        },
    }


def filter_incidents(
    *,
    chain: str | None = None,
    attack_vector: str | None = None,
    min_loss_usd: int | None = None,
    limit: int | None = None,
    dataset: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return filtered public incident records."""
    loaded = dataset or load_incident_dataset()
    incidents = [_public_incident_fields(item) for item in loaded.get("incidents", [])]

    if chain:
        incidents = [item for item in incidents if item["chain"].lower() == chain.lower()]
    if attack_vector:
        incidents = [
            item for item in incidents if item["attack_vector"].lower() == attack_vector.lower()
        ]
    if min_loss_usd is not None:
        incidents = [item for item in incidents if item["loss_usd"] >= min_loss_usd]
    incidents.sort(key=lambda item: item["loss_usd"], reverse=True)
    if limit is not None:
        incidents = incidents[:limit]
    return incidents


def detection_coverage(dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run incident records through the signature engine and report coverage."""
    loaded = dataset or load_incident_dataset()
    incidents = list(loaded.get("incidents") or [])
    rows: list[dict[str, Any]] = []
    covered = 0

    for incident in incidents:
        payload = incident_to_detection_payload(incident)
        result = check_crypto_hack_signatures(payload).to_dict()
        matched = bool(result["blockers"] or result["warnings"] or result["signatures_matched"])
        if matched:
            covered += 1
        rows.append(
            {
                "incident": _public_incident_fields(incident),
                "matched": matched,
                "signaturesMatched": result["signatures_matched"],
                "blockerCount": len(result["blockers"]),
                "warningCount": len(result["warnings"]),
                "iocCount": len(result["iocs_hit"]),
            }
        )

    return {
        "schema": COVERAGE_SCHEMA,
        "datasetFingerprint": dataset_fingerprint(loaded),
        "incidentCount": len(incidents),
        "coveredCount": covered,
        "coverageRatio": round(covered / len(incidents), 4) if incidents else 0,
        "coverage": rows,
    }


def incident_to_detection_payload(incident: dict[str, Any]) -> dict[str, Any]:
    """Convert an incident record into a preview-mode signature-check payload."""
    text = " ".join(
        str(incident.get(key, ""))
        for key in ("protocol", "attack_vector", "description", "lesson", "attribution")
    )
    vector = str(incident.get("attack_vector", "")).lower()
    payload: dict[str, Any] = {
        "action": incident.get("attack_vector", "unknown"),
        "mode": "preview",
        "prompt_text": text,
        "value_eth": 0,
        "requires_signature": False,
    }
    if "bridge" in vector or "state proof" in vector or "message" in vector:
        payload["calldata"] = "0x8c3152e9"
        payload["prompt_text"] += " executePayload processMessage verifyAndProcess"
    if "oracle" in vector or "reserve" in vector:
        payload["calldata"] = "0x41441d3b"
        payload["prompt_text"] += " updatePrice price deviation 50"
    if "flash loan" in vector:
        payload["steps"] = [{"action": "flashLoan"}, {"action": "swap"}, {"action": "withdraw"}]
    if "access control" in vector or "admin key" in vector:
        payload["steps"] = [
            {"action": "grantRole", "calldata": "0x2f2ff15d"},
            {"action": "upgradeTo", "calldata": "0x3659cfe6"},
        ]
    if "eip-7702" in text.lower() or "batchcall" in text.lower():
        payload["prompt_text"] += (
            " EIP-7702 delegated code BatchExecutor BatchCall.batch lacks access control "
            "permissionless authorized caller reserve pool"
        )
    if "signature replay" in vector:
        payload["calldata"] = (
            "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )
    if "hot wallet" in vector or "social engineering" in vector:
        payload["requires_signature"] = True
        payload["mode"] = "live_transaction"
    if "reentrancy" in vector:
        payload["calldata"] = "0x2e1a7d4d"
    return payload


def dataset_fingerprint(dataset: dict[str, Any]) -> str:
    encoded = json.dumps(dataset, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_incident_date(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO date string")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} must be an ISO date string")


def _public_incident_fields(incident: dict[str, Any]) -> dict[str, Any]:
    public = {
        "id": incident.get("id"),
        "date": incident.get("date"),
        "protocol": incident.get("protocol"),
        "loss_usd": incident.get("loss_usd", 0),
        "chain": incident.get("chain"),
        "attack_vector": incident.get("attack_vector"),
        "attribution": incident.get("attribution"),
        "lesson": incident.get("lesson"),
    }
    source_urls = incident.get("source_urls")
    if isinstance(source_urls, list) and source_urls:
        public["source_urls"] = source_urls
    derived_evidence = incident.get("derived_source_evidence")
    if isinstance(derived_evidence, list) and derived_evidence:
        public["derived_source_evidence"] = derived_evidence
    return public


def _sorted_counter(values) -> dict[str, int]:
    counts = Counter(str(value or "Unknown") for value in values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _safe_average(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))
