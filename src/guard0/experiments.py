"""Frontier experiment lab for next-step 0guard integrations.

This module turns research into safe product experiments. Every experiment is
read-only by default: it may call existing local preview builders, but it never
signs, broadcasts, uploads to 0G Storage, calls 0G Compute, sends Telegram
messages, posts to social, bridges, swaps, or places exchange orders.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from guard0.mira import build_mira_claim_preview
from guard0.native_preflight import build_native_preflight
from guard0.reputation import reputation_connector_manifest
from guard0.storage import store_threat_intel
from guard0.ton import build_ton_wallet_risk_preview

FRONTIER_EXPERIMENTS_SCHEMA = "0guard.frontier_experiments.v1"
FRONTIER_EXPERIMENT_PREVIEW_SCHEMA = "0guard.frontier_experiment_preview.v1"

DEFAULT_EVM_ADDRESS = "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab"
DEFAULT_TON_ADDRESS = "0:" + ("0" * 64)

_OFFICIAL_SOURCES: dict[str, str] = {
    "0g_storage_sdk": "https://docs.0g.ai/developer-hub/building-on-0g/storage/sdk",
    "0g_compute_inference": (
        "https://docs.0g.ai/developer-hub/building-on-0g/compute-network/inference"
    ),
    "goplus_docs": "https://docs.gopluslabs.io/",
    "chainabuse_get_reports": "https://docs.chainabuse.com/docs/get-reports-parameters",
    "forta_api": "https://docs.forta.network/en/latest/forta-api-reference/",
    "tenderly_docs": "https://docs.tenderly.co/",
    "blocksec_phalcon": "https://docs.blocksec.com/phalcon/phalcon-explorer/simulator",
    "telegram_mini_apps": (
        "https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app"
    ),
    "ton_center_v3": "https://docs.ton.org/ecosystem/api/toncenter/v3/overview",
    "ton_connect": "https://docs.ton.org/v3/guidelines/ton-connect/overview",
    "mira_verify": "https://verify.mira.network/",
}

_EXPERIMENTS: tuple[dict[str, Any], ...] = (
    {
        "rank": 1,
        "id": "zero_g_storage_receipt_readback",
        "name": "0G Storage receipt readback",
        "currentMode": "receipt_preview_no_live_upload",
        "whyItMatters": (
            "Makes 0G more than a screenshot by preparing the exact receipt payload that an "
            "operator can upload and read back once storage credentials and retention are approved."
        ),
        "safeBuildNow": "Generate canonical storage receipts for threat-intel payloads.",
        "activationStep": "Add an operator-only CLI that uploads, downloads with proof, and records the root hash.",
        "officialSources": [_OFFICIAL_SOURCES["0g_storage_sdk"]],
        "successMetrics": [
            "receipt_has_stable_root_hash",
            "upload_status_is_explicit",
            "readback_plan_names_operator_gate",
        ],
    },
    {
        "rank": 2,
        "id": "reputation_connector_shadow",
        "name": "GoPlus, Chainabuse, Forta reputation shadow mode",
        "currentMode": "connector_manifest_no_network_calls",
        "whyItMatters": (
            "Highest near-term lift for wallet, token, dApp, approval, domain, and Telegram alert quality."
        ),
        "safeBuildNow": "Rank applicable connectors and output only derived source-rights metadata.",
        "activationStep": "Enable one keyed connector behind terms review and derived-output tests.",
        "officialSources": [
            _OFFICIAL_SOURCES["goplus_docs"],
            _OFFICIAL_SOURCES["chainabuse_get_reports"],
            _OFFICIAL_SOURCES["forta_api"],
        ],
        "successMetrics": [
            "connector_applies_to_subject",
            "credential_boundary_visible",
            "raw_payloads_not_returned",
        ],
    },
    {
        "rank": 3,
        "id": "evm_simulation_delta_digest",
        "name": "Tenderly or BlockSec state-delta digest",
        "currentMode": "local_preflight_plus_synthetic_delta_no_provider_call",
        "whyItMatters": (
            "State deltas explain approvals, swaps, upgrades, and bridge-like messages in plain language."
        ),
        "safeBuildNow": "Convert intent/preflight output into a derived asset-delta schema without raw traces.",
        "activationStep": "Call one simulator with credentials, then persist only redacted deltas and hashes.",
        "officialSources": [
            _OFFICIAL_SOURCES["tenderly_docs"],
            _OFFICIAL_SOURCES["blocksec_phalcon"],
        ],
        "successMetrics": [
            "human_readable_asset_delta",
            "dangerous_call_detected",
            "provider_trace_not_stored",
        ],
    },
    {
        "rank": 4,
        "id": "telegram_ton_activity_passport",
        "name": "Telegram and TON risk passport",
        "currentMode": "syntax_policy_preview_no_indexer_call",
        "whyItMatters": (
            "Telegram is the natural first consumer surface; TON should be covered natively, not via bridge framing."
        ),
        "safeBuildNow": "Generate a TON wallet risk passport from syntax and intent policy only.",
        "activationStep": "Add TON Center or TONAPI read-only activity features behind rate-limit and privacy gates.",
        "officialSources": [
            _OFFICIAL_SOURCES["telegram_mini_apps"],
            _OFFICIAL_SOURCES["ton_center_v3"],
            _OFFICIAL_SOURCES["ton_connect"],
        ],
        "successMetrics": [
            "valid_ton_address_normalized",
            "telegram_identity_boundary_visible",
            "send_transaction_disabled",
        ],
    },
    {
        "rank": 5,
        "id": "zero_g_compute_shadow_score",
        "name": "0G Compute shadow anomaly score",
        "currentMode": "deterministic_local_score_no_inference_call",
        "whyItMatters": (
            "Prepares the 0G Compute story around model-assisted triage while keeping today's demo reproducible."
        ),
        "safeBuildNow": "Run a deterministic local feature score and expose the prompt envelope that 0G Compute would receive.",
        "activationStep": "Route the same redacted envelope through 0G Compute after provider funding and secret handling are approved.",
        "officialSources": [_OFFICIAL_SOURCES["0g_compute_inference"]],
        "successMetrics": [
            "prompt_envelope_redacted",
            "local_score_reproducible",
            "compute_secret_not_required",
        ],
    },
    {
        "rank": 6,
        "id": "mira_claim_verification_packet",
        "name": "Mira claim verification packet",
        "currentMode": "deterministic_claim_packet_no_external_call",
        "whyItMatters": (
            "Turns each guardrail into portable claims that can be externally verified without trusting the UI."
        ),
        "safeBuildNow": "Create a Mira-ready claim packet with evidence hashes and no external calls.",
        "activationStep": "Submit claims to Mira only after API/token terms are confirmed.",
        "officialSources": [_OFFICIAL_SOURCES["mira_verify"]],
        "successMetrics": [
            "claims_are_hash_backed",
            "external_mira_calls_false",
            "wallet_signatures_not_requested",
        ],
    },
)


def frontier_experiments() -> dict[str, Any]:
    """Return the ranked experiment backlog and safety posture."""
    experiments = [dict(item) for item in _EXPERIMENTS]
    return {
        "schema": FRONTIER_EXPERIMENTS_SCHEMA,
        "generatedAt": _now(),
        "mode": "frontier_lab_read_only",
        "thesis": (
            "0guard wins by owning the pre-wallet checkpoint for agents: receipts on 0G, "
            "reputation and simulation as evidence, Telegram/TON as the first consumer surface, "
            "and no bridge or custody dependency."
        ),
        "experimentCount": len(experiments),
        "recommendedSequence": [item["id"] for item in experiments],
        "experiments": experiments,
        "operatorBuyList": [
            "Stay on PhishDestroy, CryptoScamDB, and Forta labelled datasets until freshness or coverage proves insufficient.",
            "GoPlus or Chainabuse only after open-source sources cannot cover token, approval, or dApp safety needs.",
            "Tenderly or BlockSec only after reputation shadow mode is feeding product flows.",
            "Dune, Allium, Bitquery, or comparable feature stores only when native adapters are too slow.",
        ],
        "hardNoList": [
            "Do not bridge funds as an integration story.",
            "Do not expose raw paid-feed payloads.",
            "Do not let the public workbench sign, broadcast, send Telegram messages, or post socially.",
            "Do not claim 0G Storage or 0G Compute live calls unless a receipt/readback proves them.",
        ],
        "safety": _safety(),
    }


def run_frontier_experiment_preview(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a no-side-effect preview for one frontier experiment."""
    body = payload or {}
    if not isinstance(body, dict):
        raise ValueError("payload must be an object")
    experiment_id = str(body.get("experimentId") or body.get("id") or _EXPERIMENTS[0]["id"]).strip()
    spec = _experiment_by_id(experiment_id)
    subject = _subject(body)

    preview = _preview_for_experiment(spec["id"], subject)
    receipt_payload = {
        "schema": FRONTIER_EXPERIMENT_PREVIEW_SCHEMA,
        "experimentId": spec["id"],
        "previewHash": _hash_json(preview),
        "safety": _safety(),
    }
    return {
        "schema": FRONTIER_EXPERIMENT_PREVIEW_SCHEMA,
        "generatedAt": _now(),
        "mode": "no_side_effect_preview",
        "experiment": spec,
        "subject": _public_subject(subject),
        "decision": _decision(preview),
        "preview": preview,
        "receipt": {
            "hash": _hash_json(receipt_payload),
            "algorithm": "sha256_canonical_json",
            "zeroGStorageReady": True,
            "liveAnchorPerformed": False,
            "liveUploadPerformed": False,
        },
        "successMetrics": spec["successMetrics"],
        "nextOperatorStep": spec["activationStep"],
        "safety": _safety(),
    }


def _preview_for_experiment(experiment_id: str, subject: dict[str, Any]) -> dict[str, Any]:
    if experiment_id == "zero_g_storage_receipt_readback":
        return _storage_receipt_preview(subject)
    if experiment_id == "reputation_connector_shadow":
        return reputation_connector_manifest(
            {
                "url": subject["url"],
                "address": subject["evmAddress"],
                "chain": subject["chain"],
                "surface": "frontier_lab",
            }
        )
    if experiment_id == "evm_simulation_delta_digest":
        return _simulation_delta_preview(subject)
    if experiment_id == "telegram_ton_activity_passport":
        return build_ton_wallet_risk_preview(
            subject["tonAddress"],
            intent=subject["intent"],
            network="mainnet",
            live=False,
            include_activity=False,
        )
    if experiment_id == "zero_g_compute_shadow_score":
        return _compute_shadow_score(subject)
    if experiment_id == "mira_claim_verification_packet":
        return build_mira_claim_preview(
            subject={"project": "0guard", "experimentId": experiment_id},
            claims=[
                {
                    "id": "frontier_preview_is_read_only",
                    "claim": "This frontier experiment preview did not sign, send, upload, post, bridge, swap, or move funds.",
                    "evidenceSourceIds": ["0guard_runtime", "frontier_lab_receipt"],
                },
                {
                    "id": "risk_verdict_is_receipt_backed",
                    "claim": "The preview generated a deterministic receipt hash that can be anchored or uploaded after operator approval.",
                    "evidenceSourceIds": ["0g_storage_sdk", "0guard_runtime"],
                },
            ],
            evidence=[
                {
                    "sourceId": "0guard_frontier_lab",
                    "kind": "local_preview",
                    "url": "/api/experiments/run",
                    "subjectHash": _hash_json(_public_subject(subject)),
                }
            ],
        )
    raise ValueError(f"unsupported experiment: {experiment_id}")


def _storage_receipt_preview(subject: dict[str, Any]) -> dict[str, Any]:
    receipt = store_threat_intel(
        key="frontier-experiment-preview",
        data={
            "subjectHash": _hash_json(_public_subject(subject)),
            "intent": subject["intent"],
            "source": "0guard_frontier_lab",
        },
        tags=["frontier-lab", "0g-storage", "receipt-preview"],
    )
    return {
        "schema": "0guard.frontier_storage_receipt_preview.v1",
        "storageReceipt": receipt,
        "readbackPlan": {
            "operatorRequired": True,
            "uploadCommandStatus": "not_run_from_public_workbench",
            "downloadProofRequired": True,
            "publicOutput": "root_hash_tx_hash_size_and_redacted_payload_hash_only",
        },
        "safety": _safety(),
    }


def _simulation_delta_preview(subject: dict[str, Any]) -> dict[str, Any]:
    preflight = build_native_preflight(
        {
            "surface": "tenderly_simulation",
            "operation": "approve",
            "chain": subject["chain"],
            "to": subject["evmAddress"],
            "valueEth": "0",
            "intentText": subject["intentText"],
            "labels": ["approval preview", "potential drainer"],
            "liveSigning": False,
            "liveTransaction": False,
            "reputation": True,
            "url": subject["url"],
            "address": subject["evmAddress"],
        }
    )
    delta = {
        "assetDeltas": [
            {
                "asset": "ERC20",
                "direction": "approval",
                "humanSummary": "External simulator adapter would summarize allowance changes, not store a full trace.",
                "risk": "review_infinite_or_unbounded_approval",
            }
        ],
        "dangerousCalls": [
            {
                "id": "approval_or_upgrade_requires_review",
                "reason": "Approvals, upgrades, and bridge-like messages must pass policy and reputation before a signer appears.",
            }
        ],
        "providerCallsPerformed": False,
        "rawTraceStored": False,
        "traceHashOnly": _hash_json(
            {
                "preflightReceipt": preflight["receipt"]["hash"],
                "providerCallsPerformed": False,
            }
        ),
    }
    return {
        "schema": "0guard.frontier_simulation_delta_preview.v1",
        "preflight": preflight,
        "derivedDeltaDigest": delta,
        "safety": _safety(),
    }


def _compute_shadow_score(subject: dict[str, Any]) -> dict[str, Any]:
    envelope = {
        "task": "classify_pre_wallet_agent_intent",
        "modelInputs": {
            "intentTextHash": _hash_text(subject["intentText"]),
            "chain": subject["chain"],
            "domainHash": _hash_text(subject["url"]),
            "addressHash": _hash_text(subject["evmAddress"].lower()),
        },
        "redaction": "hashes_and_policy_features_only",
    }
    score_seed = _hash_json(envelope)
    score = int(score_seed[:8], 16) % 101
    verdict = "deny" if score >= 80 else "review" if score >= 45 else "allow"
    return {
        "schema": "0guard.frontier_compute_shadow_score.v1",
        "mode": "local_deterministic_no_0g_compute_call",
        "score": score,
        "verdict": verdict,
        "promptEnvelope": envelope,
        "providerFundingRequired": False,
        "computeSecretRequired": False,
        "liveInferencePerformed": False,
        "officialSource": _OFFICIAL_SOURCES["0g_compute_inference"],
        "safety": _safety(),
    }


def _decision(preview: dict[str, Any]) -> dict[str, Any]:
    if "decision" in preview and isinstance(preview["decision"], dict):
        decision = preview["decision"].get("decision") or preview["decision"].get("verdict")
        severity = preview["decision"].get("severity") or "medium"
        return {"decision": decision or "review", "severity": severity}
    if preview.get("verdict"):
        return {"decision": preview["verdict"], "severity": "medium"}
    if preview.get("storageReceipt", {}).get("stored") is False:
        return {"decision": "review", "severity": "medium"}
    return {"decision": "review", "severity": "medium"}


def _experiment_by_id(experiment_id: str) -> dict[str, Any]:
    for item in _EXPERIMENTS:
        if item["id"] == experiment_id:
            return dict(item)
    valid = ", ".join(item["id"] for item in _EXPERIMENTS)
    raise ValueError(f"unknown experimentId: {experiment_id}. valid values: {valid}")


def _subject(body: dict[str, Any]) -> dict[str, Any]:
    raw_subject = body.get("subject") if isinstance(body.get("subject"), dict) else {}
    intent = raw_subject.get("intent") if isinstance(raw_subject.get("intent"), dict) else {}
    intent_text = str(
        raw_subject.get("intentText")
        or body.get("intentText")
        or "Agent asks to approve an urgent wallet verification flow before claiming rewards."
    )
    return {
        "url": str(
            raw_subject.get("url")
            or body.get("url")
            or "https://docs.0g.ai.evil.example/claim"
        ),
        "evmAddress": str(raw_subject.get("evmAddress") or body.get("address") or DEFAULT_EVM_ADDRESS),
        "tonAddress": str(raw_subject.get("tonAddress") or body.get("tonAddress") or DEFAULT_TON_ADDRESS),
        "chain": str(raw_subject.get("chain") or body.get("chain") or "eip155:1"),
        "intentText": intent_text,
        "intent": {
            "action": intent.get("action") or "approve",
            "mode": intent.get("mode") or "preview",
            "requires_signature": bool(intent.get("requires_signature", True)),
            "prompt_text": intent.get("prompt_text") or intent_text,
        },
    }


def _public_subject(subject: dict[str, Any]) -> dict[str, Any]:
    return {
        "urlHash": _hash_text(subject["url"]),
        "evmAddressRedacted": _redact(subject["evmAddress"]),
        "tonAddressRedacted": _redact(subject["tonAddress"]),
        "chain": subject["chain"],
        "intentTextHash": _hash_text(subject["intentText"]),
    }


def _safety() -> dict[str, Any]:
    return {
        "readOnly": True,
        "networkCalls": False,
        "liveStorageUpload": False,
        "liveComputeInference": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "walletSignaturesRequested": False,
        "paymentSettlementEnabled": False,
        "exchangeOrdersEnabled": False,
        "bridgingEnabled": False,
        "moneyMovementEnabled": False,
        "rawPayloadsReturned": False,
    }


def _redact(value: str) -> str:
    if len(value) <= 16:
        return "***"
    return f"{value[:6]}...{value[-6:]}"


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
