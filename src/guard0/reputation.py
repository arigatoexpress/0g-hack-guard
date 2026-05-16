"""Rights-aware counterparty and domain reputation probes for 0guard."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from guard0.crypto_hack_guard import KNOWN_MALICIOUS_ADDRESSES
from guard0.policy import evaluate_intent

REPUTATION_PROBE_SCHEMA = "0guard.reputation_probe.v1"

CURATED_DOMAIN_ALLOWLIST = (
    "0g.ai",
    "docs.0g.ai",
    "hackquest.io",
    "github.com",
)

_BAD_LABEL_TERMS = (
    "abuse",
    "attack",
    "compromised",
    "drain",
    "drainer",
    "exploit",
    "hack",
    "malicious",
    "phish",
    "scam",
    "spoof",
)
_GOOD_LABEL_TERMS = (
    "allow",
    "benign",
    "known_good",
    "trusted",
    "verified",
)
_EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def build_reputation_probe(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic reputation verdict without raw-source resale."""
    body = payload or {}
    if not isinstance(body, dict):
        raise ValueError("payload must be an object")

    subject = _subject_from_payload(body)
    signals: list[dict[str, Any]] = []
    signals.extend(_domain_signals(subject["domain"], subject["urlHash"]))
    signals.extend(_address_signals(subject["address"]))
    signals.extend(_label_signals(body.get("labels") or body.get("tags") or []))
    signals.extend(_source_evidence_signals(body.get("sourceEvidence") or body.get("evidence") or []))
    signals.extend(_intent_signals(body.get("intent"), subject))

    decision = _rollup(signals)
    receipt_hash = _hash_json(
        {
            "schema": REPUTATION_PROBE_SCHEMA,
            "subject": subject,
            "decision": decision["decision"],
            "signals": signals,
        }
    )
    return {
        "schema": REPUTATION_PROBE_SCHEMA,
        "generatedAt": _now(),
        "mode": "derived_reputation_no_raw_resale",
        "subject": subject,
        "decision": decision,
        "signalCount": len(signals),
        "signals": signals,
        "receipt": {
            "hash": receipt_hash,
            "algorithm": "sha256_canonical_json",
            "zeroGChainReady": True,
            "zeroGStorageReady": True,
            "liveAnchorPerformed": False,
            "liveUploadPerformed": False,
        },
        "rightsPolicy": {
            "rawPayloadsReturned": False,
            "rawPayloadResaleAllowed": False,
            "sourceLinksOrHashesOnly": True,
            "callerEvidenceTreatedAsUntrusted": True,
        },
        "recommendedNextStep": _next_step(decision["decision"]),
        "safety": _safety(),
    }


def domain_decision(url: str) -> dict[str, Any]:
    """Return the curated-domain allowlist posture used by the legacy domain route."""
    parsed = _parse_url_or_host(url)
    host = parsed.hostname
    for allowed in sorted(CURATED_DOMAIN_ALLOWLIST, key=len, reverse=True):
        allowed_host = allowed.lower()
        if host == allowed_host or host.endswith(f".{allowed_host}"):
            return {"host": host, "allowed": True, "matched": allowed_host}
    return {"host": host, "allowed": False, "matched": None}


def _subject_from_payload(body: dict[str, Any]) -> dict[str, Any]:
    raw_url = str(body.get("url") or body.get("domain") or body.get("website") or "").strip()
    parsed = _parse_url_or_host(raw_url) if raw_url else None
    address = str(
        body.get("address")
        or body.get("target")
        or body.get("to")
        or body.get("counterparty")
        or ""
    ).strip()
    chain = str(body.get("chain") or body.get("caip2") or "").strip()
    return {
        "domain": parsed.hostname if parsed else "",
        "urlHash": _hash_text(raw_url) if raw_url else "",
        "address": address,
        "addressRedacted": _redact_address(address),
        "chain": chain,
        "surface": str(body.get("surface") or body.get("sourceProject") or "").strip(),
    }


def _parse_url_or_host(value: str):
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = (parsed.hostname or "").lower().rstrip(".")
    return parsed._replace(netloc=host)


def _domain_signals(domain: str, url_hash: str) -> list[dict[str, Any]]:
    if not domain:
        return []
    decision = domain_decision(domain)
    if decision["allowed"]:
        return [
            _signal(
                "trusted_domain_allowlist",
                "allow",
                "low",
                f"Domain matches curated allowlist host {decision['matched']}.",
                evidence={"domain": domain, "urlHash": url_hash},
            )
        ]

    for allowed in CURATED_DOMAIN_ALLOWLIST:
        allowed_host = allowed.lower()
        if allowed_host in domain:
            return [
                _signal(
                    "allowlist_suffix_spoof",
                    "deny",
                    "high",
                    f"Untrusted domain embeds curated host {allowed_host}.",
                    evidence={"domain": domain, "matchedAllowlistText": allowed_host},
                )
            ]

    return [
        _signal(
            "domain_not_allowlisted",
            "review",
            "medium",
            "Domain is not in the curated allowlist.",
            evidence={"domain": domain, "urlHash": url_hash},
        )
    ]


def _address_signals(address: str) -> list[dict[str, Any]]:
    if not address:
        return []
    known = {item.lower(): item for item in KNOWN_MALICIOUS_ADDRESSES}
    if address.lower() in known:
        return [
            _signal(
                "known_malicious_counterparty",
                "deny",
                "critical",
                "Counterparty matches a known malicious or compromised address indicator.",
                evidence={"addressRedacted": _redact_address(address), "source": "0guard_ioc_set"},
            )
        ]
    if address.startswith("0x") and not _EVM_ADDRESS_RE.match(address):
        return [
            _signal(
                "malformed_evm_address",
                "review",
                "medium",
                "Counterparty looks like an EVM address but has invalid syntax.",
                evidence={"addressRedacted": _redact_address(address)},
            )
        ]
    if _EVM_ADDRESS_RE.match(address):
        return [
            _signal(
                "evm_address_syntax_valid",
                "allow",
                "low",
                "Counterparty has valid EVM address syntax and no local IOC match.",
                evidence={"addressRedacted": _redact_address(address)},
            )
        ]
    return [
        _signal(
            "non_evm_counterparty_unresolved",
            "review",
            "medium",
            "Counterparty is non-EVM or unresolved by the local reputation probe.",
            evidence={"addressRedacted": _redact_address(address)},
        )
    ]


def _label_signals(labels: Any) -> list[dict[str, Any]]:
    if isinstance(labels, str):
        labels = [labels]
    if not isinstance(labels, list):
        return []
    signals = []
    for label in [str(item).strip() for item in labels if str(item).strip()][:10]:
        norm = label.lower()
        if any(term in norm for term in _BAD_LABEL_TERMS):
            signals.append(
                _signal(
                    "caller_bad_reputation_label",
                    "deny",
                    "high",
                    "Caller-supplied label indicates malicious or spoofed behavior.",
                    evidence={"label": label},
                )
            )
        elif any(term in norm for term in _GOOD_LABEL_TERMS):
            signals.append(
                _signal(
                    "caller_good_reputation_label",
                    "allow",
                    "low",
                    "Caller-supplied label indicates a trusted or verified entity.",
                    evidence={"label": label},
                )
            )
    return signals


def _source_evidence_signals(evidence: Any) -> list[dict[str, Any]]:
    if not isinstance(evidence, list):
        return []
    signals = []
    for row in evidence[:10]:
        if not isinstance(row, dict):
            continue
        verdict = str(row.get("verdict") or row.get("decision") or row.get("label") or "").lower()
        confidence = _confidence(row.get("confidence"))
        source_id = str(row.get("sourceId") or row.get("source_id") or "caller_evidence").strip()
        label = str(row.get("label") or verdict or "unspecified").strip()
        evidence_hash = _hash_json(
            {
                "sourceId": source_id,
                "verdict": verdict,
                "confidence": confidence,
                "label": label,
                "url": row.get("url") or row.get("referenceUrl"),
            }
        )
        if any(term in verdict or term in label.lower() for term in _BAD_LABEL_TERMS):
            signals.append(
                _signal(
                    "source_negative_vote",
                    "deny" if confidence >= 0.8 else "review",
                    "high" if confidence >= 0.8 else "medium",
                    "Caller-provided source evidence reports negative reputation.",
                    evidence={
                        "sourceId": source_id,
                        "confidence": confidence,
                        "label": label,
                        "evidenceHash": evidence_hash,
                    },
                )
            )
        elif any(term in verdict or term in label.lower() for term in _GOOD_LABEL_TERMS):
            signals.append(
                _signal(
                    "source_positive_vote",
                    "allow",
                    "low",
                    "Caller-provided source evidence reports positive reputation.",
                    evidence={
                        "sourceId": source_id,
                        "confidence": confidence,
                        "label": label,
                        "evidenceHash": evidence_hash,
                    },
                )
            )
    return signals


def _intent_signals(intent: Any, subject: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(intent, dict) or not intent:
        return []
    enriched = {
        **intent,
        "target_contract": intent.get("target_contract") or subject.get("address"),
        "app": intent.get("app") or subject.get("domain") or subject.get("surface"),
    }
    decision = evaluate_intent(enriched).to_dict()
    if decision["decision"] == "allow":
        return [
            _signal(
                "intent_policy_allow",
                "allow",
                "low",
                "Intent policy check did not find blockers or warnings.",
                evidence={"receiptHash": decision["receipt_hash"]},
            )
        ]
    return [
        _signal(
            "intent_policy_reputation_context",
            decision["decision"],
            "critical" if decision["decision"] == "deny" else "medium",
            "Intent policy check found signer, calldata, secret, or exploit-pattern risk.",
            evidence={
                "receiptHash": decision["receipt_hash"],
                "blockerCount": len(decision.get("blockers") or []),
                "warningCount": len(decision.get("warnings") or []),
            },
        )
    ]


def _rollup(signals: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [signal for signal in signals if signal["decision"] == "deny"]
    reviews = [signal for signal in signals if signal["decision"] == "review"]
    if blockers:
        return {
            "decision": "deny",
            "severity": "critical" if any(s["severity"] == "critical" for s in blockers) else "high",
            "riskScore": 96 if any(s["severity"] == "critical" for s in blockers) else 88,
            "reasons": [signal["reason"] for signal in blockers[:5]],
        }
    if reviews:
        return {
            "decision": "review",
            "severity": "medium",
            "riskScore": 62,
            "reasons": [signal["reason"] for signal in reviews[:5]],
        }
    return {
        "decision": "allow",
        "severity": "low",
        "riskScore": 8 if signals else 15,
        "reasons": ["No negative local reputation signals matched."],
    }


def _signal(
    signal_id: str,
    decision: str,
    severity: str,
    reason: str,
    *,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": signal_id,
        "decision": decision,
        "severity": severity,
        "reason": reason,
        "evidence": evidence,
    }


def _confidence(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, parsed))


def _next_step(decision: str) -> str:
    if decision == "deny":
        return "Stop before signer access and attach the reputation receipt to the review path."
    if decision == "review":
        return "Show the reputation reasons, request stronger evidence, and keep the flow simulation-only."
    return "Reputation context is acceptable; live actions still need native preflight and operator policy."


def _redact_address(address: str) -> str:
    value = str(address or "").strip()
    if len(value) <= 12:
        return value
    return f"{value[:6]}...{value[-4:]}"


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_json(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "networkCalls": False,
        "rawPayloadsReturned": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "privateKeyImportEnabled": False,
        "walletCreationEnabled": False,
        "telegramSendsEnabled": False,
        "moneyMovementEnabled": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
