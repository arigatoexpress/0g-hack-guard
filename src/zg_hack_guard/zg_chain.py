"""
0G Chain Integration — Policy Receipt Anchoring
================================================
0G Chain is an EVM-compatible blockchain (Chain ID configurable via env).
This module anchors SHA-256 policy receipt hashes on-chain so decisions are
auditable, tamper-evident, and verifiable by third parties.

Intended contract: PolicyReceiptAnchor (see contracts/PolicyReceiptAnchor.sol)
"""
from __future__ import annotations

import os
from typing import Any

ZGG_CHAIN_RPC = os.getenv("ZGG_CHAIN_RPC", "https://evmrpc.0g.ai")
ZGG_CHAIN_ID = int(os.getenv("ZGG_CHAIN_ID", "16600"))
ZGG_RECEIPT_CONTRACT = os.getenv(
    "ZGG_RECEIPT_CONTRACT",
    "0x0000000000000000000000000000000000000000",  # placeholder until deployed
)


def anchor_receipt(
    receipt_hash: str,
    decision: str,
    severity: str,
    agent_id: str = "",
) -> dict[str, Any]:
    """
    Anchor a policy receipt hash on 0G Chain.

    In live mode this builds & signs a transaction to the PolicyReceiptAnchor
    contract. For hackathon demo / testing the receipt is returned in
    'pre-flight' form so the user can review before broadcasting.
    """
    payload = {
        "receipt_hash": receipt_hash,
        "decision": decision,
        "severity": severity,
        "agent_id": agent_id,
        "chain_id": ZGG_CHAIN_ID,
        "contract": ZGG_RECEIPT_CONTRACT,
        "rpc": ZGG_CHAIN_RPC,
        "status": "preflight",
        "note": "Set ZGG_RECEIPT_CONTRACT to a deployed PolicyReceiptAnchor address to enable live anchoring.",
    }
    return payload


def verify_anchor(receipt_hash: str, tx_hash: str | None = None) -> dict[str, Any]:
    """Verify that a receipt hash has been anchored on 0G Chain."""
    return {
        "receipt_hash": receipt_hash,
        "tx_hash": tx_hash,
        "verified": False,
        "note": "Verification requires a live RPC call to the PolicyReceiptAnchor contract.",
    }
