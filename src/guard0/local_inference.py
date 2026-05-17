"""Read-only local inference, x402 data-product, and backfill plans."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

LOCAL_INFERENCE_SCHEMA = "0guard.local_inference_mesh.v1"
TELEGRAM_LOCAL_INFERENCE_PREVIEW_SCHEMA = "0guard.telegram_local_inference_preview.v1"
X402_DATA_PRODUCTS_SCHEMA = "0guard.x402_data_products.v1"
BACKFILL_PLAN_SCHEMA = "0guard.historical_backfill_plan.v1"

DEFAULT_WINDOWS_OLLAMA_URL = "http://192.168.1.61:11434"
DEFAULT_RVPI_A_HEALTH_URL = "http://192.168.1.111:8765/health"
DEFAULT_RVPI_B_OLLAMA_URL = "http://10.77.4.12:11434"

X402_DOC_URL = "https://docs.cdp.coinbase.com/x402/welcome"
X402_NETWORK_URL = "https://docs.cdp.coinbase.com/x402/network-support"
X402_BAZAAR_URL = "https://docs.cdp.coinbase.com/x402/bazaar"
X402_SITE_URL = "https://www.x402.org/"

HttpGet = Callable[..., Any]


def build_local_inference_mesh(
    *,
    live: bool = False,
    timeout_seconds: float = 3.0,
    http_get: HttpGet | None = None,
) -> dict[str, Any]:
    """Return the local inference mesh posture without executing prompts."""

    getter = http_get or requests.get
    windows_url = os.getenv("ZG_WINDOWS_OLLAMA_URL", DEFAULT_WINDOWS_OLLAMA_URL).rstrip("/")
    rvpi_a_url = os.getenv("ZG_RVPI_A_EDGE_HEALTH_URL", DEFAULT_RVPI_A_HEALTH_URL)
    rvpi_b_url = os.getenv("ZG_RVPI_B_OLLAMA_URL", DEFAULT_RVPI_B_OLLAMA_URL).rstrip("/")

    nodes = [
        _ollama_node(
            node_id="windows_ollama",
            label="Windows 12-core local model host",
            url=windows_url,
            role="heavy_local_inference_candidate",
            live=live,
            timeout_seconds=timeout_seconds,
            http_get=getter,
            currentObservation=(
                "LAN reachable on 2026-05-17, but `/api/tags` returned an empty model list."
            ),
        ),
        _edge_health_node(
            node_id="rvpi_a_edge",
            label="rvpi-a edge sentinel",
            url=rvpi_a_url,
            role="sentinel_probe_and_evidence_cache",
            live=live,
            timeout_seconds=timeout_seconds,
            http_get=getter,
            currentObservation=(
                "LAN health endpoint was reachable on 2026-05-17 with telemetry-only safety."
            ),
        ),
        _ollama_node(
            node_id="rvpi_b_ollama_candidate",
            label="rvpi-b Ethernet peer",
            url=rvpi_b_url,
            role="small_filter_or_cache_candidate",
            live=live,
            timeout_seconds=timeout_seconds,
            http_get=getter,
            currentObservation=(
                "SSH over the Pi-to-Pi Ethernet link is reachable, but Ollama is not exposed yet."
            ),
        ),
        {
            "id": "0g_private_computer_router",
            "label": "0G Private Computer / 0GM router",
            "role": "attested_external_inference_for_sensitive_summaries",
            "status": "manifest_only_operator_funded",
            "promptExecutionEnabled": False,
            "paidInferenceEnabled": False,
            "requires": [
                "server-side Router API key",
                "operator-reviewed 0G compute balance",
                "prompt minimization and secret scrub",
            ],
        },
    ]

    blockers = _mesh_blockers(nodes)
    return {
        "schema": LOCAL_INFERENCE_SCHEMA,
        "generatedAt": _now(),
        "mode": "live_read_only_probe_no_prompts" if live else "configured_mesh_no_network",
        "live": live,
        "summary": {
            "readyForTelegramBackend": not blockers,
            "reachableNodes": sum(1 for node in nodes if node.get("reachable") is True),
            "modelServingNodes": sum(1 for node in nodes if node.get("modelNames")),
            "promptExecutionEnabled": False,
            "telegramSendsEnabled": False,
        },
        "nodes": nodes,
        "routingPlan": [
            {
                "intent": "telegram_status_question",
                "primary": "deterministic_zero_guard_status",
                "fallback": "windows_ollama_after_model_loaded",
                "allowedOutputs": ["status_summary", "operator_next_steps"],
            },
            {
                "intent": "node_log_digest",
                "primary": "rvpi_a_edge_snapshot_plus_windows_ollama_summary",
                "fallback": "0g_private_computer_router_after_operator_funding",
                "allowedOutputs": ["digest", "blocker_list", "proof_links"],
            },
            {
                "intent": "policy_or_money_movement",
                "primary": "deterministic_guardrails_only",
                "fallback": None,
                "allowedOutputs": ["allow_review_deny", "human_confirmation_required"],
            },
        ],
        "telegramBridge": {
            "route": "/api/telegram/local-inference-preview",
            "delivery": "preview_no_send",
            "liveBotSendEnabled": False,
            "commandPlan": [
                "/zg systems - summarize Windows, Pi, 0G, and Telegram readiness",
                "/zg node - return storage/DA status without keys",
                "/zg risk <address-or-url> - run deterministic checks before any model text",
            ],
        },
        "operatorNext": [
            "Load one small local model on the Windows Ollama host before routing prompts there.",
            "Install or expose the rvpi-b sentinel runtime after identity is verified.",
            "Keep Telegram command handling read-only until opt-in persistence and rate limits are reviewed.",
            "Use 0G Private Computer for sensitive explanation only after a server-side API key exists.",
        ],
        "safety": _safety(live_network_calls=live),
    }


def build_telegram_local_inference_preview(
    mesh: dict[str, Any] | None = None,
    *,
    opt_in_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Telegram-safe digest preview for local inference readiness."""

    mesh_status = mesh or build_local_inference_mesh(live=False)
    nodes = mesh_status.get("nodes") or []
    node_lines = [
        f"- {node.get('label')}: {node.get('status')}"
        for node in nodes
        if node.get("id") != "0g_private_computer_router"
    ]
    blockers = mesh_status.get("operatorNext") or []
    message = "\n".join(
        [
            "ZeroGuard local systems preview",
            f"Mode: {mesh_status.get('mode')}",
            f"Model-serving nodes: {(mesh_status.get('summary') or {}).get('modelServingNodes', 0)}",
            *node_lines[:4],
            "Delivery: preview only; no Telegram send, no prompt execution.",
        ]
    )
    return {
        "schema": TELEGRAM_LOCAL_INFERENCE_PREVIEW_SCHEMA,
        "generatedAt": _now(),
        "delivery": "preview_no_send",
        "telegram_send": False,
        "optInRecord": _public_opt_in(opt_in_record),
        "message": message,
        "mesh": {
            "schema": mesh_status.get("schema"),
            "mode": mesh_status.get("mode"),
            "summary": mesh_status.get("summary"),
            "blockers": blockers,
        },
        "safety": _safety(live_network_calls=bool(mesh_status.get("live"))),
    }


def build_x402_data_products() -> dict[str, Any]:
    """Return the rights-cleared x402 product map for ZeroGuard data streams."""

    products = [
        {
            "id": "wallet_preflight_verdict",
            "priceHint": "0.01-0.05 USDC per check after testnet proof",
            "resourcePath": "/x402/v1/wallet-preflight",
            "value": "A normalized allow/review/deny packet for a wallet or agent action.",
            "inputs": ["intent", "chain", "address_or_calldata", "source_context"],
            "sellableOutput": ["verdict", "receipt_hash", "source_ids", "human_summary"],
            "rawPayloadResaleAllowed": False,
        },
        {
            "id": "threat_packet_summary",
            "priceHint": "0.10-0.50 USDC per enriched packet",
            "resourcePath": "/x402/v1/threat-packet",
            "value": "A source-cited incident, reputation, and policy explanation for agent UIs.",
            "inputs": ["domain", "address", "tx_preview", "public_source_ids"],
            "sellableOutput": ["risk_factors", "matched_incidents", "links", "hashes"],
            "rawPayloadResaleAllowed": False,
        },
        {
            "id": "node_health_snapshot",
            "priceHint": "0.05-0.25 USDC per operator snapshot",
            "resourcePath": "/x402/v1/node-health",
            "value": "0G node sync, peer, and blocker summaries for opted-in operators.",
            "inputs": ["node_public_id", "snapshot_scope"],
            "sellableOutput": ["sync_gap", "peer_count", "readiness", "proof_links"],
            "rawPayloadResaleAllowed": False,
        },
        {
            "id": "reputation_shadow_digest",
            "priceHint": "subscription candidate",
            "resourcePath": "/x402/v1/reputation-shadow",
            "value": "Dedupe-friendly derived reputation features for wallets and Telegram bots.",
            "inputs": ["domain", "wallet", "token", "source_mix"],
            "sellableOutput": ["features", "confidence", "source_ids", "cooldown_state"],
            "rawPayloadResaleAllowed": False,
        },
        {
            "id": "historical_incident_features",
            "priceHint": "bundle or research artifact",
            "resourcePath": "/x402/v1/incident-features",
            "value": "Backfilled exploit-pattern features that help agents avoid known failure modes.",
            "inputs": ["time_window", "chain", "category"],
            "sellableOutput": ["feature_counts", "detector_ids", "source_links", "fingerprints"],
            "rawPayloadResaleAllowed": False,
        },
    ]
    return {
        "schema": X402_DATA_PRODUCTS_SCHEMA,
        "generatedAt": _now(),
        "mode": "product_manifest_no_settlement",
        "protocolPosture": {
            "paymentRequiredStatus": 402,
            "usesHttpHeaders": True,
            "supportedNetworksToPrepare": [
                {"network": "Base", "caip2": "eip155:8453"},
                {"network": "Base Sepolia", "caip2": "eip155:84532"},
                {"network": "Arbitrum One", "caip2": "eip155:42161"},
                {"network": "Polygon", "caip2": "eip155:137"},
            ],
            "initialSettlement": "disabled_until_operator_keys_and_testnet_flow_exist",
            "facilitator": "CDP or x402.org testnet after review",
        },
        "products": products,
        "qualityGates": [
            "Every paid response must include data provenance, schema version, and receipt hash.",
            "Payment unlocks derived analysis only; it does not grant raw upstream feed resale rights.",
            "MetaMask Smart Accounts / ERC-7710 can scope recurring x402 access later.",
            "1Shot API can be a demo facilitator path only after credentials and spend limits are set.",
            "Arbitrum One is a natural mainnet payment lane; use testnet or sandbox first.",
        ],
        "implementationSteps": [
            "Add dry-run 402 response metadata for one route without accepting payments.",
            "Add x402 client tests with fixture payment headers and no settlement.",
            "Add a signed capability policy for Smart Account or Advanced Permission demos.",
            "Move to testnet facilitator only after route schemas and spend limits are frozen.",
        ],
        "sources": [X402_DOC_URL, X402_NETWORK_URL, X402_BAZAAR_URL, X402_SITE_URL],
        "safety": _safety(live_network_calls=False),
    }


def build_historical_backfill_plan() -> dict[str, Any]:
    """Return the historical data plan for durable, provenance-rich ZeroGuard features."""

    return {
        "schema": BACKFILL_PLAN_SCHEMA,
        "generatedAt": _now(),
        "mode": "backfill_plan_no_fetch",
        "storage": {
            "nearTerm": "append-only JSONL under data/backfill/ plus fingerprints in content/",
            "scalePath": "DuckDB or SQLite feature store with source manifests and immutable run ids",
            "zeroGPath": "store public-safe derived bundles on 0G Storage after upload/readback is operator-approved",
            "privateDataPolicy": "never store private keys, mnemonics, raw chats, or paid-feed dumps",
        },
        "recordSchema": {
            "event_id": "stable source id or sha256 of canonical public evidence",
            "observed_at": "ISO-8601 timestamp",
            "chain": "EVM, TON, Solana, 0G, or unknown",
            "entity": "domain, wallet, contract, node, or agent id",
            "features": "derived detector and reputation features only",
            "source_refs": "URLs, source ids, and hashes",
            "rights": "license/terms class and raw-resale decision",
        },
        "backfillLanes": [
            {
                "id": "incident_corpus_2020_present",
                "priority": 1,
                "sources": ["existing April 2026 dataset", "public reports", "open labelled datasets"],
                "output": "detector training/evaluation features",
                "qualityChecks": ["source_link_present", "loss_usd_optional", "detector_mapping"],
            },
            {
                "id": "reputation_history",
                "priority": 2,
                "sources": ["PhishDestroy", "CryptoScamDB", "MetaMask eth-phishing-detect", "Forta labels"],
                "output": "domain/address first-seen, persistence, and confidence features",
                "qualityChecks": ["license_reviewed", "source_hash", "dedupe_key"],
            },
            {
                "id": "node_ops_timeseries",
                "priority": 3,
                "sources": ["Windows storage snapshots", "rvpi-a heartbeat", "public explorers"],
                "output": "sync gap, peer count, relay health, and blocker timeline",
                "qualityChecks": ["no_keys", "no_private_logs", "source_host_redacted_if_needed"],
            },
            {
                "id": "telegram_opt_in_events",
                "priority": 4,
                "sources": ["local opt-in registry only"],
                "output": "redacted subscription and cooldown state",
                "qualityChecks": ["no_raw_chat_body", "redacted_public_user", "opt_out_supported"],
            },
            {
                "id": "x402_receipt_metadata",
                "priority": 5,
                "sources": ["future testnet/mainnet payment receipts"],
                "output": "paid-access audit trail without payment signatures or secrets",
                "qualityChecks": ["no_payment_header_storage", "spend_limit_recorded", "route_schema_pinned"],
            },
        ],
        "freshnessPlan": [
            "Backfill historical incident and reputation lanes first because they improve every verdict.",
            "Snapshot node telemetry on a schedule, but treat it as operator evidence, not public claims.",
            "Promote x402 metadata only after dry-run contract tests and testnet settlement proof exist.",
        ],
        "safety": _safety(live_network_calls=False),
    }


def _ollama_node(
    *,
    node_id: str,
    label: str,
    url: str,
    role: str,
    live: bool,
    timeout_seconds: float,
    http_get: HttpGet,
    currentObservation: str,
) -> dict[str, Any]:
    base = _public_url(url)
    node = {
        "id": node_id,
        "label": label,
        "role": role,
        "baseUrl": base,
        "tagsUrl": f"{base}/api/tags",
        "status": "not_checked",
        "reachable": None,
        "modelNames": [],
        "promptExecutionEnabled": False,
        "currentObservation": currentObservation,
    }
    if not live:
        return node
    result = _read_json(f"{url}/api/tags", timeout_seconds=timeout_seconds, http_get=http_get)
    node["probe"] = result
    node["reachable"] = result["ok"]
    if not result["ok"]:
        node["status"] = "unreachable"
        return node
    payload = result.get("json") if isinstance(result.get("json"), dict) else {}
    models = payload.get("models") if isinstance(payload, dict) else []
    model_names = [
        str(item.get("name") or item.get("model"))
        for item in models or []
        if isinstance(item, dict) and (item.get("name") or item.get("model"))
    ]
    node["modelNames"] = model_names
    node["status"] = "ready" if model_names else "reachable_no_models"
    return node


def _edge_health_node(
    *,
    node_id: str,
    label: str,
    url: str,
    role: str,
    live: bool,
    timeout_seconds: float,
    http_get: HttpGet,
    currentObservation: str,
) -> dict[str, Any]:
    node = {
        "id": node_id,
        "label": label,
        "role": role,
        "healthUrl": _public_url(url),
        "status": "not_checked",
        "reachable": None,
        "promptExecutionEnabled": False,
        "currentObservation": currentObservation,
    }
    if not live:
        return node
    result = _read_json(url, timeout_seconds=timeout_seconds, http_get=http_get)
    node["probe"] = result
    node["reachable"] = result["ok"]
    if not result["ok"]:
        node["status"] = "unreachable"
        return node
    payload = result.get("json") if isinstance(result.get("json"), dict) else {}
    node["status"] = "edge_ready"
    node["service"] = {
        "host": payload.get("host"),
        "role": payload.get("role"),
        "mode": payload.get("mode"),
        "safety": payload.get("safety"),
    }
    return node


def _read_json(url: str, *, timeout_seconds: float, http_get: HttpGet) -> dict[str, Any]:
    try:
        response = http_get(url, timeout=timeout_seconds)
    except requests.RequestException as exc:
        return {"ok": False, "status": "request_failed", "error": str(exc)}
    except OSError as exc:
        return {"ok": False, "status": "request_failed", "error": str(exc)}
    status_code = getattr(response, "status_code", None)
    if status_code != 200:
        return {"ok": False, "status": "http_error", "httpStatus": status_code}
    try:
        payload = response.json()
    except ValueError as exc:
        return {"ok": False, "status": "invalid_json", "httpStatus": status_code, "error": str(exc)}
    return {"ok": True, "status": "ok", "httpStatus": status_code, "json": payload}


def _mesh_blockers(nodes: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    if not any(node.get("id") == "windows_ollama" and node.get("modelNames") for node in nodes):
        blockers.append("windows_ollama_model_not_loaded")
    if not any(node.get("id") == "rvpi_a_edge" and node.get("reachable") is True for node in nodes):
        blockers.append("rvpi_a_edge_health_not_live_checked")
    if not any(
        node.get("id") == "rvpi_b_ollama_candidate" and node.get("reachable") is True
        for node in nodes
    ):
        blockers.append("rvpi_b_runtime_not_verified")
    return blockers


def _public_url(url: str) -> str:
    parsed = urlsplit(url)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path.rstrip("/"), "", ""))


def _public_opt_in(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "record_id": record.get("record_id"),
        "active": record.get("active"),
        "scopes": record.get("scopes") or [],
    }


def _safety(*, live_network_calls: bool) -> dict[str, Any]:
    return {
        "readOnly": True,
        "liveNetworkCalls": live_network_calls,
        "promptExecutionEnabled": False,
        "paidInferenceEnabled": False,
        "telegramSendsEnabled": False,
        "externalMessagesEnabled": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "moneyMovementEnabled": False,
        "privateKeysReturned": False,
        "rawPayloadsReturned": False,
        "x402SettlementEnabled": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
