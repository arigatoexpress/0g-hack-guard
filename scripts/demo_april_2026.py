#!/usr/bin/env python3
"""
Demo: 0G Hack Guard detecting real April 2026 exploit signatures.

Run:
    python3 scripts/demo_april_2026.py
"""
from __future__ import annotations

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from guard0.policy import evaluate_intent


def banner(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def show(result: dict) -> None:
    print(json.dumps(result, indent=2))
    print()


# ── 1. Drift Protocol — Durable nonce social engineering ─────────────────────
banner("1. DRIFT PROTOCOL — Durable Nonce Social Engineering ($285M)")
drift = evaluate_intent({
    "action": "sign",
    "mode": "live_transaction",
    "prompt_text": "Please pre-sign this durable nonce transaction to transfer admin powers to our new trading partner.",
    "requires_signature": True,
})
show(drift.to_dict())

# ── 2. Kelp DAO — LayerZero 1-of-1 DVN bridge forgery ────────────────────────
banner("2. KELP DAO — Bridge Forgery via 1-of-1 DVN ($293M)")
kelp = evaluate_intent({
    "action": "lzReceive",
    "mode": "live_transaction",
    "calldata": "0x3f7658ff...",  # lzReceive selector
    "prompt_text": "Release 116,500 rsETH via LayerZero with requiredDVNCount: 1",
    "value_eth": 0,
})
show(kelp.to_dict())

# ── 3. Wasabi Protocol — UUPS upgrade via compromised deployer ───────────────
banner("3. WASABI PROTOCOL — UUPS Upgrade Takeover ($5M+)")
wasabi = evaluate_intent({
    "action": "upgrade",
    "mode": "live_transaction",
    "calldata": "0x3659cfe60000000000000000000000002228b0afcdbedf8180d96fc181da3af5dd1d1ab",
    "target_contract": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
    "requires_signature": True,
})
show(wasabi.to_dict())

# ── 4. Rhea Finance — Flash-loan + fake collateral ───────────────────────────
banner("4. RHEA FINANCE — Flash-Loan + Fake Collateral ($18.4M)")
rhea = evaluate_intent({
    "action": "flashLoan",
    "mode": "live_transaction",
    "steps": [
        {"action": "flashLoan", "calldata": "0xab9c4b5d..."},
        {"action": "swap", "calldata": "0x..."},
        {"action": "withdraw", "calldata": "0x..."},
    ],
})
show(rhea.to_dict())

# ── 5. Giddy Finance — Unlimited approval / signature replay ─────────────────
banner("5. GIDDY FINANCE — Unlimited Approval / Signature Replay ($1.3M)")
giddy = evaluate_intent({
    "action": "approve",
    "mode": "live_transaction",
    "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "requires_signature": True,
})
show(giddy.to_dict())

# ── 6. Safe intent (should ALLOW) ────────────────────────────────────────────
banner("6. SAFE INTENT — Read-only balance check (should ALLOW)")
safe = evaluate_intent({
    "action": "read_balance",
    "method": "eth_getBalance",
    "mode": "simulation",
})
show(safe.to_dict())

banner("Demo complete")
print("All evaluations emitted receipt hashes. In production these can be anchored on 0G Chain.")
