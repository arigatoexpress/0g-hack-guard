"""Composed threat case files for judge and operator review."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Any

from guard0.crypto_hack_guard import check_crypto_hack_signatures
from guard0.osint import incident_provenance_matrix, signature_map, threat_receipt_passport
from guard0.policy import evaluate_intent, normalize_intent
from guard0.reputation import build_reputation_probe
from guard0.reputation_adapters import normalize_reputation_adapters_from_payload
from guard0.wallet_alerts import build_wallet_alert_preview

THREAT_CASE_FILE_SCHEMA = "0guard.threat_case_file.v1"
DEFAULT_WALLET = "0x885b0892D241Cb5033C9995e09cA521d54f936b5"
DEFAULT_COUNTERPARTY = "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab"

_SECRET_PATTERNS = (
    re.compile(r"0x[a-fA-F0-9]{64}"),
    re.compile(r"\b(seed phrase|private key|mnemonic|api key|password)\b", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}"),
)


def build_threat_case_file(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build one human-readable no-side-effect dossier for a wallet-adjacent intent."""
    body = payload or {}
    if not isinstance(body, dict):
        raise ValueError("payload must be an object")

    intent = _coerce_intent(body)
    subject = _subject(body, intent)
    normalized_intent = normalize_intent(intent)

    policy = evaluate_intent(
        intent,
        agent_id="threat-case-file",
        enable_0g_anchor=True,
        enable_0g_storage=True,
    ).to_dict()
    hack = check_crypto_hack_signatures(normalized_intent).to_dict()
    adapter_previews = normalize_reputation_adapters_from_payload(body)
    source_evidence = _combined_source_evidence(body, adapter_previews)
    reputation = build_reputation_probe(
        {
            "url": subject["url"],
            "address": subject["counterparty"],
            "chain": subject["chain"],
            "surface": "threat_case_file",
            "labels": body.get("labels") or ["agent preflight case file"],
            "sourceEvidence": source_evidence,
            "intent": intent,
        }
    )
    wallet_alert = build_wallet_alert_preview(
        subject["wallet"],
        intent=intent,
        reputation_context={
            "url": subject["url"],
            "address": subject["counterparty"],
            "chain": subject["chain"],
            "sourceEvidence": source_evidence,
        },
        live=False,
        max_alerts=3,
    )
    sig_map = signature_map()
    provenance = incident_provenance_matrix(live=False)
    passport = threat_receipt_passport()

    decision = _rollup(
        [
            policy.get("decision"),
            reputation.get("decision", {}).get("decision"),
            wallet_alert.get("decision", {}).get("decision"),
            "deny" if hack.get("blockers") else "review" if hack.get("warnings") else "allow",
        ]
    )
    reasons = _reasons(policy, reputation, wallet_alert, hack)
    evidence = _evidence(policy, reputation, wallet_alert, hack, sig_map, provenance, passport)
    receipt_payload = {
        "schema": THREAT_CASE_FILE_SCHEMA,
        "decision": decision,
        "subject": _public_subject(subject, normalized_intent),
        "evidenceHashes": [item["hash"] for item in evidence],
    }

    return {
        "schema": THREAT_CASE_FILE_SCHEMA,
        "generatedAt": _now(),
        "mode": "case_file_preview_no_live_actions",
        "decision": decision,
        "plainEnglish": _plain_english(decision, reasons),
        "technicalSummary": {
            "policyDecision": policy["decision"],
            "policySeverity": policy["severity"],
            "hackSignatureCount": len(hack.get("signatures_matched") or []),
            "iocHitCount": len(hack.get("iocs_hit") or []),
            "reputationDecision": reputation["decision"]["decision"],
            "adapterEvidenceCount": sum(
                preview["derivedEvidenceCount"] for preview in adapter_previews
            ),
            "adapterSourceIds": [preview["sourceId"] for preview in adapter_previews],
            "walletAlertCount": wallet_alert["alertCount"],
            "datasetCoverage": {
                "incidentCount": sig_map.get("incidentCount"),
                "matchedCount": sig_map.get("matchedCount"),
                "gapCount": sig_map.get("gapCount"),
                "withMatchedEvidence": provenance.get("coverage", {}).get("withMatchedEvidence"),
            },
        },
        "subject": _public_subject(subject, normalized_intent),
        "adapterEvidence": _public_adapter_evidence(adapter_previews),
        "evidence": evidence,
        "operatorNextSteps": _operator_next_steps(decision),
        "receipt": {
            "hash": _hash_json(receipt_payload),
            "algorithm": "sha256_canonical_json",
            "policyReceiptHash": policy["receipt_hash"],
            "zeroGStorageReady": True,
            "liveAnchorPerformed": False,
            "liveUploadPerformed": False,
        },
        "sourceRights": {
            "rawPayloadsReturned": False,
            "rawPayloadResaleAllowed": False,
            "sourceLinksOrHashesOnly": True,
            "paymentIsNotPermission": True,
        },
        "safety": _safety(),
    }


def _coerce_intent(body: dict[str, Any]) -> dict[str, Any]:
    raw = body.get("intent") if isinstance(body.get("intent"), dict) else body
    if not isinstance(raw, dict) or not raw:
        return _default_intent()
    intent = dict(raw)
    if not any(intent.get(key) for key in ("action", "method", "prompt_text", "calldata")):
        return _default_intent()
    intent.setdefault("mode", "preview")
    intent.setdefault("requires_signature", False)
    return intent


def _default_intent() -> dict[str, Any]:
    return {
        "action": "approve",
        "mode": "live_transaction",
        "requires_signature": True,
        "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "target_contract": DEFAULT_COUNTERPARTY,
        "prompt_text": "Urgent wallet verification asks the agent to approve a maximum allowance.",
    }


def _subject(body: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    return {
        "wallet": str(body.get("wallet") or body.get("walletAddress") or DEFAULT_WALLET),
        "counterparty": str(
            body.get("counterparty")
            or body.get("address")
            or body.get("target")
            or intent.get("target_contract")
            or intent.get("to")
            or DEFAULT_COUNTERPARTY
        ),
        "url": str(body.get("url") or body.get("domain") or "https://docs.0g.ai.evil.example/claim"),
        "chain": str(body.get("chain") or intent.get("chain") or "eip155:1"),
    }


def _combined_source_evidence(
    body: dict[str, Any],
    adapter_previews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence = body.get("sourceEvidence") or body.get("source_evidence") or body.get("evidence") or []
    if isinstance(evidence, dict):
        evidence = [evidence]
    if not isinstance(evidence, list):
        evidence = []
    combined = [item for item in evidence if isinstance(item, dict)]
    for preview in adapter_previews:
        combined.extend(preview.get("derivedEvidence") or [])
    return combined


def _public_adapter_evidence(adapter_previews: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "enabled": bool(adapter_previews),
        "sourceIds": [preview["sourceId"] for preview in adapter_previews],
        "derivedEvidenceCount": sum(preview["derivedEvidenceCount"] for preview in adapter_previews),
        "rawPayloadsReturned": False,
        "previews": [
            {
                "schema": preview["schema"],
                "sourceId": preview["sourceId"],
                "rawPayloadReturned": preview["rawPayloadReturned"],
                "rawPayloadHash": preview["rawPayloadHash"],
                "derivedEvidenceCount": preview["derivedEvidenceCount"],
                "reputationDecision": preview["reputationPreview"]["decision"]["decision"],
                "nextStep": preview["nextStep"],
            }
            for preview in adapter_previews
        ],
    }


def _rollup(decisions: list[Any]) -> dict[str, str]:
    normalized = [str(item or "").lower() for item in decisions]
    if "deny" in normalized:
        return {"decision": "deny", "severity": "critical"}
    if "review" in normalized:
        return {"decision": "review", "severity": "medium"}
    return {"decision": "allow", "severity": "low"}


def _reasons(
    policy: dict[str, Any],
    reputation: dict[str, Any],
    wallet_alert: dict[str, Any],
    hack: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    reasons.extend(policy.get("blockers") or [])
    reasons.extend(reputation.get("decision", {}).get("reasons") or [])
    reasons.extend(hack.get("blockers") or [])
    reasons.extend(policy.get("warnings") or [])
    reasons.extend(hack.get("warnings") or [])
    if wallet_alert.get("alerts"):
        reasons.extend(alert.get("title", "") for alert in wallet_alert["alerts"][:2])
    return [_redact_text(reason) for reason in reasons if str(reason).strip()][:8]


def _plain_english(decision: dict[str, str], reasons: list[str]) -> list[str]:
    if decision["decision"] == "deny":
        opening = "0guard would stop this request before the wallet is asked to sign."
    elif decision["decision"] == "review":
        opening = "0guard would require human review before a wallet prompt appears."
    else:
        opening = "0guard found no blocker in this read-only preview."
    top_reason = reasons[0] if reasons else "No high-risk source-backed signal matched."
    return [
        opening,
        f"Top reason: {top_reason}",
        "The case file combines policy, exploit signatures, reputation, wallet-alert quality gates, provenance, and 0G-ready receipts.",
        "This public workbench did not send a Telegram alert, call a signer, broadcast a transaction, upload to 0G Storage, bridge, swap, settle a payment, or post socially.",
    ]


def _evidence(
    policy: dict[str, Any],
    reputation: dict[str, Any],
    wallet_alert: dict[str, Any],
    hack: dict[str, Any],
    sig_map: dict[str, Any],
    provenance: dict[str, Any],
    passport: dict[str, Any],
) -> list[dict[str, Any]]:
    adapter_evidence = [
        signal.get("evidence", {}).get("sourceId")
        for signal in reputation.get("signals", [])
        if signal.get("id") == "source_negative_vote" and signal.get("evidence", {}).get("sourceId")
    ]
    rows = [
        {
            "id": "policy_engine",
            "kind": "local_policy_verdict",
            "summary": f"{policy['decision']} / {policy['severity']}",
            "sourceIds": ["0guard_policy_engine"],
            "hash": policy["receipt_hash"],
        },
        {
            "id": "hack_signatures",
            "kind": "detector_match",
            "summary": (
                f"{len(hack.get('signatures_matched') or [])} signature matches, "
                f"{len(hack.get('iocs_hit') or [])} IOC hits"
            ),
            "sourceIds": ["0guard_signature_engine", "april_2026_incident_dataset"],
            "hash": _hash_json(
                {
                    "signatures": hack.get("signatures_matched") or [],
                    "iocs": [_redact_text(item) for item in hack.get("iocs_hit") or []],
                }
            ),
        },
        {
            "id": "reputation_probe",
            "kind": "derived_reputation",
            "summary": reputation["decision"]["decision"],
            "sourceIds": [
                signal.get("evidence", {}).get("sourceId") or signal.get("id")
                for signal in reputation.get("signals", [])[:5]
            ],
            "hash": reputation["receipt"]["hash"],
        },
        {
            "id": "reputation_adapter_evidence",
            "kind": "normalized_external_adapter",
            "summary": (
                f"{len(adapter_evidence)} normalized external source signals"
                if adapter_evidence
                else "no external adapter payload supplied"
            ),
            "sourceIds": sorted(set(adapter_evidence)) or ["none_supplied"],
            "hash": _hash_json(sorted(set(adapter_evidence))),
        },
        {
            "id": "wallet_alert_quality",
            "kind": "telegram_quality_gate",
            "summary": f"{wallet_alert['alertCount']} direct alerts, no Telegram send",
            "sourceIds": ["0guard_wallet_alerts"],
            "hash": _hash_json(wallet_alert.get("alerts") or []),
        },
        {
            "id": "incident_provenance",
            "kind": "source_rights_coverage",
            "summary": (
                f"{provenance.get('coverage', {}).get('withMatchedEvidence')}/"
                f"{provenance.get('coverage', {}).get('incidentCount')} incidents have matched evidence"
            ),
            "sourceIds": ["0guard_provenance_matrix"],
            "hash": _hash_json(provenance.get("coverage") or {}),
        },
        {
            "id": "signature_coverage",
            "kind": "detector_coverage",
            "summary": (
                f"{sig_map.get('matchedCount')}/{sig_map.get('incidentCount')} incident seeds covered"
            ),
            "sourceIds": ["0guard_signature_map"],
            "hash": _hash_json(
                {
                    "incidentCount": sig_map.get("incidentCount"),
                    "matchedCount": sig_map.get("matchedCount"),
                    "gapCount": sig_map.get("gapCount"),
                }
            ),
        },
        {
            "id": "zero_g_threat_passport",
            "kind": "0g_ready_receipt",
            "summary": passport.get("receipt", {}).get("decision", "receipt ready"),
            "sourceIds": ["0g_chain", "0g_storage_ready_payload"],
            "hash": _hash_json(passport.get("receipt") or {}),
        },
    ]
    return rows


def _operator_next_steps(decision: dict[str, str]) -> list[str]:
    if decision["decision"] == "allow":
        return [
            "Proceed only if the downstream signer policy independently agrees.",
            "Keep a receipt hash with the action log.",
        ]
    return [
        "Do not ask a wallet to sign this request from the public workbench.",
        "Review the top evidence row and source IDs before escalating.",
        "If this is a real integration, run it through an operator-controlled connector with credentials and retention terms reviewed.",
    ]


def _public_subject(subject: dict[str, str], intent: dict[str, Any]) -> dict[str, Any]:
    return {
        "walletRedacted": _redact_text(subject["wallet"]),
        "counterpartyRedacted": _redact_text(subject["counterparty"]),
        "urlHash": _hash_text(subject["url"]),
        "chain": subject["chain"],
        "intent": {
            "action": intent.get("action"),
            "mode": intent.get("mode"),
            "method": intent.get("method"),
            "requiresSignature": intent.get("requires_signature"),
            "promptTextHash": _hash_text(str(intent.get("prompt_text") or "")),
            "calldataHash": _hash_text(str(intent.get("calldata") or "")),
        },
    }


def _redact_text(value: Any) -> str:
    text = str(value or "")
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("***REDACTED***", text)
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f"url:{_hash_text(text)[:12]}"
    if text.startswith("0x") and len(text) >= 18:
        return f"{text[:6]}...{text[-6:]}"
    if "." in text and " " not in text and "/" not in text and len(text) <= 253:
        return f"domain:{_hash_text(text)[:12]}"
    return text


def _safety() -> dict[str, Any]:
    return {
        "readOnly": True,
        "networkCalls": False,
        "walletSignaturesRequested": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "liveStorageUpload": False,
        "paymentSettlementEnabled": False,
        "exchangeOrdersEnabled": False,
        "bridgingEnabled": False,
        "moneyMovementEnabled": False,
        "rawPayloadsReturned": False,
    }


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
