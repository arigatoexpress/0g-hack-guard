"""Read-only TON and Telegram wallet risk previews for 0guard.

The TON lane is intentionally not an execution adapter. It validates address
syntax, exposes a TON Connect manifest, and prepares a risk passport that can be
shown inside the Telegram Mini App without requesting signatures, tonProof, or
transactions.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

TON_STATUS_SCHEMA = "0guard.ton_status.v1"
TON_RISK_RULES_SCHEMA = "0guard.ton_risk_rules.v1"
TON_WALLET_RISK_PREVIEW_SCHEMA = "0guard.ton_wallet_risk_preview.v1"
TONCONNECT_MANIFEST_SCHEMA = "0guard.tonconnect_manifest.v1"
TON_RULESET_VERSION = "ton-risk-passport-2026-05-15"

TON_OFFICIAL_SOURCES = [
    "https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app",
    "https://core.telegram.org/bots/blockchain-guidelines",
    "https://docs.ton.org/v3/guidelines/ton-connect/overview",
    "https://docs.ton.org/v3/guidelines/ton-connect/creating-manifest",
    "https://docs.ton.org/ecosystem/api/toncenter/v3/overview",
]

_RAW_TON_ADDRESS = re.compile(r"^-?(?:0|1):[0-9a-fA-F]{64}$")
_FRIENDLY_TON_ADDRESS = re.compile(r"^[A-Za-z0-9_-]{48}$")


TON_RISK_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "ton_untrusted_payload_or_comment",
        "name": "High-risk TON comment or payload language",
        "severity": "high",
        "signalType": "intent_text",
        "description": (
            "Flags TON wallet flows that ask users to urgently claim rewards, verify a wallet, "
            "or reveal recovery material inside a Telegram context."
        ),
        "sourceIds": ["telegram_webapps_docs", "ton_connect_docs", "0guard_policy_engine"],
    },
    {
        "id": "ton_live_activity_not_checked",
        "name": "No live TON activity readback",
        "severity": "medium",
        "signalType": "source_coverage",
        "description": (
            "Default previews avoid network calls. The passport stays in review until a TON "
            "indexer adapter is explicitly enabled."
        ),
        "sourceIds": ["toncenter_v3_docs", "0guard_source_rights"],
    },
    {
        "id": "ton_spam_asset_watchlist",
        "name": "Jetton/NFT spam and airdrop watchlist",
        "severity": "medium",
        "signalType": "future_indexer_signal",
        "description": (
            "Planned read-only TON Center or TONAPI enrichment for suspicious Jetton and NFT "
            "inbound patterns common in Telegram phishing."
        ),
        "sourceIds": ["toncenter_v3_docs", "chainabuse", "openphish"],
    },
    {
        "id": "ton_bounced_message_cluster",
        "name": "Bounced or failed message cluster",
        "severity": "medium",
        "signalType": "future_indexer_signal",
        "description": (
            "Planned activity feature for wallets interacting with contracts that repeatedly "
            "bounce or fail TON messages."
        ),
        "sourceIds": ["toncenter_v3_docs"],
    },
    {
        "id": "ton_connect_no_signing_boundary",
        "name": "TON Connect is presentation-only in 0guard",
        "severity": "info",
        "signalType": "safety_boundary",
        "description": (
            "0guard can display a manifest and accept a pasted/connected address, but it does "
            "not call sendTransaction, signData, or tonProof in this repo slice."
        ),
        "sourceIds": ["ton_connect_docs", "telegram_blockchain_guidelines"],
    },
)


def tonconnect_manifest(base_url: str) -> dict[str, Any]:
    """Return a TON Connect manifest payload for wallet UIs."""
    root = base_url.rstrip("/")
    return {
        "url": root,
        "name": "0guard",
        "iconUrl": f"{root}/static/0guard-logo.png",
        "termsOfUseUrl": f"{root}/docs/hackathon-0g/",
        "privacyPolicyUrl": f"{root}/docs/hackathon-0g/",
        "schema": TONCONNECT_MANIFEST_SCHEMA,
        "safety": _ton_safety(),
    }


def ton_status() -> dict[str, Any]:
    """Return TON integration posture without making network calls."""
    return {
        "schema": TON_STATUS_SCHEMA,
        "generatedAt": _now(),
        "mode": "telegram_ton_read_only_preview",
        "tonConnect": {
            "manifestPath": "/tonconnect-manifest.json",
            "manifestReady": True,
            "sendTransactionEnabled": False,
            "signDataEnabled": False,
            "tonProofRequested": False,
            "walletConnectionRequiredForPreview": False,
        },
        "indexers": {
            "tonCenterApiBase": os.getenv("TONCENTER_API_BASE", "https://toncenter.com/api/v3"),
            "tonCenterApiKeyConfigured": bool(os.getenv("TONCENTER_API_KEY")),
            "tonApiKeyConfigured": bool(os.getenv("TONAPI_KEY")),
            "networkCallsDefault": False,
        },
        "supportedNetworks": ["mainnet", "testnet"],
        "riskRulesVersion": TON_RULESET_VERSION,
        "officialSources": TON_OFFICIAL_SOURCES,
        "safety": _ton_safety(),
    }


def ton_risk_rules() -> dict[str, Any]:
    """Return source-cited TON risk rules used by the preview passport."""
    return {
        "schema": TON_RISK_RULES_SCHEMA,
        "generatedAt": _now(),
        "rulesVersion": TON_RULESET_VERSION,
        "ruleCount": len(TON_RISK_RULES),
        "rules": list(TON_RISK_RULES),
        "safety": _ton_safety(),
    }


def build_ton_wallet_risk_preview(
    address: str,
    *,
    intent: dict[str, Any] | None = None,
    network: str = "mainnet",
    live: bool = False,
    include_activity: bool = False,
) -> dict[str, Any]:
    """Build a deterministic TON risk passport without signing or broadcasting."""
    normalized, address_format = normalize_ton_address(address)
    network = _normalize_network(network)
    intent = intent or {}
    intent_text = _intent_text(intent)
    risk_signals = _ton_risk_signals(intent_text, live=live, include_activity=include_activity)
    decision = _decision_from_signals(risk_signals)
    address_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    receipt_payload = {
        "schema": TON_WALLET_RISK_PREVIEW_SCHEMA,
        "addressHash": address_hash,
        "network": network,
        "decision": decision,
        "signals": risk_signals,
        "rulesVersion": TON_RULESET_VERSION,
    }
    receipt_hash = hashlib.sha256(_serialize(receipt_payload)).hexdigest()
    evidence = [
        {
            "sourceId": "ton_connect_docs",
            "kind": "protocol_contract",
            "url": "https://docs.ton.org/v3/guidelines/ton-connect/overview",
            "claim": "TON Connect is the standard wallet connection layer for TON apps.",
        },
        {
            "sourceId": "telegram_webapps_docs",
            "kind": "auth_contract",
            "url": "https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app",
            "claim": "Telegram Mini App initData must be validated server-side before trusting user identity.",
        },
        {
            "sourceId": "toncenter_v3_docs",
            "kind": "future_indexer",
            "url": "https://docs.ton.org/ecosystem/api/toncenter/v3/overview",
            "claim": "TON Center v3 is the planned read-only indexed activity adapter.",
        },
    ]
    return {
        "schema": TON_WALLET_RISK_PREVIEW_SCHEMA,
        "generatedAt": _now(),
        "mode": "preview_no_sign_no_send",
        "network": network,
        "address": {
            "redacted": _redact_address(normalized),
            "hash": address_hash,
            "format": address_format,
            "validationMode": "syntax_only",
        },
        "decision": decision,
        "riskSignals": risk_signals,
        "evidence": evidence,
        "miraClaims": [
            {
                "id": "ton_preview_is_read_only",
                "claim": "This TON passport did not request a wallet signature or transaction.",
                "evidenceSourceIds": ["ton_connect_docs", "0guard_runtime"],
            },
            {
                "id": "telegram_identity_requires_server_validation",
                "claim": "Telegram user identity is only trusted after raw initData validation.",
                "evidenceSourceIds": ["telegram_webapps_docs", "0guard_runtime"],
            },
            {
                "id": "ton_activity_enrichment_is_not_live_by_default",
                "claim": "TON account activity is not fetched unless an operator enables read-only indexer probes.",
                "evidenceSourceIds": ["toncenter_v3_docs", "0guard_source_rights"],
            },
        ],
        "receipt": {
            "hash": receipt_hash,
            "algorithm": "sha256_canonical_json",
            "zeroGStorageReady": True,
            "liveUploadPerformed": False,
            "storageMode": "receipt_only_no_live_upload",
        },
        "safety": _ton_safety(live=live),
    }


def normalize_ton_address(address: str) -> tuple[str, str]:
    """Validate enough TON syntax to prevent obviously bad Mini App input."""
    value = str(address or "").strip()
    if not value:
        raise ValueError("TON address is required")
    if _RAW_TON_ADDRESS.fullmatch(value):
        return value.lower(), "raw_workchain_hex"
    if _FRIENDLY_TON_ADDRESS.fullmatch(value):
        return value, "friendly_base64url"
    raise ValueError("TON address must be a friendly 48-character address or raw workchain:hex address")


def _ton_risk_signals(
    intent_text: str,
    *,
    live: bool,
    include_activity: bool,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    high_risk_terms = (
        "seed phrase",
        "private key",
        "recovery phrase",
        "urgent claim",
        "wallet verification",
        "airdrop claim",
        "free nft",
        "connect wallet to verify",
    )
    matched_terms = [term for term in high_risk_terms if term in intent_text.lower()]
    if matched_terms:
        signals.append(
            {
                "ruleId": "ton_untrusted_payload_or_comment",
                "severity": "high",
                "signal": "high_risk_telegram_wallet_language",
                "matchedTerms": matched_terms[:5],
                "recommendation": "Block or require explicit human review before opening any TON wallet prompt.",
            }
        )
    if not live or not include_activity:
        signals.append(
            {
                "ruleId": "ton_live_activity_not_checked",
                "severity": "medium",
                "signal": "no_live_indexer_activity",
                "recommendation": "Treat this as a syntax-and-policy passport until TON indexer readbacks are enabled.",
            }
        )
    signals.append(
        {
            "ruleId": "ton_connect_no_signing_boundary",
            "severity": "info",
            "signal": "read_only_ton_connect_boundary",
            "recommendation": "Show the passport before any separate wallet app requests a transaction.",
        }
    )
    return signals


def _decision_from_signals(signals: list[dict[str, Any]]) -> dict[str, Any]:
    severities = {signal["severity"] for signal in signals}
    if "high" in severities:
        verdict = "deny"
        severity = "high"
    elif "medium" in severities:
        verdict = "review"
        severity = "medium"
    else:
        verdict = "allow"
        severity = "low"
    reasons = [signal["recommendation"] for signal in signals if signal.get("recommendation")]
    return {
        "decision": verdict,
        "severity": severity,
        "reasons": reasons,
        "rulesVersion": TON_RULESET_VERSION,
    }


def _normalize_network(network: str) -> str:
    value = str(network or "mainnet").strip().lower()
    if value not in {"mainnet", "testnet"}:
        raise ValueError("TON network must be mainnet or testnet")
    return value


def _intent_text(intent: dict[str, Any]) -> str:
    return json.dumps(intent, sort_keys=True, default=str)


def _redact_address(address: str) -> str:
    if len(address) <= 16:
        return "***"
    return f"{address[:6]}...{address[-6:]}"


def _serialize(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _ton_safety(*, live: bool = False) -> dict[str, Any]:
    return {
        "readOnly": True,
        "networkCalls": bool(live),
        "networkCallsDefault": False,
        "telegramSendsEnabled": False,
        "walletSignaturesRequested": False,
        "sendTransactionEnabled": False,
        "signDataEnabled": False,
        "tonProofRequested": False,
        "bridgingEnabled": False,
        "moneyMovementEnabled": False,
        "rawPayloadsReturned": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
