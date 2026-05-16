"""Reviewed live connector workers for reputation feeds.

Workers fetch only explicitly reviewed public sources, then immediately reduce
the payload into derived evidence, hashes, counts, and source metadata. Public
responses never return raw feed rows.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

REPUTATION_CONNECTOR_SNAPSHOT_SCHEMA = "0guard.reputation_connector_snapshot.v1"
PHISHDESTROY_SOURCE_ID = "phishdestroy_destroylist"
PHISHDESTROY_ACTIVE_DOMAINS_URL = (
    "https://raw.githubusercontent.com/phishdestroy/destroylist/main/dns/active_domains.json"
)
PHISHDESTROY_PUBLIC_SOURCE_URL = "https://phishdestroy.io/dataset"
USER_AGENT = "0guard-osint/0.1 (+https://github.com/arigatoexpress/0guard)"
MAX_PHISHDESTROY_BYTES = 5_000_000


def phishdestroy_active_domains_snapshot(
    *,
    live: bool = False,
    limit: int = 5,
    subject_url: str = "",
    timeout_seconds: float = 6.0,
) -> dict[str, Any]:
    """Fetch and reduce the PhishDestroy active-domain feed."""
    from guard0.reputation_adapters import normalize_reputation_adapter_payload

    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    subject_domain = _domain_from_url(subject_url)
    if not live:
        return _not_fetched_snapshot(limit=limit, subject_domain=subject_domain)

    fetched = _fetch_url(
        PHISHDESTROY_ACTIVE_DOMAINS_URL,
        timeout_seconds=timeout_seconds,
        max_bytes=MAX_PHISHDESTROY_BYTES,
    )
    if not fetched["ok"]:
        return _degraded_snapshot(fetched, limit=limit, subject_domain=subject_domain)

    domains = _decode_domain_list(fetched["body"])
    unique_domains = sorted({domain for domain in domains if domain})
    matched = subject_domain in set(unique_domains) if subject_domain else None
    sample_domains = (
        [subject_domain]
        if matched is True
        else unique_domains[:limit]
    )
    adapter_payload = {
        "sourceId": PHISHDESTROY_SOURCE_ID,
        "subject": {"url": subject_url} if subject_url else {},
        "payload": {
            "active_domains": [
                {
                    "domain": domain,
                    "site_status": "active",
                    "source": PHISHDESTROY_PUBLIC_SOURCE_URL,
                }
                for domain in sample_domains
            ]
        },
    }
    normalized = normalize_reputation_adapter_payload(adapter_payload)
    body_hash = _hash_bytes(fetched["body"])
    snapshot_hash = _hash_json(
        {
            "sourceId": PHISHDESTROY_SOURCE_ID,
            "bodyHash": body_hash,
            "domainCount": len(unique_domains),
            "sampleHashes": [item["evidenceHash"] for item in normalized["derivedEvidence"]],
            "subjectDomainHash": _hash_text(subject_domain) if subject_domain else "",
            "subjectMatched": matched,
        }
    )

    return {
        "schema": REPUTATION_CONNECTOR_SNAPSHOT_SCHEMA,
        "generatedAt": _now(),
        "mode": "live_fetch_derived_only",
        "sourceId": PHISHDESTROY_SOURCE_ID,
        "sourceName": "PhishDestroy active-domain feed",
        "sourceLink": PHISHDESTROY_PUBLIC_SOURCE_URL,
        "feedLink": PHISHDESTROY_ACTIVE_DOMAINS_URL,
        "live": True,
        "fetch": {
            "status": "ok",
            "httpStatus": fetched["statusCode"],
            "latencyMs": fetched["elapsedMs"],
            "contentType": fetched["contentType"],
            "contentLength": fetched["contentLength"],
            "etag": fetched["etag"],
            "lastModified": fetched["lastModified"],
            "feedHash": body_hash,
            "parsedDomainCount": len(unique_domains),
            "sampledEvidenceCount": len(normalized["derivedEvidence"]),
            "ttlSeconds": 21600,
        },
        "subject": _public_subject(subject_domain, matched),
        "derivedEvidence": normalized["derivedEvidence"],
        "reputationPreview": normalized["reputationPreview"],
        "snapshotReceipt": {
            "hash": snapshot_hash,
            "algorithm": "sha256_canonical_json",
            "zeroGChainReady": True,
            "zeroGStorageReady": True,
            "liveAnchorPerformed": False,
            "liveUploadPerformed": False,
        },
        "promotionUse": [
            "Use this as a live phishing-domain freshness proof.",
            "Use subjectMatched=true evidence in wallet/domain preflight before any signer prompt.",
            "Do not promote sampled feed rows into user alerts unless the user's target matches.",
        ],
        "rightsPolicy": _rights_policy(),
        "safety": _safety(live_connector_fetch=True),
    }


def reputation_connector_snapshot(
    *,
    source_id: str = PHISHDESTROY_SOURCE_ID,
    live: bool = False,
    limit: int = 5,
    subject_url: str = "",
    timeout_seconds: float = 6.0,
) -> dict[str, Any]:
    """Dispatch a reviewed connector worker by source id."""
    if source_id != PHISHDESTROY_SOURCE_ID:
        raise ValueError(f"unsupported live connector sourceId: {source_id}")
    return phishdestroy_active_domains_snapshot(
        live=live,
        limit=limit,
        subject_url=subject_url,
        timeout_seconds=timeout_seconds,
    )


def phishdestroy_digest_signal(snapshot: dict[str, Any], source: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a connector snapshot into an OSINT signal row."""
    fetch = snapshot.get("fetch") if isinstance(snapshot.get("fetch"), dict) else {}
    if fetch.get("status") != "ok":
        return None
    signal = {
        "schema": "0guard.osint_signal.v1",
        "sourceId": source["id"],
        "sourceOwner": source["owner"],
        "sourceUrl": source["url"],
        "retrievalMode": source["retrieval_mode"],
        "rightsEnvelope": source["license_or_rights"],
        "outputPolicy": source["output_policy"],
        "observedAt": snapshot.get("generatedAt"),
        "signalType": "reputation_feed_digest",
        "title": "PhishDestroy active-domain digest",
        "activeDomainCount": fetch.get("parsedDomainCount", 0),
        "sampledEvidenceCount": fetch.get("sampledEvidenceCount", 0),
        "ttlSeconds": fetch.get("ttlSeconds", 21600),
        "sourceLink": snapshot.get("sourceLink"),
        "feedHash": fetch.get("feedHash"),
        "snapshotHash": (snapshot.get("snapshotReceipt") or {}).get("hash"),
        "rawPayloadReturned": False,
    }
    signal["recordHash"] = _hash_json(signal)
    return signal


def _not_fetched_snapshot(*, limit: int, subject_domain: str) -> dict[str, Any]:
    return {
        "schema": REPUTATION_CONNECTOR_SNAPSHOT_SCHEMA,
        "generatedAt": _now(),
        "mode": "live_fetch_disabled",
        "sourceId": PHISHDESTROY_SOURCE_ID,
        "sourceName": "PhishDestroy active-domain feed",
        "sourceLink": PHISHDESTROY_PUBLIC_SOURCE_URL,
        "feedLink": PHISHDESTROY_ACTIVE_DOMAINS_URL,
        "live": False,
        "fetch": {
            "status": "live_fetch_disabled",
            "sampleLimit": limit,
        },
        "subject": _public_subject(subject_domain, None),
        "derivedEvidence": [],
        "snapshotReceipt": {
            "hash": "",
            "algorithm": "sha256_canonical_json",
            "zeroGChainReady": False,
            "zeroGStorageReady": False,
            "liveAnchorPerformed": False,
            "liveUploadPerformed": False,
        },
        "rightsPolicy": _rights_policy(),
        "safety": _safety(live_connector_fetch=False),
    }


def _degraded_snapshot(
    fetched: dict[str, Any],
    *,
    limit: int,
    subject_domain: str,
) -> dict[str, Any]:
    snapshot = _not_fetched_snapshot(limit=limit, subject_domain=subject_domain)
    snapshot["live"] = True
    snapshot["mode"] = "live_fetch_degraded"
    snapshot["fetch"] = {
        "status": "degraded",
        "httpStatus": fetched["statusCode"],
        "latencyMs": fetched["elapsedMs"],
        "contentType": fetched["contentType"],
        "contentLength": fetched["contentLength"],
        "etag": fetched["etag"],
        "lastModified": fetched["lastModified"],
        "error": fetched["error"],
        "sampleLimit": limit,
    }
    snapshot["safety"] = _safety(live_connector_fetch=True)
    return snapshot


def _fetch_url(url: str, *, timeout_seconds: float, max_bytes: int) -> dict[str, Any]:
    started = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(max_bytes + 1)
            too_large = len(body) > max_bytes
            if too_large:
                body = body[:max_bytes]
            return {
                "ok": not too_large,
                "statusCode": getattr(response, "status", None),
                "contentType": response.headers.get("content-type", ""),
                "contentLength": _int(response.headers.get("content-length")),
                "etag": response.headers.get("etag"),
                "lastModified": response.headers.get("last-modified"),
                "elapsedMs": int((time.perf_counter() - started) * 1000),
                "body": body,
                "error": "response exceeded max bytes" if too_large else None,
            }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "statusCode": None,
            "contentType": "",
            "contentLength": 0,
            "etag": None,
            "lastModified": None,
            "elapsedMs": int((time.perf_counter() - started) * 1000),
            "body": b"",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _decode_domain_list(body: bytes) -> list[str]:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    if not isinstance(decoded, list):
        return []
    return [_normalize_domain(item) for item in decoded if isinstance(item, str)]


def _domain_from_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urllib.parse.urlparse(raw)
    return _normalize_domain(parsed.hostname or parsed.path.split("/", 1)[0])


def _normalize_domain(value: str) -> str:
    return str(value or "").strip().lower().rstrip(".")


def _public_subject(subject_domain: str, matched: bool | None) -> dict[str, Any]:
    return {
        "domainHash": _hash_text(subject_domain) if subject_domain else "",
        "matchedInFeed": matched,
        "rawDomainReturned": False,
    }


def _rights_policy() -> dict[str, bool]:
    return {
        "rawPayloadsReturned": False,
        "rawPayloadResaleAllowed": False,
        "rawDomainsReturned": False,
        "sourceLinksOrHashesOnly": True,
        "derivedEvidenceOnly": True,
    }


def _safety(*, live_connector_fetch: bool) -> dict[str, bool]:
    return {
        "readOnly": True,
        "networkCalls": live_connector_fetch,
        "liveConnectorFetch": live_connector_fetch,
        "rawPayloadsReturned": False,
        "rawDomainsReturned": False,
        "privateKeyRequired": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "paymentSettlementEnabled": False,
        "bridgingEnabled": False,
        "swappingEnabled": False,
    }


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
