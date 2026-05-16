"""Operational readiness summary for the 0guard service."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from guard0.chain import ZERO_ADDRESS, get_0g_config
from guard0.incident_data import detection_coverage, incident_summary
from guard0.reputation_shadow import build_reputation_shadow_cache

READINESS_SCHEMA = "0guard.readyz.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
MAINNET_PROOF_PATH = REPO_ROOT / "docs" / "hackathon-0g" / "mainnet-proof.json"


def production_readiness() -> dict[str, Any]:
    """Return an honest no-side-effect production-readiness profile."""
    cfg = get_0g_config()
    mainnet_proof = _load_mainnet_proof()
    summary = incident_summary()
    coverage = detection_coverage()
    shadow = build_reputation_shadow_cache()
    telegram_store = _telegram_store_detail()

    checks = [
        _check(
            "runtime_health",
            "ok",
            "Flask API can build health/readiness payloads without secrets.",
            {"service": "zg-hack-guard"},
        ),
        _check(
            "mainnet_verifier_profile",
            "ok" if _mainnet_runtime_configured(cfg, mainnet_proof) else "review",
            "0G mainnet verifier env should point at the proven receipt contract.",
            {
                "currentChainId": cfg["chain_id"],
                "currentRpc": cfg["rpc"],
                "receiptContractConfigured": cfg["receipt_contract"].lower()
                != ZERO_ADDRESS.lower(),
                "expectedChainId": mainnet_proof.get("chain_id"),
                "expectedRpc": mainnet_proof.get("rpc"),
                "expectedReceiptContract": mainnet_proof.get("contract_address"),
            },
        ),
        _check(
            "mainnet_proof_file",
            "ok" if mainnet_proof.get("readback", {}).get("verified") else "review",
            "Repository includes a public 0G mainnet deploy and receipt-readback proof.",
            {
                "path": "docs/hackathon-0g/mainnet-proof.json",
                "anchorVerified": bool(mainnet_proof.get("readback", {}).get("verified")),
                "anchorTxHash": mainnet_proof.get("anchor_tx_hash", ""),
                "contractAddress": mainnet_proof.get("contract_address", ""),
            },
        ),
        _check(
            "incident_dataset",
            "ok" if (summary.get("meta") or {}).get("total_incidents") else "review",
            "Incident corpus is loaded and source-linked for detector coverage.",
            {
                "incidentCount": (summary.get("meta") or {}).get("total_incidents"),
                "datasetFingerprint": coverage.get("datasetFingerprint"),
            },
        ),
        _check(
            "detector_coverage",
            "ok" if coverage.get("coverageRatio") == 1.0 else "review",
            "Detector seeds cover the validated incident set used by the public proof page.",
            {
                "coveredCount": coverage.get("coveredCount"),
                "incidentCount": coverage.get("incidentCount"),
                "coverageRatio": coverage.get("coverageRatio"),
            },
        ),
        _check(
            "reputation_shadow_cache",
            "ok" if shadow.get("sourceCount", 0) >= 3 else "review",
            "Derived reputation cache composes reviewed payloads without live fetches or raw resale.",
            {
                "schema": shadow.get("schema"),
                "sourceCount": shadow.get("sourceCount"),
                "derivedSignalCount": shadow.get("derivedSignalCount"),
                "decision": (shadow.get("probePreview") or {}).get("decision", {}).get("decision"),
                "rawPayloadsReturned": shadow.get("sourceRights", {}).get("rawPayloadsReturned"),
            },
        ),
        _check(
            "telegram_state_store",
            "ok" if telegram_store["persistentStoreConfigured"] else "review",
            "Telegram opt-in state can persist when TELEGRAM_OPT_IN_STORE_PATH is configured.",
            {
                **telegram_store,
                "outboundSendsEnabled": False,
                "operatorNextStep": (
                    "set TELEGRAM_OPT_IN_STORE_PATH to a private JSON file or wire Firestore/Cloud SQL"
                    if not telegram_store["persistentStoreConfigured"]
                    else "promote this file-backed store only for low-volume previews; use Firestore/Cloud SQL for scale"
                ),
            },
        ),
        _check(
            "external_actions",
            "ok",
            "Workbench cannot sign, broadcast, settle, send, post, bridge, swap, or move funds.",
            _safety(),
        ),
    ]
    review_count = sum(1 for check in checks if check["status"] == "review")
    return {
        "schema": READINESS_SCHEMA,
        "generatedAt": _now(),
        "mode": "operational_readiness_no_side_effects",
        "ok": review_count == 0,
        "readiness": "production_review" if review_count else "production_ready",
        "reviewCount": review_count,
        "checks": checks,
        "operatorPromotions": [
            {
                "rank": 1,
                "id": "configure_mainnet_runtime_env",
                "why": "Align fresh runtimes with the already proven 0G mainnet contract.",
                "env": {
                    "ZGG_CHAIN_RPC": mainnet_proof.get("rpc") or "https://evmrpc.0g.ai",
                    "ZGG_CHAIN_ID": str(mainnet_proof.get("chain_id") or 16661),
                    "ZGG_RECEIPT_CONTRACT": mainnet_proof.get("contract_address") or "",
                },
                "requiresSecret": False,
            },
            {
                "rank": 2,
                "id": "persistent_telegram_opt_in_store",
                "why": "Makes wallet-alert subscriptions survive deploy restarts without enabling outbound sends.",
                "suggestedOptions": ["Firestore", "SQLite volume", "Cloud SQL"],
                "requiresSecret": True,
            },
            {
                "rank": 3,
                "id": "first_reviewed_connector_worker",
                "why": "Refresh the shadow cache from one reviewed source before claiming continuous live protection.",
                "suggestedFirstSources": [
                    "phishdestroy_destroylist",
                    "cryptoscamdb",
                    "forta_labelled_datasets",
                ],
                "requiresSecret": False,
            },
        ],
        "safety": _safety(),
    }


def _mainnet_runtime_configured(cfg: dict[str, Any], proof: dict[str, Any]) -> bool:
    return (
        cfg["chain_id"] == proof.get("chain_id")
        and cfg["rpc"] == proof.get("rpc")
        and cfg["receipt_contract"].lower() == str(proof.get("contract_address", "")).lower()
    )


def _load_mainnet_proof() -> dict[str, Any]:
    try:
        return json.loads(MAINNET_PROOF_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _telegram_store_detail() -> dict[str, Any]:
    raw_path = os.getenv("TELEGRAM_OPT_IN_STORE_PATH", "").strip()
    raw_url = os.getenv("TELEGRAM_OPT_IN_STORE_URL", "").strip()
    file_url_configured = raw_url.startswith("file://")
    persistent = bool(raw_path or file_url_configured)
    if persistent:
        mode = "local_json"
    elif raw_url:
        mode = "external_adapter_pending"
    else:
        mode = "in_memory"
    return {
        "persistentStoreConfigured": persistent,
        "storeMode": mode,
        "externalStoreConfigured": bool(raw_url and not file_url_configured),
        "secretDisplayEnabled": False,
        "networkCalls": False,
    }


def _check(check_id: str, status: str, summary: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "summary": summary,
        "detail": detail,
    }


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "networkCalls": False,
        "liveConnectorFetch": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "paymentSettlementEnabled": False,
        "exchangeOrdersEnabled": False,
        "bridgingEnabled": False,
        "moneyMovementEnabled": False,
        "secretDisplayEnabled": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
