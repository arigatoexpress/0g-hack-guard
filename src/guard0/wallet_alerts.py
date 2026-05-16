"""Read-only wallet alert previews with anti-spam quality gates."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from web3 import Web3

from guard0.crosschain import CHAIN_TARGETS, configured_rpc
from guard0.incident_data import detection_coverage
from guard0.osint import incident_provenance_matrix, signature_map
from guard0.policy import evaluate_intent
from guard0.reputation import build_reputation_probe

WALLET_ALERT_PREVIEW_SCHEMA = "0guard.wallet_alert_preview.v1"
WALLET_ALERT_QUALITY_POLICY_SCHEMA = "0guard.wallet_alert_quality_policy.v1"
DEFAULT_MIN_ALERT_SCORE = 0.72
DEFAULT_MAX_ALERTS = 5
MAX_LIVE_PROBES = 4


def wallet_alert_quality_policy() -> dict[str, Any]:
    """Return the deterministic quality gate for Telegram-worthy wallet alerts."""
    return {
        "schema": WALLET_ALERT_QUALITY_POLICY_SCHEMA,
        "minAlertScore": DEFAULT_MIN_ALERT_SCORE,
        "maxAlertsPerPreview": DEFAULT_MAX_ALERTS,
        "cooldownsSeconds": {
            "critical": 900,
            "high": 1800,
            "medium": 21600,
            "low": 86400,
        },
        "sendEligibilityRules": [
            "direct wallet relevance",
            "source or detector evidence attached",
            "dedupe key not seen inside cooldown window",
            "no low-score informational repeats",
            "opt-in record must include wallet.alerts scope for live sends",
        ],
        "workbenchSendEnabled": False,
        "telegramSendEnabled": False,
    }


def normalize_evm_address(address: str) -> str:
    """Validate and checksum an EVM address without resolving ENS or making network calls."""
    value = str(address or "").strip()
    if not Web3.is_address(value):
        raise ValueError("address must be a valid EVM address")
    return Web3.to_checksum_address(value)


def build_wallet_alert_preview(
    address: str,
    *,
    intent: dict[str, Any] | None = None,
    reputation_context: dict[str, Any] | None = None,
    live: bool = False,
    max_alerts: int = DEFAULT_MAX_ALERTS,
    now: str | None = None,
) -> dict[str, Any]:
    """Build a wallet-specific alert preview without sending or signing anything."""
    normalized_address = normalize_evm_address(address)
    limit = _validate_max_alerts(max_alerts)
    evaluation_intent = _normalize_wallet_intent(intent) if intent is not None else {
        "action": "read_balance",
        "mode": "simulation",
        "method": "eth_getBalance",
        "requires_signature": False,
    }
    amount_issue = _detect_amount_invariant_violation(intent)
    decision = evaluate_intent(
        evaluation_intent,
        agent_id=f"wallet-alert:{normalized_address[:10]}",
        enable_0g_anchor=True,
        enable_0g_storage=True,
    ).to_dict()
    if amount_issue:
        decision = _force_deny_for_amount_issue(decision, amount_issue)
    reputation = _build_reputation_context(
        reputation_context=reputation_context,
        raw_intent=intent,
        evaluation_intent=evaluation_intent,
        wallet_address=normalized_address,
    )
    if reputation:
        decision = _merge_reputation_decision(decision, reputation)
    sig_map = signature_map()
    coverage = detection_coverage()
    provenance = incident_provenance_matrix(live=False)
    quality_policy = wallet_alert_quality_policy()
    alerts = _alerts_from_decision(
        normalized_address,
        decision,
        sig_map,
        provenance,
        quality_policy,
    )
    if reputation:
        alerts.extend(
            _alerts_from_reputation(
                normalized_address,
                reputation,
                quality_policy,
            )
        )
    digest_items = _digest_items(sig_map, coverage, provenance)
    probes = _wallet_read_only_probes(normalized_address, live=live)

    alerts = sorted(alerts, key=lambda item: item["score"], reverse=True)[:limit]
    return {
        "schema": WALLET_ALERT_PREVIEW_SCHEMA,
        "generatedAt": now or datetime.now(timezone.utc).isoformat(),
        "mode": "preview_no_send",
        "wallet": {
            "address": normalized_address,
            "redacted": _redact_address(normalized_address),
            "liveProbes": probes,
        },
        "decision": {
            "decision": decision["decision"],
            "severity": decision["severity"],
            "receiptHash": decision["receipt_hash"],
            "blockers": decision["blockers"],
            "warnings": decision["warnings"],
            "zeroG": decision["zero_g"],
        },
        "alertCount": len(alerts),
        "alerts": alerts,
        "reputation": reputation,
        "digestOnly": digest_items,
        "qualityPolicy": quality_policy,
        "telegramPreview": build_wallet_alert_message(alerts, digest_items, normalized_address),
        "safety": {
            "readOnly": True,
            "networkCalls": live,
            "walletSignaturesRequested": False,
            "transactionBroadcastingEnabled": False,
            "telegramSendEnabled": False,
            "workbenchCanSend": False,
            "rawPayloadsReturned": False,
        },
    }


def _normalize_wallet_intent(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize user-facing wallet intents into the policy evaluation schema.

    The HackQuest demo and steward checks sometimes pass a lightweight
    transaction-like shape (type/amount/to/chain). We translate those into an
    explicit spend-term action so the policy engine can reason about it.
    """
    if not isinstance(intent, dict) or not intent:
        return {
            "action": "read_balance",
            "mode": "simulation",
            "method": "eth_getBalance",
            "requires_signature": False,
        }

    if any(key in intent for key in ("action", "method", "requires_signature", "mode")):
        return intent

    intent_type = str(intent.get("type") or intent.get("kind") or "").strip().lower()
    if intent_type in {"transfer", "send"}:
        return {
            "action": "token_transfer",
            "mode": "simulation",
            "requires_signature": True,
            "prompt_text": _summarize_intent(intent),
            "target_contract": str(intent.get("to") or ""),
        }
    if intent_type in {"approve", "approval"}:
        return {
            "action": "token_approval",
            "mode": "simulation",
            "requires_signature": True,
            "prompt_text": _summarize_intent(intent),
            "target_contract": str(intent.get("token") or intent.get("spender") or ""),
        }
    return {
        "action": "unknown_wallet_intent",
        "mode": "simulation",
        "requires_signature": False,
        "prompt_text": _summarize_intent(intent),
    }


def _summarize_intent(intent: dict[str, Any]) -> str:
    parts = []
    for key in ("type", "asset", "amount", "to", "chain"):
        if key in intent:
            parts.append(f"{key}={intent.get(key)!r}")
    return "wallet_intent(" + ", ".join(parts) + ")"


def _detect_amount_invariant_violation(intent: dict[str, Any] | None) -> str | None:
    if not isinstance(intent, dict):
        return None
    if "amount" not in intent:
        return None
    try:
        amount = float(intent["amount"])
    except (TypeError, ValueError):
        return "amount must be a number"
    if amount <= 0:
        return "negative or zero amount is invalid"
    return None


def _force_deny_for_amount_issue(decision: dict[str, Any], reason: str) -> dict[str, Any]:
    updated = dict(decision)
    blockers = list(updated.get("blockers") or [])
    blockers.insert(0, f"Wallet intent amount invariant: {reason}.")
    updated["blockers"] = blockers
    updated["warnings"] = list(updated.get("warnings") or [])
    updated["decision"] = "deny"
    updated["severity"] = "critical"
    return updated


def _build_reputation_context(
    *,
    reputation_context: dict[str, Any] | None,
    raw_intent: dict[str, Any] | None,
    evaluation_intent: dict[str, Any],
    wallet_address: str,
) -> dict[str, Any] | None:
    context = dict(reputation_context or {})
    raw = raw_intent if isinstance(raw_intent, dict) else {}
    target = (
        context.get("address")
        or context.get("target")
        or raw.get("to")
        or raw.get("target")
        or raw.get("target_contract")
        or evaluation_intent.get("target_contract")
    )
    url = context.get("url") or context.get("domain") or raw.get("url") or raw.get("domain")
    labels = context.get("labels") or raw.get("labels") or []
    evidence = (
        context.get("sourceEvidence")
        or context.get("source_evidence")
        or raw.get("sourceEvidence")
        or raw.get("evidence")
        or []
    )
    if not any([target, url, labels, evidence]):
        return None

    probe = build_reputation_probe(
        {
            "url": url or "",
            "address": target or wallet_address,
            "chain": context.get("chain") or raw.get("chain") or evaluation_intent.get("chain_id") or "",
            "surface": context.get("surface") or raw.get("surface") or "wallet_alert",
            "labels": labels,
            "sourceEvidence": evidence,
            "intent": evaluation_intent,
        }
    )
    return {
        "schema": probe["schema"],
        "mode": probe["mode"],
        "decision": probe["decision"],
        "signalCount": probe["signalCount"],
        "signals": probe["signals"],
        "receipt": probe["receipt"],
        "rightsPolicy": probe["rightsPolicy"],
        "safety": probe["safety"],
    }


def _merge_reputation_decision(
    decision: dict[str, Any],
    reputation: dict[str, Any],
) -> dict[str, Any]:
    reputation_decision = reputation["decision"]["decision"]
    if reputation_decision == "allow":
        return decision

    updated = dict(decision)
    blockers = list(updated.get("blockers") or [])
    warnings = list(updated.get("warnings") or [])
    reasons = reputation["decision"].get("reasons") or ["Reputation probe requires review."]
    if reputation_decision == "deny":
        blockers.append(f"Reputation probe denied counterparty context: {reasons[0]}")
        updated["decision"] = "deny"
        updated["severity"] = "critical"
    elif updated.get("decision") != "deny":
        warnings.append(f"Reputation probe requests review: {reasons[0]}")
        updated["decision"] = "review"
        updated["severity"] = "medium"
    updated["blockers"] = blockers
    updated["warnings"] = warnings
    return updated


def build_wallet_alert_message(
    alerts: list[dict[str, Any]],
    digest_items: list[dict[str, Any]],
    address: str,
) -> str:
    """Render a concise Telegram-safe message preview."""
    if alerts:
        top = alerts[0]
        return "\n".join(
            [
                f"0guard wallet alert for {_redact_address(address)}",
                f"{top['severity'].upper()}: {top['title']}",
                f"Why: {top['whyItMatters']}",
                f"Action: {top['recommendedAction']}",
                "Delivery: preview only, no Telegram message sent.",
            ]
        )
    if digest_items:
        return "\n".join(
            [
                f"0guard wallet digest for {_redact_address(address)}",
                f"No direct wallet alert. Watching {len(digest_items)} emerging detector gaps.",
                "Delivery: preview only, no Telegram message sent.",
            ]
        )
    return "\n".join(
        [
            f"0guard wallet digest for {_redact_address(address)}",
            "No direct wallet alert and no new digest item.",
            "Delivery: preview only, no Telegram message sent.",
        ]
    )


def _alerts_from_decision(
    address: str,
    decision: dict[str, Any],
    sig_map: dict[str, Any],
    provenance: dict[str, Any],
    quality_policy: dict[str, Any],
) -> list[dict[str, Any]]:
    verdict = decision.get("decision")
    blockers = decision.get("blockers") or []
    warnings = decision.get("warnings") or []
    if verdict not in {"deny", "review"}:
        return []

    top_reason = (blockers or warnings or ["Policy review required."])[0]
    if str(top_reason).lower().startswith("reputation probe"):
        return []

    severity = str(decision.get("severity") or "medium")
    score = 0.97 if verdict == "deny" else 0.78
    if blockers and any("signature" in blocker.lower() for blocker in blockers):
        score = max(score, 0.99)
    if warnings and any("bridge" in warning.lower() for warning in warnings):
        score = max(score, 0.86)
    source_ids = _source_ids_for_alert(sig_map, provenance, top_reason)
    alert_id = _stable_id(
        {
            "address": address.lower(),
            "receipt": decision.get("receipt_hash"),
            "reason": top_reason,
            "verdict": verdict,
        }
    )

    return [
        {
            "id": f"wal_{alert_id[:24]}",
            "severity": severity,
            "score": round(score, 4),
            "title": _alert_title(verdict, top_reason),
            "whyItMatters": top_reason,
            "walletRelevance": "direct_intent_for_wallet",
            "recommendedAction": _recommended_action(verdict),
            "receiptHash": decision.get("receipt_hash"),
            "dedupeKey": _stable_id({"address": address.lower(), "reason": top_reason})[:32],
            "cooldownSeconds": quality_policy["cooldownsSeconds"].get(severity, 21600),
            "sourceIds": source_ids,
            "sendPolicy": _send_policy(score, "direct_intent_for_wallet", quality_policy),
        }
    ]


def _alerts_from_reputation(
    address: str,
    reputation: dict[str, Any],
    quality_policy: dict[str, Any],
) -> list[dict[str, Any]]:
    verdict = reputation["decision"]["decision"]
    if verdict not in {"deny", "review"}:
        return []
    severity = reputation["decision"].get("severity") or ("critical" if verdict == "deny" else "medium")
    score = 0.94 if verdict == "deny" else 0.8
    top_reason = (reputation["decision"].get("reasons") or ["Reputation review required."])[0]
    source_ids = sorted(
        {
            signal["evidence"].get("sourceId", signal["id"])
            for signal in reputation.get("signals") or []
            if isinstance(signal.get("evidence"), dict)
        }
        or {"reputation_probe"}
    )
    return [
        {
            "id": f"rep_{reputation['receipt']['hash'][:24]}",
            "severity": severity,
            "score": round(score, 4),
            "title": _reputation_alert_title(top_reason),
            "whyItMatters": top_reason,
            "walletRelevance": "counterparty_or_domain_context",
            "recommendedAction": _recommended_action(verdict),
            "receiptHash": reputation["receipt"]["hash"],
            "dedupeKey": _stable_id(
                {
                    "address": address.lower(),
                    "reputationReceipt": reputation["receipt"]["hash"],
                    "reason": top_reason,
                }
            )[:32],
            "cooldownSeconds": quality_policy["cooldownsSeconds"].get(severity, 21600),
            "sourceIds": source_ids,
            "sendPolicy": _send_policy(score, "counterparty_or_domain_context", quality_policy),
        }
    ]


def _digest_items(
    sig_map: dict[str, Any],
    coverage: dict[str, Any],
    provenance: dict[str, Any],
) -> list[dict[str, Any]]:
    items = []
    if not (sig_map.get("topGaps") or {}):
        items.append(
            {
                "type": "detector_coverage_complete",
                "incidentCount": sig_map.get("incidentCount", coverage.get("incidentCount")),
                "matchedCount": sig_map.get("matchedCount", coverage.get("coveredCount")),
                "priority": "digest_only",
                "sourceEvidenceCoverage": provenance["coverage"]["evidenceCoverageRatio"],
                "coverageRatio": coverage["coverageRatio"],
                "alertEligible": False,
                "reason": "All source-linked incident patterns currently map to detector signatures.",
            }
        )
    for gap, count in (sig_map.get("topGaps") or {}).items():
        items.append(
            {
                "type": "emerging_detector_gap",
                "gap": gap,
                "incidentCount": count,
                "priority": "digest_only",
                "sourceEvidenceCoverage": provenance["coverage"]["evidenceCoverageRatio"],
                "coverageRatio": coverage["coverageRatio"],
                "alertEligible": False,
                "reason": "Not wallet-specific until a matching intent, calldata, or source pattern appears.",
            }
        )
    return items[:3]


def _wallet_read_only_probes(address: str, *, live: bool) -> dict[str, Any]:
    rows = []
    attempted = 0
    for target in [target for target in CHAIN_TARGETS if target.evm_compatible and target.probe_default][
        :MAX_LIVE_PROBES
    ]:
        row = {
            "chainId": target.chain_id,
            "network": target.name,
            "targetId": target.id,
            "liveChecked": False,
            "status": "not_checked",
            "balanceWei": None,
            "transactionCount": None,
            "latestBlockNumber": None,
            "latencyMs": None,
            "error": None,
        }
        if live:
            attempted += 1
            row.update(_probe_wallet_on_target(address, target))
        rows.append(row)
    return {
        "live": live,
        "attempted": attempted,
        "checked": sum(1 for row in rows if row["status"] == "ok"),
        "probes": rows,
    }


def _probe_wallet_on_target(address: str, target: Any) -> dict[str, Any]:
    rpc = configured_rpc(target)
    if not rpc:
        return {"liveChecked": True, "status": "rpc_not_configured"}
    started = time.perf_counter()
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 3}))
        observed_chain_id = int(w3.eth.chain_id)
        balance = int(w3.eth.get_balance(address))
        tx_count = int(w3.eth.get_transaction_count(address))
        block_number = int(w3.eth.block_number)
        expected_chain_id = target.chain_id
        return {
            "liveChecked": True,
            "status": "ok" if observed_chain_id == expected_chain_id else "chain_id_mismatch",
            "observedChainId": observed_chain_id,
            "balanceWei": str(balance),
            "transactionCount": tx_count,
            "latestBlockNumber": block_number,
            "latencyMs": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:  # pragma: no cover - live RPC dependent
        return {
            "liveChecked": True,
            "status": "degraded",
            "latencyMs": int((time.perf_counter() - started) * 1000),
            "error": f"{type(exc).__name__}: {exc}",
        }


def _source_ids_for_alert(
    sig_map: dict[str, Any],
    provenance: dict[str, Any],
    top_reason: str,
) -> list[str]:
    source_ids = {"policy_engine"}
    lower_reason = top_reason.lower()
    for row in sig_map.get("rows") or []:
        row_blob = json.dumps(row, sort_keys=True, default=str).lower()
        if "approval" in lower_reason and "approval" in row_blob:
            source_ids.add("signature_map")
        if "bridge" in lower_reason and "bridge" in row_blob:
            source_ids.add("signature_map")
        if "upgrade" in lower_reason and "upgrade" in row_blob:
            source_ids.add("signature_map")
    if provenance["coverage"]["withMatchedEvidence"]:
        source_ids.add("incident_provenance")
    return sorted(source_ids)


def _send_policy(
    score: float,
    wallet_relevance: str,
    quality_policy: dict[str, Any],
) -> dict[str, Any]:
    telegram_eligible = (
        score >= quality_policy["minAlertScore"]
        and wallet_relevance in {"direct_intent_for_wallet", "counterparty_or_domain_context"}
    )
    return {
        "telegramEligibleAfterOptIn": telegram_eligible,
        "wouldSendFromWorkbench": False,
        "reason": (
            "eligible_in_live_bot_after_opt_in_and_cooldown"
            if telegram_eligible
            else "digest_only_or_below_threshold"
        ),
    }


def _recommended_action(verdict: str) -> str:
    if verdict == "deny":
        return "Do not sign. Simulate or inspect the transaction from a separate read-only wallet view."
    return "Review before signing and wait for a clearer source-backed explanation."


def _alert_title(verdict: str, reason: str) -> str:
    reason_lower = reason.lower()
    if "approval" in reason_lower or "approve" in reason_lower:
        return "Unlimited or dangerous approval attempt"
    if "bridge" in reason_lower:
        return "Bridge message or verifier risk"
    if "upgrade" in reason_lower:
        return "Proxy upgrade or admin-control risk"
    if "negative amount" in reason_lower or "accounting invariant" in reason_lower:
        return "Accounting-invariant exploit attempt"
    if "signedness" in reason_lower or "bounded-math" in reason_lower:
        return "Numeric settlement invariant risk"
    if verdict == "deny":
        return "Blocked wallet-signing request"
    return "Human review recommended"


def _reputation_alert_title(reason: str) -> str:
    reason_lower = reason.lower()
    if "suffix" in reason_lower or "domain" in reason_lower:
        return "Suspicious domain or counterparty context"
    if "malicious" in reason_lower or "compromised" in reason_lower:
        return "Known malicious counterparty"
    if "source evidence" in reason_lower or "reputation" in reason_lower:
        return "Negative reputation evidence"
    return "Counterparty reputation review"


def _validate_max_alerts(max_alerts: int) -> int:
    if isinstance(max_alerts, bool) or not isinstance(max_alerts, int):
        raise ValueError("max_alerts must be an integer")
    if max_alerts < 1 or max_alerts > 20:
        raise ValueError("max_alerts must be between 1 and 20")
    return max_alerts


def _stable_id(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _redact_address(address: str) -> str:
    return f"{address[:6]}...{address[-4:]}"
