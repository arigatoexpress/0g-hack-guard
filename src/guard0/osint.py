"""Rights-aware open-source intelligence streams for 0guard."""

from __future__ import annotations

import hashlib
import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from guard0.incident_data import (
    dataset_fingerprint,
    detection_coverage,
    incident_summary,
    incident_to_detection_payload,
    load_incident_dataset,
)
from guard0.crypto_hack_guard import check_crypto_hack_signatures

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_REGISTRY_PATH = REPO_ROOT / "data" / "osint_sources.json"
DEFAULT_PROVENANCE_CACHE_PATH = REPO_ROOT / "data" / "incident_provenance_cache.json"
OSINT_REGISTRY_SCHEMA = "0guard.osint_source_registry.v1"
OSINT_READINESS_SCHEMA = "0guard.osint_readiness.v1"
OSINT_SIGNALS_SCHEMA = "0guard.osint_signals.v1"
SIGNATURE_MAP_SCHEMA = "0guard.signature_map.v1"
HACKATHON_BRIEF_SCHEMA = "0guard.hackathon_submission_brief.v1"
PROVENANCE_MATRIX_SCHEMA = "0guard.incident_provenance_matrix.v1"
PROVENANCE_CACHE_SCHEMA = "0guard.incident_provenance_cache.v1"
USER_AGENT = "0guard-osint/0.1 (+https://github.com/arigatoexpress/0guard)"
MAX_FETCH_BYTES = 2_000_000
DEFILLAMA_INCIDENT_ALIASES = {
    "driftprotocol": {"drifttrade"},
    "rheafinance": {"rhealend"},
    "voloprotocol": {"volovault"},
    "wasabiprotocol": {"wasabiperps"},
    "silov2": {"silofinance"},
}


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    status_code: int | None
    url: str
    content_type: str
    elapsed_ms: int
    body: bytes
    error: str | None = None


def load_source_registry(path: str | Path | None = None) -> dict[str, Any]:
    """Load the source registry that defines rights and retrieval boundaries."""
    registry_path = Path(path) if path else DEFAULT_SOURCE_REGISTRY_PATH
    with registry_path.open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    if not isinstance(registry, dict):
        raise ValueError("OSINT source registry must be a JSON object")
    if registry.get("schema") != OSINT_REGISTRY_SCHEMA:
        raise ValueError(f"unexpected OSINT source registry schema: {registry.get('schema')}")
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("OSINT source registry must include sources")
    return registry


def source_registry_public() -> dict[str, Any]:
    """Return public source metadata without raw payloads or credentials."""
    registry = load_source_registry()
    return {
        "schema": registry["schema"],
        "generatedAt": registry.get("generated_at"),
        "sourceCount": len(registry["sources"]),
        "enabledByDefaultCount": sum(
            1 for source in registry["sources"] if source.get("enabled_by_default")
        ),
        "sources": [_public_source_fields(source) for source in registry["sources"]],
        "rightsPolicy": {
            "paymentIsNotPermission": True,
            "rawPayloadResaleAllowed": False,
            "outputMode": "derived_metadata_links_hashes_and_defensive_analysis",
        },
    }


def osint_readiness(*, live: bool = False, timeout_seconds: float = 3.0) -> dict[str, Any]:
    """Check source catalog posture, optionally proving live source availability."""
    registry = load_source_registry()
    rows: list[dict[str, Any]] = []
    attempted = 0
    reachable = 0

    for source in registry["sources"]:
        row = _public_source_fields(source)
        row["enabledByDefault"] = bool(source.get("enabled_by_default"))
        row["liveChecked"] = False
        row["status"] = "not_checked"
        row["latencyMs"] = None
        row["httpStatus"] = None
        row["error"] = None

        if live and source.get("enabled_by_default"):
            attempted += 1
            result = _fetch_url(source["url"], timeout_seconds=timeout_seconds, max_bytes=2048)
            row["liveChecked"] = True
            row["status"] = "reachable" if result.ok else "degraded"
            row["latencyMs"] = result.elapsed_ms
            row["httpStatus"] = result.status_code
            row["contentType"] = result.content_type
            row["error"] = result.error
            if result.ok:
                reachable += 1

        rows.append(row)

    return {
        "schema": OSINT_READINESS_SCHEMA,
        "generatedAt": _now(),
        "live": live,
        "sourceCount": len(rows),
        "enabledByDefaultCount": sum(1 for row in rows if row["enabledByDefault"]),
        "attemptedLiveChecks": attempted,
        "reachableLiveChecks": reachable,
        "readinessRatio": round(reachable / attempted, 4) if attempted else None,
        "sources": rows,
        "safety": _osint_safety(),
    }


def osint_signals(
    *,
    live: bool = True,
    limit: int = 20,
    timeout_seconds: float = 6.0,
) -> dict[str, Any]:
    """Fetch normalized OSINT signals from enabled public streams."""
    registry = load_source_registry()
    signals: list[dict[str, Any]] = []
    source_status: list[dict[str, Any]] = []

    for source in registry["sources"]:
        if not source.get("enabled_by_default"):
            continue
        adapter = source.get("adapter")
        if adapter not in ("defillama_hacks", "rss"):
            source_status.append(
                {
                    "sourceId": source["id"],
                    "adapter": adapter,
                    "status": "catalog_only",
                    "reason": "No raw payload fetched; source is used as a provenance lead.",
                }
            )
            continue
        if not live:
            source_status.append(
                {
                    "sourceId": source["id"],
                    "adapter": adapter,
                    "status": "live_fetch_disabled",
                }
            )
            continue

        result = _fetch_url(
            source["url"],
            timeout_seconds=timeout_seconds,
            max_bytes=MAX_FETCH_BYTES,
        )
        source_status.append(
            {
                "sourceId": source["id"],
                "adapter": adapter,
                "status": "ok" if result.ok else "degraded",
                "httpStatus": result.status_code,
                "latencyMs": result.elapsed_ms,
                "error": result.error,
            }
        )
        if not result.ok:
            continue
        if adapter == "defillama_hacks":
            signals.extend(_normalize_defillama_hacks(source, result.body, limit=limit))
        elif adapter == "rss":
            signals.extend(_normalize_rss_items(source, result.body, limit=limit))

    signals.sort(key=lambda item: item.get("observedAt") or "", reverse=True)
    signals = signals[:limit]
    return {
        "schema": OSINT_SIGNALS_SCHEMA,
        "generatedAt": _now(),
        "live": live,
        "signalCount": len(signals),
        "sourceStatus": source_status,
        "signals": signals,
        "safety": _osint_safety(),
    }


def signature_map(dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    """Explain incident-to-signature coverage and concrete detector gaps."""
    loaded = dataset or load_incident_dataset()
    rows: list[dict[str, Any]] = []
    matched = 0
    for incident in loaded.get("incidents", []):
        payload = incident_to_detection_payload(incident)
        result = check_crypto_hack_signatures(payload).to_dict()
        is_matched = bool(result["blockers"] or result["warnings"] or result["signatures_matched"])
        if is_matched:
            matched += 1
        rows.append(
            {
                "incidentId": incident.get("id"),
                "protocol": incident.get("protocol"),
                "attackVector": incident.get("attack_vector"),
                "chain": incident.get("chain"),
                "matched": is_matched,
                "signaturesMatched": result["signatures_matched"],
                "blockers": result["blockers"],
                "warnings": result["warnings"],
                "gap": None if is_matched else _signature_gap_for_incident(incident),
                "recommendedDetector": _recommended_detector_for_incident(incident, is_matched),
                "payloadPreview": {
                    key: payload.get(key)
                    for key in ("action", "mode", "requires_signature", "calldata", "steps")
                    if payload.get(key)
                },
            }
        )

    total = len(rows)
    return {
        "schema": SIGNATURE_MAP_SCHEMA,
        "datasetFingerprint": dataset_fingerprint(loaded),
        "incidentCount": total,
        "matchedCount": matched,
        "gapCount": total - matched,
        "coverageRatio": round(matched / total, 4) if total else 0,
        "topGaps": _top_gap_counts(rows),
        "rows": rows,
    }


def incident_provenance_matrix(
    *,
    live: bool = False,
    dataset: dict[str, Any] | None = None,
    defillama_records: list[dict[str, Any]] | None = None,
    cache_path: str | Path | None = None,
    timeout_seconds: float = 6.0,
) -> dict[str, Any]:
    """Build per-incident source evidence and live-source correlation gaps."""
    loaded = dataset or load_incident_dataset()
    meta = loaded.get("meta") or {}
    aggregate_sources = meta.get("source_urls") if isinstance(meta, dict) else []
    if not isinstance(aggregate_sources, list):
        aggregate_sources = []

    fetched = False
    records = defillama_records if defillama_records is not None else []
    cached_evidence = (
        {}
        if defillama_records is not None
        else _load_provenance_cache(cache_path=cache_path)
    )
    source_status = {
        "sourceId": "defillama_hacks",
        "status": "injected_records"
        if defillama_records is not None
        else "live_fetch_disabled",
        "live": live,
        "error": None,
        "recordsLoaded": len(records),
        "cacheRecordsLoaded": len(cached_evidence),
        "evidenceMode": "injected_records" if defillama_records is not None else "none",
    }

    if live and defillama_records is None:
        fetched = True
        result = _fetch_url(
            "https://api.llama.fi/hacks",
            timeout_seconds=timeout_seconds,
            max_bytes=MAX_FETCH_BYTES,
        )
        source_status.update(
            {
                "status": "ok" if result.ok else "degraded",
                "httpStatus": result.status_code,
                "latencyMs": result.elapsed_ms,
                "error": result.error,
            }
        )
        if result.ok:
            try:
                decoded = json.loads(result.body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                decoded = []
                source_status["status"] = "parse_error"
            if isinstance(decoded, list):
                records = [item for item in decoded if isinstance(item, dict)]
                source_status["recordsLoaded"] = len(records)
        if not records and cached_evidence:
            source_status["status"] = "degraded_cache_fallback"

    if records:
        source_status["evidenceMode"] = "live_source_records" if fetched else "injected_records"
    elif cached_evidence:
        if not live and defillama_records is None:
            source_status["status"] = "reviewed_cache"
        source_status["evidenceMode"] = "reviewed_derived_cache"

    rows = []
    linked_count = 0
    high_confidence_count = 0
    dataset_source_count = 0
    for incident in loaded.get("incidents", []):
        dataset_urls = incident.get("source_urls")
        if isinstance(dataset_urls, list) and dataset_urls:
            dataset_source_count += 1
        else:
            dataset_urls = []

        evidence = _defillama_evidence_for_incident(incident, records) if records else None
        if evidence is None and cached_evidence:
            evidence = cached_evidence.get(int(incident.get("id", -1)))
        if evidence:
            linked_count += 1
            if evidence["confidence"] >= 0.85:
                high_confidence_count += 1
        status = "source_linked" if evidence else "aggregate_only"
        if not evidence and not aggregate_sources:
            status = "missing_sources"

        rows.append(
            {
                "incidentId": incident.get("id"),
                "protocol": incident.get("protocol"),
                "date": incident.get("date"),
                "lossUsd": incident.get("loss_usd"),
                "chain": incident.get("chain"),
                "attackVector": incident.get("attack_vector"),
                "status": status,
                "datasetSourceUrls": dataset_urls,
                "aggregateSourceUrls": aggregate_sources,
                "evidence": [evidence] if evidence else [],
                "recommendedNextStep": _provenance_next_step(incident, evidence),
            }
        )

    incident_count = len(rows)
    return {
        "schema": PROVENANCE_MATRIX_SCHEMA,
        "generatedAt": _now(),
        "live": live,
        "liveFetchAttempted": fetched,
        "datasetFingerprint": dataset_fingerprint(loaded),
        "sourceStatus": source_status,
        "coverage": {
            "incidentCount": incident_count,
            "withDatasetSourceUrls": dataset_source_count,
            "withMatchedEvidence": linked_count,
            "highConfidenceEvidenceCount": high_confidence_count,
            "aggregateOnlyCount": sum(1 for row in rows if row["status"] == "aggregate_only"),
            "evidenceCoverageRatio": round(linked_count / incident_count, 4)
            if incident_count
            else 0,
        },
        "rows": rows,
        "safety": _osint_safety(),
    }


def hackathon_submission_brief() -> dict[str, Any]:
    """Return a compact, current submission checklist and product brief."""
    summary = incident_summary()
    coverage = detection_coverage()
    sig_map = signature_map()
    sources = source_registry_public()
    provenance = incident_provenance_matrix(live=False)
    return {
        "schema": HACKATHON_BRIEF_SCHEMA,
        "generatedAt": _now(),
        "project": {
            "name": "0guard",
            "oneLiner": (
                "0guard is a 0G-native pre-wallet firewall that checks AI-agent "
                "intents against real exploit intelligence before any signer can act."
            ),
            "repo": "https://github.com/arigatoexpress/0guard",
            "publicDemo": "https://arigatoexpress.github.io/0guard/",
        },
        "deadline": {
            "source": "HackQuest 0G APAC Hackathon",
            "submissionDeadline": "2026-05-16T23:59:00+08:00",
            "submissionDeadlineMdt": "2026-05-16T09:59:00-06:00",
            "submissionDeadlineEdt": "2026-05-16T11:59:00-04:00",
            "preliminaryReview": "2026-05-16 to 2026-05-24",
            "rewardAnnouncement": "2026-05-29T15:59:00+08:00",
            "note": "Official HackQuest page says all final materials must be submitted before May 16, 2026 at 23:59 UTC+8.",
        },
        "trackRecommendation": {
            "primary": "Track 5: Privacy & Sovereign Infrastructure",
            "secondary": "Track 1: Agentic Infrastructure & OpenClaw Lab",
            "why": (
                "Lead with verifiable pre-wallet security, provenance, and receipt "
                "infrastructure; mention agent orchestration only as the user context."
            ),
        },
        "submissionRequirements": {
            "repo": {
                "required": True,
                "status": "ready",
                "url": "https://github.com/arigatoexpress/0guard",
            },
            "0gProof": {
                "required": True,
                "status": "operator_required",
                "needs": [
                    "0G contract address",
                    "0G Explorer link",
                    "Clear proof of at least one 0G component",
                ],
            },
            "demoVideo": {
                "required": True,
                "status": "operator_required",
                "maxDurationSeconds": 180,
                "mustShow": [
                    "core product flow",
                    "user flow or use case",
                    "how the 0G component is actually used",
                ],
            },
            "publicXPost": {
                "mandatory": True,
                "status": "operator_required",
                "requiredTags": ["@0G_labs", "@0g_CN", "@0g_Eco", "@HackQuest_"],
                "requiredHashtags": ["#0GHackathon", "#BuildOn0G"],
                "needs": ["project name", "demo screenshot or short demo clip"],
            },
            "documentation": {
                "required": True,
                "status": "ready_with_known_gaps",
                "judgeFastPath": "README plus docs/hackathon-0g/",
            },
        },
        "judgeStory": [
            "AI agents can request wallet actions faster than humans can review them.",
            "0guard intercepts intent before the wallet, signer, bridge, or send path.",
            "The detector is grounded in real incident patterns and OSINT source streams.",
            "The verdict becomes a deterministic receipt ready for 0G Chain and Storage.",
            "Dangerous actions stay blocked from the workbench by design.",
        ],
        "competitivePositioning": [
            "Strong 0G submissions expose proof trails: contract addresses, storage roots, transaction hashes, demo URLs, and judge walkthroughs.",
            "0guard's wedge is not another agent memory app; it is the security/provenance layer agents should consult before signing.",
            "The submission should foreground read-only proof honesty and the receipt-anchor gap instead of pretending mainnet writes are complete.",
        ],
        "proofFirstChecklist": [
            "Show live /api/0g/status readback.",
            "Show /api/evaluate with 0G anchor/storage flags and the preflight receipt payload.",
            "Show /api/data/provenance?live=1 with source match counts and record hashes.",
            "Show the contract address and explorer link after operator deployment.",
            "Show the public X post link and <=3 minute demo video link in the HackQuest form.",
        ],
        "0gIntegration": {
            "chain": "Live read-only Galileo RPC proof plus PolicyReceiptAnchor preflight.",
            "storage": "Deterministic Storage-ready threat-intel receipts and root hashes.",
            "compute": "Planned 0G Compute anomaly scorer; not claimed as live inference today.",
            "agentIdentity": "Receipts can include agent_id for accountable agent sessions.",
        },
        "dataProduct": {
            "incidentCount": summary["stats"]["incidentCount"],
            "totalLossUsd": summary["stats"]["totalLossUsd"],
            "datasetFingerprint": summary["validation"]["fingerprint"],
            "detectionCoverageRatio": coverage["coverageRatio"],
            "signatureGapCount": sig_map["gapCount"],
            "sourceRegistryCount": sources["sourceCount"],
            "provenanceCoverageRatioWithoutLiveFetch": provenance["coverage"][
                "evidenceCoverageRatio"
            ],
        },
        "autonomousWorkCompleted": [
            "Validated incident dataset and read-only coverage APIs.",
            "Rights-aware OSINT source registry and live signal normalization.",
            "Signature coverage map with recommended detector gaps.",
            "Incident provenance matrix with live DeFiLlama correlation support.",
            "Submission brief API for judge/operator readback.",
        ],
        "operatorRequired": [
            "Deploy PolicyReceiptAnchor to 0G and save contract/explorer link.",
            "Record and upload the <=3 minute demo video.",
            "Post public X thread with required HackQuest tags.",
            "Submit HackQuest form with repo, demo video, X URL, and 0G proof.",
        ],
        "claimsToAvoid": [
            "Do not claim live mainnet writes.",
            "Do not claim live 0G Compute inference until a real router call is wired.",
            "Do not imply the browser can sign, trade, send Telegram messages, or move funds.",
        ],
    }


def _fetch_url(url: str, *, timeout_seconds: float, max_bytes: int) -> FetchResult:
    started = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                body = body[:max_bytes]
            return FetchResult(
                ok=200 <= response.status < 400,
                status_code=response.status,
                url=response.geturl(),
                content_type=response.headers.get("content-type", ""),
                elapsed_ms=int((time.perf_counter() - started) * 1000),
                body=body,
            )
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return FetchResult(
            ok=False,
            status_code=getattr(getattr(exc, "code", None), "value", None),
            url=url,
            content_type="",
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            body=b"",
            error=f"{type(exc).__name__}: {exc}",
        )


def _normalize_defillama_hacks(
    source: dict[str, Any],
    body: bytes,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    try:
        records = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(records, list):
        return []
    records = sorted(records, key=lambda item: item.get("date") or 0, reverse=True)[:limit]
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            continue
        observed_at = _unix_to_iso(record.get("date"))
        signal = {
            "schema": "0guard.osint_signal.v1",
            "sourceId": source["id"],
            "sourceOwner": source["owner"],
            "sourceUrl": source["url"],
            "retrievalMode": source["retrieval_mode"],
            "rightsEnvelope": source["license_or_rights"],
            "outputPolicy": source["output_policy"],
            "observedAt": observed_at,
            "signalType": "crypto_incident",
            "title": str(record.get("name") or "Unnamed incident").strip(),
            "amountUsd": record.get("amount"),
            "chains": record.get("chain") or [],
            "classification": record.get("classification"),
            "technique": record.get("technique"),
            "targetType": record.get("targetType"),
            "bridgeHack": bool(record.get("bridgeHack")),
            "sourceLink": record.get("source") or source["homepage"],
        }
        signal["recordHash"] = _record_hash(signal)
        normalized.append(signal)
    return normalized


def _normalize_rss_items(
    source: dict[str, Any],
    body: bytes,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return []
    items = root.findall(".//channel/item")[:limit]
    normalized = []
    for item in items:
        title = _xml_text(item, "title")
        link = _xml_text(item, "link")
        pub_date = _xml_text(item, "pubDate")
        categories = [_clean_text(category.text) for category in item.findall("category")]
        signal = {
            "schema": "0guard.osint_signal.v1",
            "sourceId": source["id"],
            "sourceOwner": source["owner"],
            "sourceUrl": source["url"],
            "retrievalMode": source["retrieval_mode"],
            "rightsEnvelope": source["license_or_rights"],
            "outputPolicy": source["output_policy"],
            "observedAt": _parse_rss_datetime(pub_date),
            "signalType": "research_link",
            "title": title,
            "link": link,
            "categories": [value for value in categories if value],
            "securityRelevant": _security_relevant(title, categories),
        }
        signal["recordHash"] = _record_hash(signal)
        normalized.append(signal)
    return normalized


def _defillama_evidence_for_incident(
    incident: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any] | None:
    best: tuple[float, dict[str, Any]] | None = None
    for record in records:
        score = _defillama_match_score(incident, record)
        if score < 0.62:
            continue
        if best is None or score > best[0]:
            best = (score, record)
    if best is None:
        return None

    score, record = best
    source_url = record.get("source") or "https://defillama.com/hacks"
    evidence = {
        "sourceId": "defillama_hacks",
        "sourceOwner": "DeFiLlama",
        "sourceUrl": source_url,
        "evidenceType": "public_incident_index",
        "matchedName": record.get("name"),
        "observedDate": _unix_to_iso(record.get("date")),
        "amountUsd": record.get("amount"),
        "chains": record.get("chain") or [],
        "classification": record.get("classification"),
        "technique": record.get("technique"),
        "targetType": record.get("targetType"),
        "bridgeHack": bool(record.get("bridgeHack")),
        "confidence": round(min(score, 1.0), 4),
        "rightsEnvelope": (
            "Public API metadata. Use as source-cited defensive evidence; do not mirror raw dumps."
        ),
    }
    evidence["recordHash"] = _record_hash(evidence)
    return evidence


def _load_provenance_cache(
    *,
    cache_path: str | Path | None = None,
) -> dict[int, dict[str, Any]]:
    path = Path(cache_path) if cache_path else DEFAULT_PROVENANCE_CACHE_PATH
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        cache = json.load(handle)
    if cache.get("schema") != PROVENANCE_CACHE_SCHEMA:
        raise ValueError(f"unexpected provenance cache schema: {cache.get('schema')}")
    records = cache.get("records")
    if not isinstance(records, list):
        raise ValueError("provenance cache records must be a list")

    indexed: dict[int, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        incident_id = record.get("incidentId")
        evidence = record.get("evidence")
        if not isinstance(incident_id, int) or not isinstance(evidence, dict):
            continue
        indexed[incident_id] = {
            **evidence,
            "cacheReviewStatus": record.get("reviewStatus", "derived_unreviewed"),
            "cacheGeneratedAt": cache.get("generatedAt"),
        }
    return indexed


def _defillama_match_score(incident: dict[str, Any], record: dict[str, Any]) -> float:
    incident_name = _normalize_name(incident.get("protocol"))
    record_name = _normalize_name(record.get("name"))
    aliases = DEFILLAMA_INCIDENT_ALIASES.get(incident_name, set())
    score = 0.0

    if incident_name and incident_name == record_name:
        score += 0.52
    elif record_name in aliases:
        score += 0.52
    elif incident_name and (incident_name in record_name or record_name in incident_name):
        score += 0.38

    incident_loss = incident.get("loss_usd")
    record_amount = record.get("amount")
    if _numbers_close(incident_loss, record_amount):
        score += 0.24
    elif _numbers_close(incident_loss, record_amount, tolerance=0.12):
        score += 0.16

    if incident.get("date") == _unix_to_iso(record.get("date")):
        score += 0.16

    incident_chain = _normalize_name(incident.get("chain"))
    record_chains = {_normalize_name(chain) for chain in (record.get("chain") or [])}
    if incident_chain and incident_chain in record_chains:
        score += 0.08
    elif incident_chain == "multichain" and len(record_chains) > 1:
        score += 0.06

    return score


def _provenance_next_step(incident: dict[str, Any], evidence: dict[str, Any] | None) -> str:
    if evidence and evidence["confidence"] >= 0.85:
        return "Add incident-specific source URL/evidence_type/confidence to the canonical dataset."
    if evidence:
        return "Review the matched source candidate before promoting it into canonical provenance."
    if str(incident.get("attack_vector", "")).lower() == "undisclosed":
        return "Wait for a postmortem or trusted incident writeup before adding detector-specific claims."
    return "Find a protocol postmortem, security report, transaction, or trusted incident index entry."


def _signature_gap_for_incident(incident: dict[str, Any]) -> str:
    vector = str(incident.get("attack_vector") or "").lower()
    text = f"{vector} {incident.get('description', '')}".lower()
    if "undisclosed" in vector:
        return "insufficient_public_root_cause"
    if "donate" in text or "negative" in text:
        return "signed_amount_or_accounting_invariant"
    if "burn" in text or "accounting" in text:
        return "token_accounting_invariant"
    if "signedness" in text or "math" in text:
        return "numeric_type_or_math_invariant"
    if "gateway" in text or "cross-chain" in text:
        return "cross_chain_gateway_invariant"
    if "otc" in text or "settlement" in text:
        return "settlement_atomicity_invariant"
    return "generic_detector_gap"


def _recommended_detector_for_incident(incident: dict[str, Any], matched: bool) -> str | None:
    if matched:
        return None
    gap = _signature_gap_for_incident(incident)
    recommendations = {
        "insufficient_public_root_cause": (
            "Keep as review-only until a source URL or postmortem identifies calldata or behavior."
        ),
        "signed_amount_or_accounting_invariant": (
            "Add invariant checks for negative amounts, unsigned casts, and impossible balance deltas."
        ),
        "token_accounting_invariant": (
            "Add burn/mint accounting detectors for balance supply drift and repeated refund claims."
        ),
        "numeric_type_or_math_invariant": (
            "Add signed/unsigned and bounded-math detectors for settlement and perp accounting."
        ),
        "cross_chain_gateway_invariant": (
            "Add gateway pause, nonce, and replay-proof checks for cross-chain messages."
        ),
        "settlement_atomicity_invariant": (
            "Add atomic settlement and escrow-mode checks before OTC-style transfers."
        ),
    }
    return recommendations.get(gap, "Add a source-specific detector after provenance enrichment.")


def _top_gap_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        gap = row.get("gap")
        if gap:
            counts[gap] = counts.get(gap, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _public_source_fields(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": source["id"],
        "name": source["name"],
        "owner": source["owner"],
        "url": source["url"],
        "homepage": source.get("homepage"),
        "retrievalMode": source["retrieval_mode"],
        "adapter": source["adapter"],
        "freshnessTtlSeconds": source["freshness_ttl_seconds"],
        "licenseOrRights": source["license_or_rights"],
        "outputPolicy": source["output_policy"],
        "caveats": source.get("caveats", ""),
    }


def _osint_safety() -> dict[str, Any]:
    return {
        "readOnly": True,
        "credentialsRequiredForDefaultSources": False,
        "rawPayloadsReturned": False,
        "privatePersonDossiering": False,
        "exploitPayloadsReturned": False,
        "outputMode": "metadata_links_hashes_and_defensive_analysis",
    }


def _record_hash(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _unix_to_iso(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).date().isoformat()


def _parse_rss_datetime(value: str) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def _xml_text(item: ElementTree.Element, field: str) -> str:
    found = item.find(field)
    return _clean_text(found.text if found is not None else "")


def _clean_text(value: str | None) -> str:
    return " ".join(str(value or "").split())


def _normalize_name(value: Any) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _numbers_close(left: Any, right: Any, *, tolerance: float = 0.015) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    if not isinstance(left, int | float) or not isinstance(right, int | float):
        return False
    if left == right:
        return True
    larger = max(abs(float(left)), abs(float(right)), 1.0)
    return abs(float(left) - float(right)) / larger <= tolerance


def _security_relevant(title: str, categories: list[str]) -> bool:
    haystack = " ".join([title, *categories]).lower()
    terms = (
        "crime",
        "hack",
        "exploit",
        "stolen",
        "scam",
        "sanction",
        "threat",
        "security",
        "fraud",
    )
    return any(term in haystack for term in terms)
