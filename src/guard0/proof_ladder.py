"""0G proof ladder packets for judge, wallet, and operator readbacks.

This module does not upload to 0G Storage, publish DA blobs, call 0G Compute,
operate an Alignment Node, sign transactions, or broadcast anything. It turns a
candidate intent into a deterministic proof plan that shows exactly which 0G
native rails are ready and which steps still require an operator-approved live
path.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from guard0.chain import get_0g_config
from guard0.policy import evaluate_intent

PROOF_LADDER_SCHEMA = "0guard.0g_proof_ladder.v1"
ZGG_MAINNET_CHAIN_ID = 16661
ZGG_MAINNET_RPC = "https://evmrpc.0g.ai"
ZGG_EXPLORER = "https://chainscan.0g.ai"
ZGG_STORAGE_DOCS = "https://docs.0g.ai/developer-hub/building-on-0g/storage"
ZGG_DA_DOCS = "https://docs.0g.ai/developer-hub/building-on-0g/da"
ZGG_COMPUTE_DOCS = (
    "https://docs.0g.ai/developer-hub/building-on-0g/compute-network/inference"
)
ZGG_ALIGNMENT_DOCS = "https://docs.0g.ai/run-a-node/ai-alignment-node"
_HEX_SECRET_RE = re.compile(r"0x[a-fA-F0-9]{64}")


def build_proof_ladder(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a no-side-effect 0G proof ladder packet for one intent."""
    body = payload or {}
    if not isinstance(body, dict):
        raise ValueError("payload must be an object")

    intent = body.get("intent") if isinstance(body.get("intent"), dict) else body
    intent = intent if isinstance(intent, dict) else {}
    decision = evaluate_intent(intent).to_dict()
    stable_decision = {
        "decision": decision["decision"],
        "severity": decision["severity"],
        "action": decision["action"],
        "mode": decision["mode"],
        "blockers": decision["blockers"],
        "warnings": decision["warnings"],
        "receiptHash": decision["receipt_hash"],
    }
    request_summary = _request_summary(body, intent)
    canonical_packet = {
        "schema": PROOF_LADDER_SCHEMA,
        "requestSummary": request_summary,
        "decision": stable_decision,
    }

    chain_stage = _chain_receipt_stage(stable_decision, body)
    storage_stage = _storage_packet_stage(canonical_packet)
    da_stage = _da_stage(storage_stage)
    compute_stage = _compute_preview_stage(canonical_packet, storage_stage)
    alignment_stage = _alignment_stage(canonical_packet, chain_stage, storage_stage)
    stages = [chain_stage, storage_stage, da_stage, compute_stage, alignment_stage]

    return {
        "schema": PROOF_LADDER_SCHEMA,
        "generatedAt": _now(),
        "mode": "read_only_no_side_effects",
        "requestSummary": request_summary,
        "decision": stable_decision,
        "stageCount": len(stages),
        "stages": stages,
        "canonicalPacketHash": _hash_json(canonical_packet),
        "operatorNextStep": (
            "Promote one stage at a time from this packet: first chain receipt "
            "readback, then storage upload/readback, then DA availability, then "
            "compute inference, then alignment verification."
        ),
        "safety": _safety(),
        "rightsPolicy": {
            "rawPayloadsReturned": False,
            "sourceLinksOrHashesOnly": True,
            "paymentIsNotPermission": True,
        },
    }


def _chain_receipt_stage(decision: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    cfg = get_0g_config()
    configured_mainnet = body.get("mainnet") if isinstance(body.get("mainnet"), dict) else {}
    requested_chain = str(body.get("chain") or body.get("network") or "").strip()
    chain_id = (
        _chain_id_from_request(requested_chain)
        or int(configured_mainnet.get("chainId") or configured_mainnet.get("chain_id") or cfg["chain_id"])
    )
    rpc = str(configured_mainnet.get("rpc") or (ZGG_MAINNET_RPC if chain_id == ZGG_MAINNET_CHAIN_ID else cfg["rpc"]))
    network = "0G Mainnet" if chain_id == ZGG_MAINNET_CHAIN_ID else "0G Galileo Testnet"
    return {
        "id": "chainReceipt",
        "label": "0G Chain receipt",
        "status": "receipt_hash_ready",
        "network": network,
        "chainId": chain_id,
        "rpc": rpc,
        "explorer": ZGG_EXPLORER if chain_id == ZGG_MAINNET_CHAIN_ID else "",
        "receiptHash": decision["receiptHash"],
        "decision": decision["decision"],
        "severity": decision["severity"],
        "proofHash": _hash_json({"stage": "chainReceipt", **decision, "chainId": chain_id}),
        "readbackPerformed": False,
        "liveAnchorPerformed": False,
        "transactionSigningEnabled": False,
        "broadcastingEnabled": False,
    }


def _chain_id_from_request(value: str) -> int | None:
    normalized = value.lower().replace("_", "-")
    if normalized.startswith("eip155:"):
        try:
            return int(normalized.split(":", 1)[1])
        except ValueError:
            return None
    if normalized in {"0g-mainnet", "zero-g-mainnet", "zg-mainnet"}:
        return ZGG_MAINNET_CHAIN_ID
    if normalized.isdigit():
        return int(normalized)
    return None


def _storage_packet_stage(canonical_packet: dict[str, Any]) -> dict[str, Any]:
    root_hash = _hash_json({"stage": "storagePacket", "packet": canonical_packet})
    return {
        "id": "storagePacket",
        "label": "0G Storage packet",
        "status": "prepared_not_uploaded",
        "rootHash": root_hash,
        "packetHash": _hash_json(canonical_packet),
        "gateway": "https://storage.0g.ai",
        "docs": ZGG_STORAGE_DOCS,
        "liveUploadPerformed": False,
        "readbackPerformed": False,
        "rawPayloadReturned": False,
    }


def _da_stage(storage_stage: dict[str, Any]) -> dict[str, Any]:
    bundle = {
        "storageRootHash": storage_stage["rootHash"],
        "packetHash": storage_stage["packetHash"],
        "purpose": "0guard-verdict-availability",
    }
    return {
        "id": "daAvailability",
        "label": "0G DA availability packet",
        "status": "prepared_not_published",
        "bundleRoot": _hash_json(bundle),
        "docs": ZGG_DA_DOCS,
        "liveDAWritePerformed": False,
        "availabilityReadbackPerformed": False,
    }


def _compute_preview_stage(
    canonical_packet: dict[str, Any],
    storage_stage: dict[str, Any],
) -> dict[str, Any]:
    prompt_envelope = {
        "task": "explain_0guard_verdict",
        "decision": canonical_packet["decision"]["decision"],
        "severity": canonical_packet["decision"]["severity"],
        "storageRootHash": storage_stage["rootHash"],
        "style": "plain_english_then_technical",
    }
    return {
        "id": "computePreview",
        "label": "0G Compute explanation preview",
        "status": "deterministic_local_preview",
        "promptEnvelopeHash": _hash_json(prompt_envelope),
        "docs": ZGG_COMPUTE_DOCS,
        "liveInferencePerformed": False,
        "externalLlmCalls": False,
    }


def _alignment_stage(
    canonical_packet: dict[str, Any],
    chain_stage: dict[str, Any],
    storage_stage: dict[str, Any],
) -> dict[str, Any]:
    verifier = {
        "policy": "0guard-safety-posture",
        "chainProofHash": chain_stage["proofHash"],
        "storageRootHash": storage_stage["rootHash"],
        "requestSummary": canonical_packet["requestSummary"],
    }
    return {
        "id": "alignmentVerifier",
        "label": "0G Alignment verifier packet",
        "status": "verifier_ready_not_submitted",
        "verifierHash": _hash_json(verifier),
        "docs": ZGG_ALIGNMENT_DOCS,
        "alignmentNodeOperated": False,
        "externalVerifierCalls": False,
    }


def _request_summary(body: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    public_fields = {
        "surface": body.get("surface") or intent.get("surface") or "",
        "operation": body.get("operation") or intent.get("operation") or intent.get("action") or "",
        "chain": body.get("chain") or intent.get("chain") or intent.get("chain_id") or "",
        "mode": body.get("mode") or intent.get("mode") or "",
        "requiresSignature": bool(
            body.get("requires_signature") or intent.get("requires_signature") or intent.get("liveSigning")
        ),
        "targetHash": _hash_text(str(body.get("target") or intent.get("target_contract") or intent.get("to") or "")),
        "promptTextHash": _hash_text(str(intent.get("prompt_text") or intent.get("text") or "")),
    }
    return {
        "inputHash": _hash_json(_redact_secrets(body)),
        "rawPayloadReturned": False,
        "fields": public_fields,
    }


def _redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(term in lowered for term in ("secret", "private", "mnemonic", "seed", "token", "password", "key")):
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = _redact_secrets(item)
        return redacted
    if isinstance(value, list):
        return [_redact_secrets(item) for item in value]
    if isinstance(value, str):
        return _HEX_SECRET_RE.sub("0x***REDACTED_32_BYTE_HEX***", value)
    return value


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "networkCalls": False,
        "transactionSigningEnabled": False,
        "broadcastingEnabled": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "liveAnchorPerformed": False,
        "liveStorageUpload": False,
        "liveDAWritePerformed": False,
        "liveComputeInference": False,
        "alignmentNodeOperated": False,
        "paymentSettlementEnabled": False,
        "bridgingEnabled": False,
        "moneyMovementEnabled": False,
        "rawPayloadsReturned": False,
    }


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest() if value else ""


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
