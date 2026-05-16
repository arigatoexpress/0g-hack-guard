"""Next-hackathon integration plans for 0guard.

The plans in this module are intentionally executable-roadmap surfaces, not
claims that 0guard has already deployed into each ecosystem. They keep the
project 0G-first while making Arbitrum and MetaMask/agent-wallet work concrete
enough for APIs, docs, and judges to inspect.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from guard0.crosschain import cross_chain_catalog

NEXT_HACKATHON_PLAN_SCHEMA = "0guard.next_hackathon_plan.v1"
ARBITRUM_INTEGRATION_PLAN_SCHEMA = "0guard.arbitrum_integration_plan.v1"
METAMASK_INTEGRATION_PLAN_SCHEMA = "0guard.metamask_integration_plan.v1"


def next_hackathon_plan() -> dict[str, Any]:
    """Return chronological, source-cited hackathon targets and build slices."""
    opportunities = [
        {
            "rank": 1,
            "id": "arbitrum_open_house_london_online_buildathon",
            "name": "Arbitrum Open House London Online Buildathon",
            "status": "active",
            "timing": {
                "registrationDeadline": "2026-05-25",
                "submissionDeadline": "2026-06-14",
                "rewardAnnouncement": "2026-06-17",
            },
            "primaryTrackFit": "agentic_wallet_and_l2_security",
            "why0guardFits": (
                "0guard can become an Arbitrum Agent Safety Pack: pre-signer "
                "intent review, simulation-ready verdict receipts, and L2 config "
                "guardrails before upgrades, retryables, Stylus deploys, or Orbit "
                "admin actions reach a wallet."
            ),
            "buildNow": [
                "Expose Arbitrum One, Nova, and Sepolia as read-only catalog targets.",
                "Review Arbitrum intents through native-preflight before any deploy/admin wallet prompt.",
                "Use Arbitrum Sepolia for proof-contract demos; keep 0G as the durable receipt/provenance anchor.",
            ],
            "doNotClaimYet": [
                "No live Arbitrum deployment is performed by these routes.",
                "No Robinhood Chain chain id or RPC is included until official docs are re-read.",
                "No bridge, deposit, withdrawal, or sequencer endpoint is called by 0guard.",
            ],
            "officialSources": [
                "https://www.hackquest.io/hackathons/Arbitrum-Open-House-London-Online-Buildathon",
                "https://openhouse.arbitrum.io/",
                "https://docs.arbitrum.io/build-decentralized-apps/reference/node-providers",
                "https://docs.arbitrum.io/stylus/quickstart",
            ],
        },
        {
            "rank": 2,
            "id": "ethglobal_new_york_2026_metamask_wallet_security",
            "name": "ETHGlobal New York 2026 / MetaMask wallet-safety lane",
            "status": "upcoming",
            "timing": {
                "eventDates": "2026-06-12 to 2026-06-14",
            },
            "primaryTrackFit": "wallet_security_and_agent_permissions",
            "why0guardFits": (
                "The MetaMask lane should be a wrapper/Snap concept that gates "
                "transactions, typed-data signatures, and delegation permissions "
                "through 0guard before MetaMask is invoked."
            ),
            "buildNow": [
                "Add a MetaMask Connect wrapper example around eth_sendTransaction and signTypedData.",
                "Design a Snap transaction/signature-insights handoff that displays 0guard receipts.",
                "Inspect Smart Accounts Kit advanced-permission caveats before a delegated execution runs.",
            ],
            "doNotClaimYet": [
                "0guard is not a wallet, custodian, or MetaMask partner.",
                "No extension/Snap publishing occurs without operator review.",
                "No delegated execution is redeemed by the repo.",
            ],
            "officialSources": [
                "https://ethglobal.com/events/newyork2026",
                "https://docs.metamask.io/metamask-connect/",
                "https://docs.metamask.io/snaps/features/transaction-insights/",
                "https://docs.metamask.io/snaps/features/signature-insights/",
                "https://docs.metamask.io/smart-accounts-kit/",
            ],
        },
        {
            "rank": 3,
            "id": "nanda_hack_ai_agent_trust",
            "name": "NANDA Hack / AI-agent trust and safety lane",
            "status": "upcoming",
            "timing": {
                "challengeDeadline": "2026-06-13",
                "liveEventDate": "2026-07-11",
            },
            "primaryTrackFit": "agent_identity_reputation_and_verifiable_safety",
            "why0guardFits": (
                "0guard can be framed as a verifiable guardrail that agent "
                "frameworks call before accepting wallet, payment, or signing tasks."
            ),
            "buildNow": [
                "Turn native-preflight into a tiny agent middleware recipe.",
                "Return receipts, source ids, and expiration/TTL so agents can explain decisions.",
                "Keep unsafe actions blocked outside the agent runtime rather than hidden in prompts.",
            ],
            "doNotClaimYet": [
                "No autonomous agent is allowed to sign or move assets.",
                "No identity/reputation claim is made without source-backed evidence.",
            ],
            "officialSources": [
                "https://nandahack.media.mit.edu/",
                "https://eips.ethereum.org/EIPS/eip-8004",
            ],
        },
    ]
    return {
        "schema": NEXT_HACKATHON_PLAN_SCHEMA,
        "generatedAt": _now(),
        "guidingPrinciple": "0G-first receipts, native-chain context, no bridge-first product story.",
        "sourceCheckedAt": "2026-05-16",
        "opportunityCount": len(opportunities),
        "opportunities": opportunities,
        "oodaLoop": {
            "observe": "Read live source/data readiness, chain heads, and adapter evidence.",
            "orient": "Map the action to the native ecosystem: 0G, Arbitrum, MetaMask, TON, or agent framework.",
            "decide": "Return allow/review/deny with cited evidence, TTL, and receipt hash.",
            "act": "Only the caller proceeds; 0guard itself never signs, broadcasts, posts, bridges, or settles.",
        },
        "nextShipSequence": [
            "Add real polling snapshots before any websocket/SSE promise.",
            "Land Arbitrum read-only profiles and intent guardrails.",
            "Land MetaMask wrapper/Snap architecture and delegation caveat checks.",
            "Only then add richer live connectors behind credentials and explicit retention terms.",
        ],
        "safety": _safety(),
    }


def arbitrum_integration_plan() -> dict[str, Any]:
    """Return the Arbitrum-specific safe build plan."""
    catalog = cross_chain_catalog()
    targets = [
        target
        for target in catalog["targets"]
        if str(target.get("id", "")).startswith("arbitrum_")
    ]
    return {
        "schema": ARBITRUM_INTEGRATION_PLAN_SCHEMA,
        "generatedAt": _now(),
        "positioning": "Arbitrum Agent Safety Pack for pre-signer L2 and Orbit/Stylus operations.",
        "networks": targets,
        "routeMap": [
            {
                "path": "/api/integrations/arbitrum",
                "mode": "plan_and_catalog",
                "sideEffects": False,
            },
            {
                "path": "/api/integrations/cross-chain/readiness?live=1&include_non_default=1",
                "mode": "optional_read_only_rpc_heads",
                "sideEffects": False,
            },
            {
                "path": "/api/native-preflight",
                "mode": "pre_signer_intent_review",
                "examplePayload": {
                    "surface": "arbitrum_sepolia",
                    "operation": "upgrade_proxy",
                    "chain": "eip155:421614",
                    "config": {"nativePreflightReceipt": "required_before_wallet_prompt"},
                },
            },
            {
                "path": "/api/integrations/external-guardrails/evaluate",
                "mode": "arbitrum_config_and_action_review",
                "examplePayload": {
                    "target_id": "arbitrum_orbit",
                    "action": "update_dac_config",
                    "config": {"liveTransaction": True},
                },
            },
        ],
        "riskRules": {
            "deny": [
                "private key, mnemonic, signed transaction blob, or eth_sendRawTransaction request",
                "bridge, deposit, withdrawal, or retryable execution as an autonomous side effect",
                "sequencer endpoint mutation or Orbit chain-owner/DAC mutation without operator review",
            ],
            "review": [
                "retryable tickets, sendTxToL1, proxy upgrades, role grants, Stylus deploy/activation, Orbit config changes",
                "Arbiscan/Etherscan keyed enrichment before API terms and cache TTL are configured",
            ],
            "allow": [
                "eth_chainId, eth_blockNumber, eth_call, eth_estimateGas, eth_getCode, eth_getBalance, transaction receipt lookup",
                "read-only explorer links, derived receipt summaries, and 0G proof-root context",
            ],
        },
        "demoPath": [
            "Read Arbitrum Sepolia chain head.",
            "Submit a risky approval/upgrade intent to native-preflight.",
            "Show 0guard review/deny receipt and 0G proof context.",
            "Only after operator approval, manually deploy or verify an Arbitrum Sepolia proof contract if needed for the hackathon.",
        ],
        "officialSources": [
            "https://docs.arbitrum.io/build-decentralized-apps/reference/node-providers",
            "https://docs.arbitrum.io/build-decentralized-apps/how-to-estimate-gas",
            "https://docs.arbitrum.io/build-decentralized-apps/nodeinterface/reference",
            "https://docs.arbitrum.io/stylus/quickstart",
            "https://docs.arbitrum.io/launch-arbitrum-chain/arbitrum-chain-sdk-introduction",
        ],
        "safety": _safety(),
    }


def metamask_integration_plan() -> dict[str, Any]:
    """Return the MetaMask/agent-wallet integration plan."""
    return {
        "schema": METAMASK_INTEGRATION_PLAN_SCHEMA,
        "generatedAt": _now(),
        "positioning": (
            "0guard is a pre-signer guard for MetaMask-connected dapps and "
            "agent wallets; it is not a wallet, custodian, Snap publisher, or "
            "delegation redeemer in this repo state."
        ),
        "integrationLayers": [
            {
                "id": "connect_wrapper",
                "status": "build_next",
                "whereItRuns": "dapp or agent frontend before window.ethereum.request",
                "gatedMethods": [
                    "eth_sendTransaction",
                    "personal_sign",
                    "eth_signTypedData_v4",
                    "wallet_requestPermissions",
                ],
                "guardRoute": "/api/native-preflight",
                "value": "Blocks or explains risky prompts before the wallet UI appears.",
            },
            {
                "id": "snap_transaction_signature_insights",
                "status": "architecture_ready_operator_review_required",
                "whereItRuns": "MetaMask Snaps insights surfaces",
                "guardRoute": "/api/native-preflight",
                "value": "Show source-cited 0guard verdicts inside transaction and signature reviews.",
            },
            {
                "id": "smart_accounts_advanced_permissions",
                "status": "docs_verified_design_lane",
                "whereItRuns": "Smart Accounts Kit / Delegation Toolkit permission grants and delegated execution",
                "gatedMethods": [
                    "requestExecutionPermissions",
                    "sendTransactionWithDelegation",
                    "sendUserOperationWithDelegation",
                ],
                "guardRoute": "/api/integrations/external-guardrails/evaluate",
                "value": "Reject unbounded delegated authority; require expiry, max spend, caveats, and a 0guard receipt before execution.",
            },
        ],
        "minimumControls": [
            "Every spending or delegation request needs expiry and scoped max amount.",
            "Every execution must carry a native-preflight receipt hash before wallet prompt.",
            "Raw typed-data and transaction payloads are hashed/redacted in public artifacts.",
            "Publishing a Snap or extension is operator-only after manual review.",
        ],
        "agentFit": [
            "Agents can ask 0guard for a verdict before proposing a wallet action.",
            "Receipts give users a compact reason without trusting an LLM explanation alone.",
            "Delegated authority can be bounded by source-cited policy instead of broad unlimited approvals.",
        ],
        "officialSources": [
            "https://docs.metamask.io/metamask-connect/",
            "https://docs.metamask.io/metamask-connect/evm/reference/json-rpc-api/",
            "https://docs.metamask.io/snaps/features/transaction-insights/",
            "https://docs.metamask.io/snaps/features/signature-insights/",
            "https://docs.metamask.io/smart-accounts-kit/",
            "https://docs.metamask.io/smart-accounts-kit/get-started/supported-advanced-permissions/",
        ],
        "safety": _safety(),
    }


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "transactionSigningEnabled": False,
        "broadcastingEnabled": False,
        "bridgingEnabled": False,
        "swappingEnabled": False,
        "moneyMovementEnabled": False,
        "externalAgentLaunchEnabled": False,
        "socialPostingEnabled": False,
        "rawPayloadsReturned": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
