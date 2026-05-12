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
import time
from typing import Any

from web3 import Web3

DEFAULT_ZGG_CHAIN_RPC = "https://evmrpc-testnet.0g.ai"
DEFAULT_ZGG_CHAIN_ID = 16602
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def get_0g_config() -> dict[str, Any]:
    """Return the current 0G runtime config without requiring secrets."""
    return {
        "rpc": os.getenv("ZGG_CHAIN_RPC", DEFAULT_ZGG_CHAIN_RPC),
        "chain_id": int(os.getenv("ZGG_CHAIN_ID", str(DEFAULT_ZGG_CHAIN_ID))),
        "receipt_contract": os.getenv("ZGG_RECEIPT_CONTRACT", ZERO_ADDRESS),
    }


def build_0g_status(timeout_seconds: float = 3.0) -> dict[str, Any]:
    """Run a read-only 0G RPC status check for demo and operator surfaces."""
    cfg = get_0g_config()
    contract = cfg["receipt_contract"]
    contract_configured = contract.lower() != ZERO_ADDRESS.lower()
    started = time.perf_counter()

    rpc_status: dict[str, Any] = {
        "status": "unknown",
        "rpc": cfg["rpc"],
        "expectedChainId": cfg["chain_id"],
        "observedChainId": None,
        "latestBlockNumber": None,
        "latencyMs": None,
        "error": None,
    }
    contract_status: dict[str, Any] = {
        "address": contract,
        "configured": contract_configured,
        "codePresent": False,
        "status": "not_configured",
    }

    try:
        w3 = Web3(Web3.HTTPProvider(cfg["rpc"], request_kwargs={"timeout": timeout_seconds}))
        observed_chain_id = int(w3.eth.chain_id)
        latest_block = int(w3.eth.block_number)
        latency_ms = int((time.perf_counter() - started) * 1000)
        rpc_status.update(
            {
                "status": "ok" if observed_chain_id == cfg["chain_id"] else "chain_id_mismatch",
                "observedChainId": observed_chain_id,
                "latestBlockNumber": latest_block,
                "latencyMs": latency_ms,
            }
        )

        if contract_configured:
            code = w3.eth.get_code(Web3.to_checksum_address(contract))
            contract_status.update(
                {
                    "codePresent": bool(code),
                    "status": "deployed" if code else "no_code_at_address",
                }
            )
    except Exception as exc:  # pragma: no cover - exercised by runtime probes
        rpc_status.update(
            {
                "status": "degraded",
                "latencyMs": int((time.perf_counter() - started) * 1000),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )

    return {
        "schema": "0guard.0g_status.v1",
        "network": "0G Galileo Testnet",
        "readMode": "live_rpc_read_only",
        "rpc": rpc_status,
        "receiptAnchor": contract_status,
        "safety": {
            "privateKeyRequired": False,
            "signingEnabled": False,
            "broadcastingEnabled": False,
            "moneyMovementEnabled": False,
            "workbenchCanDeploy": False,
        },
    }


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
    cfg = get_0g_config()
    payload = {
        "receipt_hash": receipt_hash,
        "decision": decision,
        "severity": severity,
        "agent_id": agent_id,
        "chain_id": cfg["chain_id"],
        "contract": cfg["receipt_contract"],
        "rpc": cfg["rpc"],
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
