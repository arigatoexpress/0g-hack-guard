"""Plain-English product brief for the current 0guard stack."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from guard0.incident_data import detection_coverage, incident_summary

PRODUCT_BRIEF_SCHEMA = "0guard.product_brief.v1"


def product_brief() -> dict[str, Any]:
    """Return a compact, honest map of what 0guard is and what is live."""
    summary = incident_summary()
    coverage = detection_coverage()
    return {
        "schema": PRODUCT_BRIEF_SCHEMA,
        "generatedAt": _now(),
        "name": "0guard",
        "oneLiner": (
            "0guard is a pre-wallet firewall for AI agents: it checks intent, "
            "calldata, domain/reputation context, and exploit intelligence before "
            "any signer is asked to act."
        ),
        "plainEnglish": [
            "An AI agent wants to do something with a wallet.",
            "0guard reads the request before a wallet prompt appears.",
            "Safe read-only actions can continue.",
            "Risky signing, sweep, bridge, payment, exchange, or phishing-shaped actions are denied or sent to review.",
            "Every verdict can produce a receipt that is ready for 0G proof workflows.",
        ],
        "builtSystems": _built_systems(summary, coverage),
        "liveProof": _live_proof(summary, coverage),
        "currentStrengths": [
            "Clear wedge: protect the moment before wallet custody, not after a signature prompt appears.",
            "A composed threat case file turns one risky agent action into judge/operator-readable evidence.",
            "A frontier experiment lab ranks the next integrations while proving no live side effects occurred.",
            "A no-network adapter normalizer turns GoPlus, Chainabuse, and Forta-shaped payloads into derived evidence.",
            "Real source-linked incident data and detector coverage instead of mock security claims.",
            "A live Telegram Mini App surface that remains preview-only and no-send.",
            "Portable developer-kit routes that other wallets, agents, Mini Apps, CI jobs, and dWallet flows can call.",
            "Rights-aware OSINT posture: external feeds become derived signals, not raw data resale.",
        ],
        "honestLimits": [
            "0G Storage upload/readback and 0G Compute inference are prepared as product lanes, not silently enabled from the workbench.",
            "GoPlus, Chainabuse, Forta, TONAPI, and simulation feed live fetches are activation-ready but disabled until keys and terms are reviewed.",
            "The GoPlus/Chainabuse/Forta normalizer is live for caller-provided payloads and returns only derived evidence.",
            "The Telegram bot and Mini App are live, but outbound Telegram sends are intentionally disabled.",
            "X, LinkedIn, Substack, wallet signing, x402 settlement, bridge/swap actions, and exchange actions require separate operator-controlled paths.",
        ],
        "nextBestBuilds": [
            {
                "rank": 1,
                "id": "reputation_connector_activation",
                "why": "Highest practical value for wallet/domain safety and Telegram alerts.",
                "ship": "Enable one external connector worker first, probably GoPlus or Chainabuse, and route it through the existing derived-output normalizer.",
            },
            {
                "rank": 2,
                "id": "threat_case_file_productization",
                "why": "Best demo and operator comprehension lift because it stitches every existing proof surface together.",
                "ship": "Use /api/threat-case-file as the default judge/operator drill for risky agent intents.",
            },
            {
                "rank": 3,
                "id": "0g_storage_receipt_readback",
                "why": "Makes the 0G story more than a chain anchor by proving receipt payload availability.",
                "ship": "Operator-approved upload/readback CLI plus public-safe receipt hash display.",
            },
            {
                "rank": 4,
                "id": "evm_simulation_adapter",
                "why": "State deltas make approvals, swaps, upgrades, and bridge messages easier for normal users to understand.",
                "ship": "Tenderly or BlockSec adapter returning derived asset-delta summaries only.",
            },
            {
                "rank": 5,
                "id": "telegram_ton_risk_passport",
                "why": "Telegram users are the natural first audience; TON should be native rather than bridged.",
                "ship": "TON Center or TONAPI read-only account/Jetton context feeding the Mini App passport.",
            },
        ],
        "socialPositioning": {
            "xThreadFile": "content/0guard_current_update_x_thread.json",
            "substackDraftFile": "content/substack_0guard_launch_draft.md",
            "recommendedTone": "plain-spoken, proof-first, not hype-first",
            "avoidClaims": [
                "Do not claim autonomous live blocking of all wallet attacks.",
                "Do not claim raw paid-feed ownership.",
                "Do not imply 0guard signs, broadcasts, bridges, swaps, or sends alerts in production by itself.",
            ],
        },
        "safety": _safety(),
    }


def _built_systems(summary: dict[str, Any], coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "intent_firewall",
            "label": "Intent firewall",
            "status": "live",
            "whatItDoes": "Returns allow, review, or deny before wallet access.",
            "proofRoutes": ["/api/evaluate", "/api/native-preflight"],
        },
        {
            "id": "incident_intelligence",
            "label": "Incident-derived exploit intelligence",
            "status": "live",
            "whatItDoes": "Uses source-linked incidents and detector signatures to catch known exploit shapes.",
            "proof": {
                "incidentCount": (summary.get("meta") or {}).get("total_incidents")
                or coverage.get("incidentCount"),
                "coverageRatio": coverage.get("coverageRatio"),
                "coveredCount": coverage.get("coveredCount"),
            },
            "proofRoutes": [
                "/api/data/summary",
                "/api/data/provenance",
                "/api/data/signature-map",
            ],
        },
        {
            "id": "reputation_probe",
            "label": "Reputation probe",
            "status": "live_local_derived",
            "whatItDoes": "Scores domains, counterparties, labels, source evidence, and intent context without returning raw source payloads.",
            "proofRoutes": [
                "/api/reputation/probe",
                "/api/reputation/connectors",
                "/api/reputation/adapters",
                "/api/reputation/adapters/normalize",
            ],
        },
        {
            "id": "threat_case_file",
            "label": "Threat case file",
            "status": "live_preview_no_side_effects",
            "whatItDoes": "Composes policy, signatures, reputation, wallet alert gates, provenance, and 0G-ready receipts into one proof dossier.",
            "proofRoutes": ["/api/threat-case-file"],
        },
        {
            "id": "frontier_experiment_lab",
            "label": "Frontier experiment lab",
            "status": "live_read_only_experiment_backlog",
            "whatItDoes": "Ranks and previews 0G Storage/Compute, reputation, simulation, TON, and Mira activation paths without live side effects.",
            "proofRoutes": ["/api/experiments/frontier", "/api/experiments/run"],
        },
        {
            "id": "telegram_mini_app",
            "label": "Telegram Mini App",
            "status": "live_preview_no_send",
            "whatItDoes": "Shows mobile wallet-alert and Mira explanations with server-side Telegram initData validation support.",
            "proofRoutes": ["/telegram", "/api/telegram/miniapp/preview"],
        },
        {
            "id": "0g_receipts",
            "label": "0G-ready receipts",
            "status": "mainnet_anchor_plus_storage_ready_payloads",
            "whatItDoes": "Produces deterministic receipts for policy and threat decisions, with public mainnet proof already recorded.",
            "proofRoutes": ["/api/0g/status", "/api/0g/receipt", "/api/hackathon/threat-passport"],
        },
        {
            "id": "developer_kit",
            "label": "Developer kit",
            "status": "live",
            "whatItDoes": "Exposes SDK/CI/wallet/Mini App/dWallet recipes for calling 0guard before any signer.",
            "proofRoutes": ["/api/developer-kit"],
        },
        {
            "id": "cross_ecosystem_guardrails",
            "label": "Cross-ecosystem guardrails",
            "status": "live_read_only_catalog",
            "whatItDoes": "Models x402, Virtuals/Base, Lighter, CCIP, LayerZero, Wormhole, Celestia, TON, Solana, Hyperliquid, Ika, and Ikavery as read-only policy surfaces.",
            "proofRoutes": [
                "/api/integrations/cross-chain",
                "/api/integrations/external-guardrails",
                "/api/integrations/ika",
            ],
        },
    ]


def _live_proof(summary: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "miniApp": "https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram",
        "telegramBot": "https://t.me/Raris0guardBot",
        "proofHub": "https://arigatoexpress.github.io/0guard/hackathon-0g/",
        "demoVideo": "https://arigatoexpress.github.io/0guard/hackathon-0g/assets/0guard-hackquest-demo-final.mp4",
        "repo": "https://github.com/arigatoexpress/0guard",
        "productionHealth": "/api/healthz",
        "incidentCount": (summary.get("meta") or {}).get("total_incidents")
        or coverage.get("incidentCount"),
        "detectorCoverageRatio": coverage.get("coverageRatio"),
        "readOnlyDefault": True,
    }


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "paymentSettlementEnabled": False,
        "exchangeOrdersEnabled": False,
        "bridgingEnabled": False,
        "rawPayloadsReturned": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
