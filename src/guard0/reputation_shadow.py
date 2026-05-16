"""Derived reputation shadow-cache previews.

This module deliberately does not fetch upstream feeds. It turns reviewed,
caller-supplied adapter payloads into a compact derived snapshot that can be
used by wallet alerts, Telegram previews, and 0G-ready receipts without
reselling raw source records.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from guard0.reputation import build_reputation_probe
from guard0.reputation_adapters import (
    normalize_reputation_adapter_payload,
    reputation_adapter_catalog,
)

REPUTATION_SHADOW_CACHE_SCHEMA = "0guard.reputation_shadow_cache.v1"


def demo_reputation_shadow_payload() -> dict[str, Any]:
    """Return a sanitized multi-source payload for GET previews and docs."""
    return {
        "subject": {
            "url": "https://docs.0g.ai.evil.example/claim",
            "address": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
            "chain": "eip155:16661",
        },
        "adapterPayloads": [
            {
                "sourceId": "phishdestroy_destroylist",
                "payload": {
                    "active_domains": [
                        {
                            "domain": "docs.0g.ai.evil.example",
                            "site_status": "alive",
                            "target_brand": "0G",
                            "drainer_type": "approval_drainer",
                        }
                    ]
                },
            },
            {
                "sourceId": "cryptoscamdb",
                "payload": {
                    "urls": [
                        {
                            "url": "https://docs.0g.ai.evil.example/claim",
                            "category": "phishing",
                            "updated": "2026-05-15T00:00:00Z",
                        }
                    ]
                },
            },
            {
                "sourceId": "forta_labelled_datasets",
                "payload": {
                    "labels": [
                        {
                            "label": "attacker",
                            "confidence": 0.83,
                            "sourceUrl": "https://github.com/forta-network/labelled-datasets",
                        }
                    ]
                },
            },
        ],
    }


def build_reputation_shadow_cache(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a rights-safe derived signal snapshot from reviewed adapter payloads."""
    body = payload or demo_reputation_shadow_payload()
    if not isinstance(body, dict):
        raise ValueError("payload must be an object")

    adapter_rows = _adapter_payloads_from_body(body)
    if not adapter_rows:
        adapter_rows = demo_reputation_shadow_payload()["adapterPayloads"]

    catalog = reputation_adapter_catalog()
    catalog_by_id = {adapter["id"]: adapter for adapter in catalog["adapters"]}
    subject = _subject_from_body(body)

    previews: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in adapter_rows[:12]:
        candidate = _merge_subject(row, subject)
        try:
            previews.append(normalize_reputation_adapter_payload(candidate))
        except (TypeError, ValueError) as exc:
            rejected.append(
                {
                    "sourceId": _candidate_source_id(candidate),
                    "accepted": False,
                    "error": _public_error(exc),
                }
            )

    derived = _derived_evidence(previews)
    source_rows = _source_rows(previews, catalog_by_id)
    activation_queue = _activation_queue(source_rows)
    probe = build_reputation_probe(
        {
            "url": subject["url"],
            "address": subject["address"],
            "chain": subject["chain"],
            "surface": "reputation_shadow_cache",
            "sourceEvidence": derived,
        }
    )
    preview = {
        "schema": probe["schema"],
        "decision": probe["decision"],
        "signalCount": probe["signalCount"],
        "receipt": probe["receipt"],
        "rawPayloadsReturned": probe["rawPayloadsReturned"],
    }
    body_hash = _hash_json(
        {
            "schema": REPUTATION_SHADOW_CACHE_SCHEMA,
            "subject": _public_subject(subject),
            "sources": source_rows,
            "derived": derived,
            "decision": preview["decision"],
        }
    )
    return {
        "schema": REPUTATION_SHADOW_CACHE_SCHEMA,
        "generatedAt": _now(),
        "mode": "derived_shadow_cache_no_fetch_no_raw_resale",
        "subject": _public_subject(subject),
        "sourceCount": len(source_rows),
        "acceptedPayloadCount": len(previews),
        "rejectedPayloadCount": len(rejected),
        "derivedSignalCount": len(derived),
        "sources": source_rows,
        "activationQueue": activation_queue,
        "recommendedPromotions": _recommended_promotions(source_rows),
        "rejectedPayloads": rejected,
        "probePreview": preview,
        "cacheReceipt": {
            "hash": body_hash,
            "algorithm": "sha256_canonical_json",
            "zeroGChainReady": True,
            "zeroGStorageReady": True,
            "liveAnchorPerformed": False,
            "liveUploadPerformed": False,
        },
        "operatorUse": [
            "use this snapshot as a local derived cache between connector worker runs",
            "feed only derived sourceEvidence into /api/reputation/probe or /api/threat-case-file",
            "refresh from operator-reviewed workers after source terms, TTLs, and retention are approved",
            "promote Telegram or wallet alerts only when the combined probe decision is deny or review",
        ],
        "sourceRights": _source_rights(),
        "safety": _safety(),
    }


def _adapter_payloads_from_body(body: dict[str, Any]) -> list[dict[str, Any]]:
    if _candidate_source_id(body):
        return [body]
    for key in ("adapterPayloads", "adapter_payloads", "reputationAdapters", "reputation_adapters"):
        value = body.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _merge_subject(row: dict[str, Any], subject: dict[str, str]) -> dict[str, Any]:
    if isinstance(row.get("subject"), dict):
        return dict(row)
    return {**row, "subject": subject}


def _candidate_source_id(row: dict[str, Any]) -> str:
    return str(row.get("sourceId") or row.get("source_id") or "").strip()


def _subject_from_body(body: dict[str, Any]) -> dict[str, str]:
    subject = body.get("subject") if isinstance(body.get("subject"), dict) else {}
    return {
        "url": str(subject.get("url") or body.get("url") or body.get("domain") or ""),
        "address": str(subject.get("address") or body.get("address") or body.get("target") or ""),
        "chain": str(subject.get("chain") or body.get("chain") or ""),
    }


def _public_subject(subject: dict[str, str]) -> dict[str, str]:
    return {
        "urlHash": _hash_text(subject["url"]) if subject["url"] else "",
        "addressRedacted": _redact(subject["address"]),
        "chain": subject["chain"],
    }


def _derived_evidence(previews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for preview in previews:
        for item in preview.get("derivedEvidence") or []:
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "sourceId": str(item.get("sourceId") or ""),
                    "verdict": str(item.get("verdict") or "unknown"),
                    "confidence": _confidence(item.get("confidence")),
                    "label": str(item.get("label") or "")[:180],
                    "categories": _safe_categories(item.get("categories") or []),
                    "referenceUrlHash": str(item.get("referenceUrlHash") or ""),
                    "evidenceHash": str(item.get("evidenceHash") or ""),
                }
            )
    return rows[:24]


def _source_rows(
    previews: list[dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    for item in _derived_evidence(previews):
        by_source.setdefault(item["sourceId"], []).append(item)

    rows = []
    for source_id, evidence in by_source.items():
        catalog = catalog_by_id.get(source_id, {})
        counts = _verdict_counts(evidence)
        max_confidence = max((_confidence(item.get("confidence")) for item in evidence), default=0.0)
        rows.append(
            {
                "sourceId": source_id,
                "stage": catalog.get("stage") or "caller_supplied",
                "credentialRequiredForLiveFetch": bool(catalog.get("credentialRequiredForLiveFetch")),
                "derivedEvidenceCount": len(evidence),
                "verdictCounts": counts,
                "maxConfidence": round(max_confidence, 4),
                "decision": _source_decision(counts, max_confidence),
                "topCategories": _top_categories(evidence),
                "evidenceHashes": [item["evidenceHash"] for item in evidence if item.get("evidenceHash")][:5],
                "referenceUrlHashes": [
                    item["referenceUrlHash"] for item in evidence if item.get("referenceUrlHash")
                ][:5],
                "rawPayloadReturned": False,
            }
        )
    return sorted(rows, key=lambda item: (item["decision"] != "deny", item["sourceId"]))


def _verdict_counts(evidence: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"malicious": 0, "suspicious": 0, "unknown": 0}
    for item in evidence:
        verdict = str(item.get("verdict") or "unknown")
        counts[verdict if verdict in counts else "unknown"] += 1
    return counts


def _source_decision(counts: dict[str, int], confidence: float) -> str:
    if counts.get("malicious", 0) and confidence >= 0.8:
        return "deny"
    if counts.get("malicious", 0) or counts.get("suspicious", 0):
        return "review"
    return "observe"


def _activation_queue(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rank = {"deny": 0, "review": 1, "observe": 2}
    rows = sorted(
        source_rows,
        key=lambda item: (
            rank.get(item["decision"], 9),
            item["credentialRequiredForLiveFetch"],
            -float(item["maxConfidence"]),
            item["sourceId"],
        ),
    )
    return [
        {
            "rank": index + 1,
            "sourceId": row["sourceId"],
            "decision": row["decision"],
            "why": _activation_reason(row),
            "credentialRequiredForLiveFetch": row["credentialRequiredForLiveFetch"],
        }
        for index, row in enumerate(rows)
    ]


def _activation_reason(row: dict[str, Any]) -> str:
    if row["decision"] == "deny":
        return "high-confidence derived malicious evidence is already useful before signer prompts"
    if row["decision"] == "review":
        return "derived evidence should enrich review alerts before being promoted to hard deny"
    return "keep in shadow mode until it produces material wallet-specific lift"


def _recommended_promotions(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    promotions = []
    deny_sources = [row for row in source_rows if row["decision"] == "deny"]
    for row in deny_sources:
        promotions.append(
            {
                "sourceId": row["sourceId"],
                "action": "promote_to_pre_signer_deny_evidence",
                "reason": "derived high-confidence malicious signal",
                "rawPayloadReturned": False,
            }
        )
    review_sources = [row for row in source_rows if row["decision"] == "review"]
    if len(review_sources) >= 2:
        promotions.append(
            {
                "sourceId": "corroborated_review_cluster",
                "action": "promote_to_wallet_review_alert",
                "reason": "multiple independent sources returned review-grade evidence",
                "rawPayloadReturned": False,
            }
        )
    return promotions[:5]


def _top_categories(evidence: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for item in evidence:
        for category in item.get("categories") or []:
            counts[category] = counts.get(category, 0) + 1
    return [item for item, _count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:6]]


def _safe_categories(categories: Any) -> list[str]:
    if not isinstance(categories, list):
        return []
    return [_safe_category(item) for item in categories if str(item).strip()][:8]


def _safe_category(value: Any) -> str:
    text = str(value).strip()[:80]
    if "://" in text or "/" in text or "." in text:
        return f"categoryHash:{_hash_text(text)[:16]}"
    return text


def _public_error(exc: Exception) -> str:
    text = str(exc)
    if len(text) > 120:
        text = text[:117] + "..."
    return text


def _confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number > 1:
        number = number / 100
    return max(0.0, min(1.0, number))


def _source_rights() -> dict[str, bool]:
    return {
        "rawPayloadsReturned": False,
        "rawPayloadResaleAllowed": False,
        "persistDerivedEvidenceOnly": True,
        "sourceLinksOrHashesOnly": True,
        "paymentIsNotPermission": True,
        "callerPayloadTreatedAsUntrusted": True,
    }


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "networkCalls": False,
        "liveConnectorFetch": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "paymentSettlementEnabled": False,
        "exchangeOrdersEnabled": False,
        "bridgingEnabled": False,
        "moneyMovementEnabled": False,
        "rawPayloadsReturned": False,
    }


def _redact(value: str) -> str:
    value = str(value or "")
    if len(value) <= 16:
        return "***" if value else ""
    return f"{value[:6]}...{value[-6:]}"


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
