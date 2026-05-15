"""
0G Storage Integration — Threat Intel Persistence Layer
========================================================
0G Storage provides ultra-low-cost decentralized storage with a dual-layer
architecture (Log archival + KV query). This module persists hack signatures,
IOCs, and policy receipts to 0G so they are censorship-resistant and
federated across agent instances.

Docs: https://docs.0g.ai/build-with-0g/storage
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any


ZGS_NODE_URL = os.getenv("ZGS_NODE_URL", "https://storage.0g.ai")
ZGS_INDEXER_URL = os.getenv("ZGS_INDEXER_URL", "https://indexer.0g.ai")


def _serialize(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def store_threat_intel(
    key: str,
    data: dict[str, Any],
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Prepare a threat-intel receipt for 0G Storage without uploading it."""
    payload = {
        "version": "zg-hack-guard/0.1.0",
        "timestamp": time.time(),
        "key": key,
        "tags": tags or [],
        "data": data,
    }
    blob = _serialize(payload)
    root_hash = hashlib.sha256(blob).hexdigest()

    # In a production deployment this would POST to the 0G Storage KV gateway.
    # The local/hackathon path is deliberately honest: it prepares the canonical
    # root hash but does not claim that a live 0G upload happened.
    receipt = {
        "stored": False,
        "storage_mode": "receipt_only_no_live_upload",
        "upload_enabled": False,
        "root_hash": root_hash,
        "size_bytes": len(blob),
        "zgs_node": ZGS_NODE_URL,
        "key": key,
        "note": (
            "Receipt root prepared for 0G Storage. No live upload was performed by this code path."
        ),
    }
    return receipt


def fetch_threat_intel(key: str) -> dict[str, Any] | None:
    """
    Fetch a threat-intel record by key from 0G Storage.
    Returns None if not found or if live fetch is not configured.
    """
    # Live fetch stub — replace with actual KV read via 0G indexer when credentials
    # and key-schema are finalized.
    return None


def batch_store_signatures(signatures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Bulk-persist hack signatures (useful for seeding fresh IOCs after an incident)."""
    receipts = []
    for sig in signatures:
        key = sig.get("id") or hashlib.sha256(_serialize(sig)).hexdigest()[:16]
        receipts.append(store_threat_intel(key=key, data=sig, tags=["signature", "april-2026"]))
    return receipts
