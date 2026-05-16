"""Convert live OSINT signals into detector candidates.

The candidate layer is deliberately not a claim that a new detector is already
production-ready. It is a reproducible bridge from a public signal into the
next regression test, preflight seed, and review gate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from guard0.crypto_hack_guard import check_crypto_hack_signatures
from guard0.osint import osint_signals
from guard0.policy import normalize_intent

DETECTOR_CANDIDATES_SCHEMA = "0guard.detector_candidates.v1"

_CHAIN_IDS = {
    "ethereum": "eip155:1",
    "base": "eip155:8453",
    "arbitrum": "eip155:42161",
    "arbitrum one": "eip155:42161",
    "optimism": "eip155:10",
    "polygon": "eip155:137",
    "polygon pos": "eip155:137",
    "bsc": "eip155:56",
    "bnb chain": "eip155:56",
    "berachain": "eip155:80094",
    "blast": "eip155:81457",
    "0g": "eip155:16661",
    "zero-g": "eip155:16661",
}

_FAMILY_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "proxy_initialization_guard",
        "keywords": ("uninitialized proxy", "initializer", "implementation upgrade", "proxy exploit"),
        "why": "Proxy initialization and upgrade mistakes should be blocked before admin or signer prompts.",
        "rule": "Flag initialize, upgradeTo, upgradeToAndCall, and owner/admin handoff calls on contracts without verified initialization context.",
        "test": "test_live_candidate_proxy_initialization_guard",
    },
    {
        "id": "deprecated_contract_guard",
        "keywords": ("deprecated", "old contract", "legacy contract"),
        "why": "Deprecated-contract interaction is a common avoidable user and agent failure mode.",
        "rule": "Require explicit review when an intent targets a deprecated contract, stale router, or noncanonical protocol address.",
        "test": "test_live_candidate_deprecated_contract_guard",
    },
    {
        "id": "address_poisoning_flow_guard",
        "keywords": ("address poisoning", "vault churn", "churn address", "poisoning"),
        "why": "Lookalike destination and churn-address attacks are best stopped before wallet confirmation.",
        "rule": "Compare destination, counterparty history, ENS/name metadata, and recent transfer graph before allowing a transfer or vault action.",
        "test": "test_live_candidate_address_poisoning_flow_guard",
    },
    {
        "id": "bridge_message_guard",
        "keywords": ("bridge", "cross-chain", "layerzero", "oft", "wormhole", "ccip", "message"),
        "why": "Bridge and cross-chain message paths need stricter proof, validator, and replay checks.",
        "rule": "Escalate cross-chain sends when validator quorum, source/destination chain, nonce, or replay context is incomplete.",
        "test": "test_live_candidate_bridge_message_guard",
    },
    {
        "id": "oracle_price_manipulation_guard",
        "keywords": ("oracle", "price", "twap", "manipulation", "fake token price"),
        "why": "Price manipulation is detectable as an intent/context mismatch before liquidation, mint, or swap actions.",
        "rule": "Require fresh oracle, liquidity, and deviation context for price-sensitive swaps, borrows, liquidations, and mints.",
        "test": "test_live_candidate_oracle_price_manipulation_guard",
    },
    {
        "id": "privileged_key_compromise_guard",
        "keywords": ("admin key", "private key", "compromised", "owner key", "access control"),
        "why": "Privileged-key failures should trigger extra guardrails around admin, owner, and treasury calls.",
        "rule": "Deny or require multisig/manual review for privileged calls when provenance or role context is missing.",
        "test": "test_live_candidate_privileged_key_compromise_guard",
    },
    {
        "id": "approval_permit_guard",
        "keywords": ("approval", "permit", "allowance", "unlimited", "spender"),
        "why": "Approvals and permits are the highest-frequency pre-wallet checkpoint for consumer and agent flows.",
        "rule": "Deny unlimited approvals and suspicious permit payloads unless spender reputation and scoped allowance are verified.",
        "test": "test_live_candidate_approval_permit_guard",
    },
    {
        "id": "flash_loan_accounting_guard",
        "keywords": ("flash loan", "rounding", "accounting", "invariant", "mint", "burn"),
        "why": "Accounting and invariant failures can be translated into simulation assertions before execution.",
        "rule": "Route mint, burn, withdraw, liquidation, and flash-loan bundles through invariant and balance-delta simulation.",
        "test": "test_live_candidate_flash_loan_accounting_guard",
    },
)


def live_detector_candidates(
    *,
    live: bool = False,
    limit: int = 10,
    signals_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return detector candidates derived from public OSINT signals."""
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    signals = signals_payload if signals_payload is not None else osint_signals(live=live, limit=limit)
    if not isinstance(signals, dict):
        raise ValueError("signals payload must be an object")

    candidates = [
        candidate
        for signal in signals.get("signals", [])
        if isinstance(signal, dict)
        for candidate in [_candidate_from_signal(signal)]
        if candidate is not None
    ][:limit]

    return {
        "schema": DETECTOR_CANDIDATES_SCHEMA,
        "generatedAt": _now(),
        "live": bool(signals.get("live", live)),
        "mode": "source_signal_to_regression_candidate",
        "sourceStatus": signals.get("sourceStatus", []),
        "signalCount": int(signals.get("signalCount") or len(signals.get("signals", []))),
        "candidateCount": len(candidates),
        "highPriorityCount": sum(
            1 for candidate in candidates if candidate["priority"] in {"critical", "high"}
        ),
        "candidates": candidates,
        "promotionGate": [
            "Keep source id, source link, and record hash attached to the candidate.",
            "Add a deterministic intent/calldata fixture before moving from candidate to detector.",
            "Add a regression test and at least one benign false-positive control.",
            "Only alert users after the rule passes preview, shadow, and operator review stages.",
        ],
        "honestLimits": [
            "Candidates are not production detectors until a regression test and false-positive control exist.",
            "The route returns derived metadata only and does not expose raw upstream payloads.",
            "No mempool subscription, wallet tracking, Telegram send, signing, broadcast, bridge, or swap happens here.",
        ],
        "safety": _safety(),
    }


def _candidate_from_signal(signal: dict[str, Any]) -> dict[str, Any] | None:
    title = str(signal.get("title") or "").strip()
    if not title:
        return None

    technique = str(signal.get("technique") or "").strip()
    classification = str(signal.get("classification") or "").strip()
    categories = signal.get("categories") if isinstance(signal.get("categories"), list) else []
    text = " ".join(
        str(value)
        for value in (
            title,
            technique,
            classification,
            signal.get("targetType") or "",
            " ".join(str(category) for category in categories),
        )
        if value
    )
    families = _families_for_text(text)
    if not families and signal.get("signalType") == "research_link" and not signal.get("securityRelevant"):
        return None
    if not families:
        families = [_default_family()]

    chain_focus = _chain_focus(signal.get("chains"))
    preflight_seed = _preflight_seed(signal, families, chain_focus)
    signature_preview = check_crypto_hack_signatures(normalize_intent(preflight_seed)).to_dict()
    priority = _priority(signal, families)
    record_hash = str(signal.get("recordHash") or _hash_json(signal))

    return {
        "schema": "0guard.detector_candidate.v1",
        "candidateId": f"cand_{record_hash[:16]}",
        "sourceId": signal.get("sourceId"),
        "sourceLink": signal.get("sourceLink") or signal.get("link"),
        "recordHash": record_hash,
        "rawPayloadReturned": False,
        "observedAt": signal.get("observedAt"),
        "title": title,
        "signalType": signal.get("signalType"),
        "amountUsd": signal.get("amountUsd"),
        "chains": _chain_list(signal.get("chains")),
        "classification": classification,
        "technique": technique,
        "priority": priority,
        "families": families,
        "chainFocus": chain_focus,
        "preflightSeed": preflight_seed,
        "currentSignaturePreview": {
            "decision": _signature_decision(signature_preview),
            "severity": _signature_severity(signature_preview),
            "signaturesMatched": signature_preview.get("signatures_matched", []),
            "blockerCount": len(signature_preview.get("blockers", [])),
            "warningCount": len(signature_preview.get("warnings", [])),
        },
        "promotionStatus": "candidate_needs_regression_test",
        "nextRegressionTest": _next_test_name(families, record_hash),
    }


def _families_for_text(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    families: list[dict[str, str]] = []
    for rule in _FAMILY_RULES:
        if any(keyword in lowered for keyword in rule["keywords"]):
            families.append(
                {
                    "id": rule["id"],
                    "why": rule["why"],
                    "candidateRule": rule["rule"],
                    "testTemplate": rule["test"],
                }
            )
    return families


def _default_family() -> dict[str, str]:
    return {
        "id": "incident_context_review",
        "why": "A new public incident still improves wallet prompts by adding provenance, chain, loss, and technique context.",
        "candidateRule": "Create a review-only note until a reproducible intent, selector, trace, or simulation pattern is available.",
        "testTemplate": "test_live_candidate_incident_context_review",
    }


def _preflight_seed(
    signal: dict[str, Any],
    families: list[dict[str, str]],
    chain_focus: dict[str, Any],
) -> dict[str, Any]:
    family_ids = {family["id"] for family in families}
    if "approval_permit_guard" in family_ids:
        action = "approve"
    elif "bridge_message_guard" in family_ids:
        action = "cross_chain_send"
    elif "privileged_key_compromise_guard" in family_ids or "proxy_initialization_guard" in family_ids:
        action = "admin_call"
    elif "oracle_price_manipulation_guard" in family_ids:
        action = "price_sensitive_swap"
    else:
        action = "agent_transaction"

    return {
        "action": action,
        "mode": "live_transaction",
        "requires_signature": True,
        "chain": chain_focus["caip2"] or "unknown",
        "surface": "live_osint_detector_candidate",
        "source_id": signal.get("sourceId"),
        "source_record_hash": signal.get("recordHash"),
        "prompt_text": (
            f"Review {signal.get('title')} before any signer is invoked. "
            f"Technique: {signal.get('technique') or 'not provided'}."
        ),
        "steps": [
            {"action": "attach_source_provenance", "source_id": signal.get("sourceId")},
            {"action": "build_intent_fixture", "record_hash": signal.get("recordHash")},
            {"action": "run_signature_preview", "mode": "deterministic"},
            {"action": "add_regression_test_before_alerting", "required": True},
        ],
    }


def _priority(signal: dict[str, Any], families: list[dict[str, str]]) -> str:
    amount = _int(signal.get("amountUsd"))
    family_ids = {family["id"] for family in families}
    if amount >= 10_000_000 or "bridge_message_guard" in family_ids:
        return "critical"
    if amount >= 1_000_000 or "arbitrum" in [chain.lower() for chain in _chain_list(signal.get("chains"))]:
        return "high"
    if amount >= 100_000 or signal.get("securityRelevant"):
        return "medium"
    return "watch"


def _signature_decision(signature_preview: dict[str, Any]) -> str:
    if signature_preview.get("blockers"):
        return "deny"
    if signature_preview.get("warnings") or signature_preview.get("signatures_matched"):
        return "review"
    return "allow"


def _signature_severity(signature_preview: dict[str, Any]) -> str:
    if signature_preview.get("blockers"):
        return "critical"
    if signature_preview.get("warnings") or signature_preview.get("signatures_matched"):
        return "medium"
    return "info"


def _chain_focus(value: Any) -> dict[str, Any]:
    chains = _chain_list(value)
    for chain in chains:
        caip2 = _CHAIN_IDS.get(chain.lower())
        if caip2:
            return {"name": chain, "caip2": caip2, "recognized": True}
    return {"name": chains[0] if chains else "", "caip2": "", "recognized": False}


def _chain_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _next_test_name(families: list[dict[str, str]], record_hash: str) -> str:
    template = families[0].get("testTemplate") or "test_live_candidate_regression"
    return f"{template}_{record_hash[:8]}"


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "rawPayloadsReturned": False,
        "privateKeyRequired": False,
        "transactionSigningEnabled": False,
        "broadcastingEnabled": False,
        "bridgingEnabled": False,
        "swappingEnabled": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "candidatePromotionAutomatic": False,
    }


def _hash_json(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
