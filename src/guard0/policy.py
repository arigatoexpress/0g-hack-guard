"""
Policy Engine — Intent Firewall with Hack Detection
====================================================
Evaluates agent intents against safety rules + crypto-hack signatures.
Emits allow / review / deny decisions with SHA-256 receipt hashes.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from guard0.crypto_hack_guard import check_crypto_hack_signatures
from guard0.chain import anchor_receipt
from guard0.storage import store_threat_intel


# ── Constants ────────────────────────────────────────────────────────────────

READ_ONLY_RPC_METHODS = frozenset({
    "eth_call", "eth_getBalance", "eth_getCode", "eth_getStorageAt",
    "eth_getTransactionCount", "eth_getBlockByNumber", "eth_getBlockByHash",
    "eth_getTransactionReceipt", "eth_getLogs", "eth_chainId",
    "eth_estimateGas", "eth_gasPrice", "eth_blockNumber",
})

DENIED_RPC_METHODS = frozenset({
    "eth_sendRawTransaction", "eth_sendTransaction", "eth_sign",
    "eth_signTransaction", "eth_signTypedData", "personal_sign",
    "wallet_requestPermissions", "wallet_addEthereumChain",
})

SAFE_ACTIONS = frozenset({
    "scout", "catalog", "read_balance", "simulate", "preview",
    "health_check", "domain_check", "hack_check",
})

SIMULATION_PREFIXES = ("simulate_", "preview_", "dry_run_", "quote_")

SPEND_ACTION_TERMS = frozenset({
    "buy", "bridge", "deposit", "swap", "sign", "wager", "bet",
    "transfer", "send", "mint", "launch", "stake", "unstake", "claim",
    "approve", "withdraw", "donate", "pay",
})

SECRET_EGRESS_PATTERNS = (
    r"private\s*key",
    r"seed\s*phrase",
    r"mnemonic",
    r"api\s*key",
    r"0x[a-fA-F0-9]{64}",
    r"[a-zA-Z0-9]{24,}\.[a-zA-Z0-9]{6,}\.[a-zA-Z0-9]{24,}",  # JWT-ish
)

PROMPT_INJECTION_PATTERNS = (
    r"ignore\s+(previous|all\s+previous)\s+instructions",
    r"bypass\s+(security|guard|safety|policy)",
    r"disable\s+(guard|safety|protection|check)",
    r"you\s+are\s+now\s+in\s+.*mode",
    r"DAN\s+mode",
    r"jailbreak",
)

DEFAULT_BUDGET_CAPS = {
    "max_value_eth": 0.1,
    "max_approval_usd": 1_000,
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PolicyDecision:
    decision: str  # allow | review | deny
    severity: str  # low | medium | high | critical
    action: str
    mode: str
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    allowed_next_steps: tuple[str, ...] = ()
    receipt_hash: str = ""
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "severity": self.severity,
            "action": self.action,
            "mode": self.mode,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "allowed_next_steps": list(self.allowed_next_steps),
            "receipt_hash": self.receipt_hash,
            "generated_at": self.generated_at,
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

def contains_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def action_has_spend_term(action: str) -> bool:
    return any(term in action.lower() for term in SPEND_ACTION_TERMS)


def redact_intent(intent: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for k, v in intent.items():
        lk = k.lower()
        if any(s in lk for s in ("secret", "private", "mnemonic", "seed", "token", "key", "password")):
            redacted[k] = "***REDACTED***"
        else:
            redacted[k] = v
    return redacted


def normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": str(intent.get("action") or "").strip(),
        "method": str(intent.get("method") or "").strip(),
        "mode": str(intent.get("mode") or "simulation").strip(),
        "prompt_text": str(intent.get("prompt_text") or intent.get("text") or "").strip(),
        "value_eth": float(intent.get("value_eth") or 0),
        "app": str(intent.get("app") or "").strip(),
        "chain_id": int(intent.get("chain_id") or 0),
        "requires_signature": bool(intent.get("requires_signature", False)),
        "calldata": str(intent.get("calldata") or intent.get("data") or "").strip(),
        "steps": intent.get("steps") or intent.get("operations") or [],
        "target_contract": str(intent.get("target_contract") or intent.get("to") or "").strip(),
    }


def _receipt_hash(context: dict[str, Any]) -> str:
    blob = json.dumps(context, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(blob).hexdigest()


# ── Main Evaluation ──────────────────────────────────────────────────────────

def evaluate_intent(
    intent: dict[str, Any],
    budget: dict[str, Any] | None = None,
    agent_id: str = "",
    enable_0g_anchor: bool = False,
    enable_0g_storage: bool = False,
) -> PolicyDecision:
    payload = normalize_intent(intent)
    blockers: list[str] = []
    warnings: list[str] = []
    allowed_next_steps: list[str] = []

    caps = {**DEFAULT_BUDGET_CAPS, **(budget or {})}

    # ── RPC method guard ───────────────────────────────────────────────────
    method = payload["method"]
    if method:
        if method in DENIED_RPC_METHODS:
            blockers.append(f"RPC method '{method}' is denied.")
        elif method not in READ_ONLY_RPC_METHODS:
            warnings.append(f"RPC method '{method}' is unrecognized.")

    # ── Secret egress guard ────────────────────────────────────────────────
    prompt = payload["prompt_text"]
    if contains_pattern(prompt, SECRET_EGRESS_PATTERNS):
        blockers.append("Secret-bearing content detected in prompt text.")

    # ── Prompt-injection guard ─────────────────────────────────────────────
    if contains_pattern(prompt, PROMPT_INJECTION_PATTERNS):
        blockers.append("Prompt-injection pattern detected.")

    # ── Crypto hack signature guard (NEW) ──────────────────────────────────
    hack = check_crypto_hack_signatures(payload)
    blockers.extend(hack.blockers)
    warnings.extend(hack.warnings)

    # ── Action safety guard ────────────────────────────────────────────────
    action = payload["action"]
    if action:
        if action in SAFE_ACTIONS or action.startswith(SIMULATION_PREFIXES):
            allowed_next_steps.append(action)
        elif action_has_spend_term(action):
            if payload["mode"] not in ("simulation", "preview", "dry_run"):
                blockers.append(f"Action '{action}' is a spend term and mode is live.")
            else:
                warnings.append(f"Action '{action}' is flagged as spendy but in sim mode.")
        else:
            warnings.append(f"Action '{action}' is not in the safe-actions list.")

    # ── Budget guard ───────────────────────────────────────────────────────
    value_eth = payload["value_eth"]
    max_val = float(caps.get("max_value_eth", 0))
    if max_val and value_eth > max_val:
        blockers.append(f"Value {value_eth} ETH exceeds budget cap {max_val} ETH.")

    # ── Signature guard ────────────────────────────────────────────────────
    if payload["requires_signature"] and payload["mode"] not in ("simulation", "preview"):
        blockers.append("Intent requires a wallet signature in non-simulation mode.")

    # ── Decision logic ─────────────────────────────────────────────────────
    if blockers:
        decision = "deny"
        severity = "critical" if any("secret" in b.lower() or "signature" in b.lower() or "critical" in b.lower() for b in blockers) else "high"
    elif warnings:
        decision = "review"
        severity = "medium"
        allowed_next_steps.append("human_review")
    else:
        decision = "allow"
        severity = "low"
        allowed_next_steps.extend(["proceed", "simulate_first"])

    # ── Receipt generation ─────────────────────────────────────────────────
    receipt_ctx = {
        "decision": decision,
        "severity": severity,
        "action": action,
        "mode": payload["mode"],
        "blockers": blockers,
        "warnings": warnings,
        "agent_id": agent_id,
        "hack_signatures": list(hack.signatures_matched),
        "iocs": list(hack.iocs_hit),
    }
    receipt_hash = _receipt_hash(receipt_ctx)

    # ── 0G Chain anchoring (optional) ──────────────────────────────────────
    if enable_0g_anchor:
        anchor_receipt(receipt_hash, decision, severity, agent_id)

    # ── 0G Storage persistence (optional) ──────────────────────────────────
    if enable_0g_storage and (hack.signatures_matched or hack.iocs_hit):
        store_threat_intel(
            key=f"intent-{receipt_hash[:16]}",
            data={
                "receipt_hash": receipt_hash,
                "signatures_matched": list(hack.signatures_matched),
                "iocs_hit": list(hack.iocs_hit),
                "decision": decision,
                "severity": severity,
            },
            tags=["hack-guard", "intent-evaluation", "april-2026"],
        )

    return PolicyDecision(
        decision=decision,
        severity=severity,
        action=action,
        mode=payload["mode"],
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        allowed_next_steps=tuple(allowed_next_steps),
        receipt_hash=receipt_hash,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
