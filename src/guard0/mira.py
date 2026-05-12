"""Deterministic Mira preview helpers for Telegram-facing 0guard flows."""

from __future__ import annotations

from typing import Any

from guard0.policy import evaluate_intent

MIRA_PREVIEW_SCHEMA = "0guard.mira_preview.v1"


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
