"""
Flask API & Dashboard for 0G Hack Guard
========================================
Endpoints:
  GET  /api/health
  GET  /api/frontend-contract
  GET  /api/external-action-contracts
  POST /api/evaluate
  POST /api/hack-check
  GET  /api/domain
"""

from __future__ import annotations

import os

from flask import Flask, Response, jsonify, render_template, request

from guard0.policy import evaluate_intent
from guard0.crypto_hack_guard import check_crypto_hack_signatures

app = Flask(__name__)

FRONTEND_REQUIRED_SELECTORS = (
    "#nav-intent",
    "#nav-signatures",
    "#nav-domain",
    "#mode-pill",
    "#send-pill",
    "#chain-pill",
    "#decision-pill",
    "#intent-input",
    "#run-evaluate",
    "#load-deny-sample",
    "#load-allow-sample",
    "#hack-input",
    "#run-hack-check",
    "#domain-input",
    "#run-domain-check",
    "#result-output",
    "#contract-output",
    "#wallet-status",
    "#telegram-status",
    "#deploy-status",
)


def external_action_contracts_payload() -> dict:
    """Return the non-mutating external action posture for the workbench."""
    return {
        "schema": "0guard.external_action_contracts.v1",
        "defaultMode": "dry_run",
        "workbenchCanTriggerLiveActions": False,
        "livePostingEnabled": False,
        "telegramSendsEnabled": False,
        "transactionSigningEnabled": False,
        "transactionBroadcastingEnabled": False,
        "moneyMovementEnabled": False,
        "secretDisplayEnabled": False,
        "actions": [
            {
                "id": "x-post",
                "script": "scripts/x_post.py",
                "default": "dry_run",
                "liveConfirmationFlag": "--live-post-confirm POST_TO_X_FROM_0GUARD",
                "reachableFromWorkbench": False,
            },
            {
                "id": "telegram-post",
                "script": "scripts/telegram_post.py",
                "default": "dry_run",
                "liveConfirmationFlag": "--live-send-confirm SEND_TO_TELEGRAM_FROM_0GUARD",
                "reachableFromWorkbench": False,
            },
            {
                "id": "0g-contract-deploy",
                "script": "scripts/deploy_0g.py",
                "default": "blocked_from_workbench",
                "liveConfirmationFlag": "local CLI only with PRIVATE_KEY and explicit operator review",
                "reachableFromWorkbench": False,
            },
        ],
        "blockedCapabilities": [
            "wallet signature requests",
            "raw transaction broadcasting",
            "X/Telegram posting from the browser",
            "secret display or echo",
            "fund movement",
            "production deploys",
        ],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return Response(status=204)


@app.route("/api/frontend-contract", methods=["GET"])
def api_frontend_contract():
    return jsonify(
        {
            "schema": "0guard.frontend_contract.v1",
            "route": "/",
            "mode": "read_only_pre_wallet",
            "network": "0g",
            "chainId": int(os.getenv("ZGG_CHAIN_ID", "16600")),
            "requiredText": [
                "0G Hack Guard",
                "Intent Firewall",
                "Hack Signature Check",
                "Domain Guard",
                "External Action Contract",
                "Safety Inspector",
                "no signing",
                "external sends blocked",
            ],
            "requiredSelectors": list(FRONTEND_REQUIRED_SELECTORS),
            "apiRoutes": [
                "/api/health",
                "/api/external-action-contracts",
                "/api/evaluate",
                "/api/hack-check",
                "/api/domain?url=https%3A%2F%2Fdocs.0g.ai",
            ],
            "primaryActions": [
                "evaluate-intent",
                "load-deny-sample",
                "load-simulation-sample",
                "run-hack-check",
                "run-domain-check",
            ],
            "safety": external_action_contracts_payload(),
        }
    )


@app.route("/api/external-action-contracts", methods=["GET"])
def api_external_action_contracts():
    return jsonify(external_action_contracts_payload())


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify(
        {
            "service": "zg-hack-guard",
            "version": "0.1.0",
            "0g_chain_id": int(os.getenv("ZGG_CHAIN_ID", "16600")),
            "0g_storage_node": os.getenv("ZGS_NODE_URL", "not_configured"),
            "safety_flags": {
                "read_only": True,
                "wallet_signatures_blocked": True,
                "external_sends_blocked_from_workbench": True,
                "live_posting_enabled": False,
                "telegram_sends_enabled": False,
                "money_movement_enabled": False,
            },
        }
    )


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    body = request.get_json(silent=True) or {}
    intent = body.get("intent", body)
    budget = body.get("budget")
    agent_id = body.get("agent_id", "")
    decision = evaluate_intent(
        intent,
        budget=budget,
        agent_id=agent_id,
        enable_0g_anchor=body.get("enable_0g_anchor", False),
        enable_0g_storage=body.get("enable_0g_storage", False),
    )
    return jsonify(decision.to_dict())


@app.route("/api/hack-check", methods=["POST"])
def api_hack_check():
    payload = request.get_json(silent=True) or {}
    from guard0.policy import normalize_intent

    result = check_crypto_hack_signatures(normalize_intent(payload))
    return jsonify(result.to_dict())


@app.route("/api/domain", methods=["GET"])
def api_domain():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "Missing url parameter"}), 400
    # Simple domain guard — can be expanded
    allowed = ["0g.ai", "hackquest.io", "github.com", "docs.0g.ai"]
    is_allowed = any(a in url.lower() for a in allowed)
    return jsonify(
        {
            "url": url,
            "decision": "allow" if is_allowed else "review",
            "reasons": [] if is_allowed else ["Domain not in curated allowlist"],
        }
    )


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8109"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
