"""Deterministic Mira preview helpers for Telegram-facing 0guard flows."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from guard0.policy import evaluate_intent

MIRA_PREVIEW_SCHEMA = "0guard.mira_preview.v1"
MIRA_CLAIM_PREVIEW_SCHEMA = "0guard.mira_claim_preview.v1"


def build_mira_security_preview(
    intent: dict[str, Any],
    *,
    opt_in_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Telegram-safe Mira response preview without sending anything."""
    decision = evaluate_intent(intent).to_dict()
    verdict = decision.get("decision", "review")
    blockers = decision.get("blockers") or []
    warnings = decision.get("warnings") or []

    if verdict == "deny":
        headline = "Mira blocked this agent action before wallet signing."
    elif verdict == "allow":
        headline = "Mira found no policy blockers for this simulation."
    else:
        headline = "Mira marked this action for human review."

    reasons = blockers or warnings or decision.get("reasons") or ["No high-risk signature matched."]
    lines = [
        f"0guard Mira: {headline}",
        f"Verdict: {str(verdict).upper()}",
        f"Top reason: {reasons[0]}",
        "Delivery: preview only, no Telegram message sent.",
    ]

    return {
        "schema": MIRA_PREVIEW_SCHEMA,
        "delivery": "preview_no_send",
        "telegram_send": False,
        "network_calls": False,
        "opt_in_status": (opt_in_record or {}).get("status", "not_attached"),
        "record_id": (opt_in_record or {}).get("record_id"),
        "message": "\n".join(lines),
        "decision": decision,
    }


def build_mira_claim_preview(
    *,
    subject: dict[str, Any],
    claims: list[dict[str, Any]],
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build an external-Mira-ready claim packet without making network calls."""
    evidence = evidence or []
    normalized_claims = []
    for index, claim in enumerate(claims):
        claim_id = str(claim.get("id") or f"claim_{index + 1}")
        claim_text = str(claim.get("claim") or "").strip()
        if not claim_text:
            continue
        normalized_claims.append(
            {
                "id": claim_id,
                "claim": claim_text,
                "status": "ready_for_external_mira_verification",
                "confidenceMode": "local_deterministic_preview",
                "evidenceSourceIds": list(claim.get("evidenceSourceIds") or []),
            }
        )

    packet = {
        "subject": subject,
        "claims": normalized_claims,
        "evidenceHashes": [_hash_json(item) for item in evidence],
    }
    return {
        "schema": MIRA_CLAIM_PREVIEW_SCHEMA,
        "delivery": "preview_no_send",
        "externalMiraCalls": False,
        "network_calls": False,
        "miraVerifyReady": bool(normalized_claims),
        "subject": subject,
        "claimCount": len(normalized_claims),
        "claims": normalized_claims,
        "evidence": [
            {
                "sourceId": item.get("sourceId"),
                "kind": item.get("kind"),
                "url": item.get("url"),
                "hash": _hash_json(item),
            }
            for item in evidence
        ],
        "receiptHash": _hash_json(packet),
        "officialSources": [
            "https://verify.mira.network/",
            "https://docs.mira.co/",
            "https://mira.network/research/mira-whitepaper.pdf",
        ],
        "safety": {
            "telegram_send": False,
            "rawPayloadsReturned": False,
            "walletSignaturesRequested": False,
            "moneyMovementEnabled": False,
        },
    }


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
