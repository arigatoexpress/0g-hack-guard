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

from flask import Flask, jsonify, render_template_string, request, Response

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


HTML_DASHBOARD = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>0guard Workbench</title>
  <style>
    :root{
      color-scheme:dark;
      --bg:#080a0f;
      --panel:#121823;
      --panel-2:#172031;
      --border:#2b3a4d;
      --text:#e9eef6;
      --muted:#96a6ba;
      --accent:#24d3a5;
      --accent-2:#7cc7ff;
      --danger:#ff6b6b;
      --warn:#f8c15c;
      --ok:#32d583;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      background:var(--bg);
      color:var(--text);
      font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      letter-spacing:0;
    }
    .shell{
      min-height:100vh;
      display:grid;
      grid-template-columns:220px minmax(0,1fr) 320px;
    }
    nav,.inspector{
      background:#0c111a;
      border-color:var(--border);
      padding:22px;
    }
    nav{border-right:1px solid var(--border)}
    .inspector{border-left:1px solid var(--border)}
    main{padding:24px;min-width:0}
    .brand{font-size:22px;font-weight:800;margin-bottom:8px}
    .muted{color:var(--muted)}
    .nav-item{
      display:block;
      width:100%;
      margin:10px 0;
      padding:10px 12px;
      border:1px solid var(--border);
      border-radius:8px;
      background:transparent;
      color:var(--text);
      text-align:left;
      font-weight:700;
    }
    .nav-item.active{border-color:var(--accent);color:var(--accent)}
    .hero{
      display:flex;
      justify-content:space-between;
      gap:20px;
      align-items:flex-start;
      margin-bottom:22px;
    }
    h1,h2,h3,p{margin-top:0}
    h1{font-size:36px;line-height:1.05;margin-bottom:10px}
    h2{font-size:18px;margin-bottom:12px}
    h3{font-size:14px;margin-bottom:8px;color:var(--muted);text-transform:uppercase}
    .grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,420px);gap:18px}
    .card{
      background:var(--panel);
      border:1px solid var(--border);
      border-radius:8px;
      padding:18px;
      min-width:0;
    }
    .stack{display:grid;gap:14px}
    .rail-list{display:grid;gap:10px;margin-top:16px}
    .status{
      display:flex;
      justify-content:space-between;
      gap:12px;
      padding:10px 0;
      border-bottom:1px solid var(--border);
      color:var(--muted);
    }
    .status strong{color:var(--text);text-align:right}
    .pill{
      display:inline-flex;
      align-items:center;
      min-height:28px;
      padding:4px 10px;
      border-radius:999px;
      border:1px solid var(--border);
      color:var(--text);
      background:var(--panel-2);
      font-size:12px;
      font-weight:800;
      white-space:nowrap;
    }
    .pill.deny{border-color:rgba(255,107,107,.6);color:var(--danger)}
    .pill.allow{border-color:rgba(50,213,131,.6);color:var(--ok)}
    .pill.review{border-color:rgba(248,193,92,.7);color:var(--warn)}
    .actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
    button{
      min-height:38px;
      border:1px solid var(--accent);
      background:var(--accent);
      color:#06110d;
      border-radius:8px;
      padding:8px 13px;
      cursor:pointer;
      font-weight:800;
    }
    button.secondary{
      background:transparent;
      color:var(--accent-2);
      border-color:var(--border);
    }
    textarea,input{
      width:100%;
      border:1px solid var(--border);
      border-radius:8px;
      background:#0a0f17;
      color:var(--text);
      padding:12px;
      font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
    }
    pre{
      min-height:240px;
      max-height:520px;
      overflow:auto;
      margin:0;
      padding:14px;
      border-radius:8px;
      background:#05070b;
      border:1px solid var(--border);
      color:#d7e2f0;
      font:12px/1.55 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
      white-space:pre-wrap;
    }
    .mini{font-size:12px;color:var(--muted);line-height:1.45}
    @media(max-width:980px){
      .shell{grid-template-columns:1fr}
      nav,.inspector{border:0;border-bottom:1px solid var(--border)}
      .grid,.hero{grid-template-columns:1fr;display:grid}
    }
  </style>
</head>
<body>
  <div class="shell">
    <nav aria-label="Workbench sections">
      <div class="brand">0guard</div>
      <p class="mini">Read-only agent firewall for 0G hack signatures.</p>
      <button class="nav-item active" id="nav-intent" type="button">Intent Firewall</button>
      <button class="nav-item" id="nav-signatures" type="button">Hack Signatures</button>
      <button class="nav-item" id="nav-domain" type="button">Domain Guard</button>
      <div class="rail-list">
        <span class="pill deny" id="mode-pill">no signing</span>
        <span class="pill deny" id="send-pill">external sends blocked</span>
        <span class="pill review" id="chain-pill">0G preflight only</span>
      </div>
    </nav>

    <main>
      <section class="hero">
        <div>
          <h1>0G Hack Guard</h1>
          <p class="muted">Evaluate wallet-adjacent agent intents before they reach a signing key.</p>
        </div>
        <span class="pill deny" id="decision-pill">default deny</span>
      </section>

      <section class="grid">
        <div class="stack">
          <div class="card">
            <h2>Intent Firewall</h2>
            <textarea id="intent-input" rows="10">{
  "action": "swap",
  "mode": "live_transaction",
  "value_eth": 0.05,
  "calldata": "0x095ea7b3000000000000000000000000a0b86a33e6776808dc56eb68bb0a0f74ff38ffff",
  "requires_signature": true
}</textarea>
            <div class="actions">
              <button id="run-evaluate" type="button">Evaluate</button>
              <button id="load-deny-sample" class="secondary" type="button">Deny sample</button>
              <button id="load-allow-sample" class="secondary" type="button">Simulation sample</button>
            </div>
          </div>

          <div class="card">
            <h2>Hack Signature Check</h2>
            <textarea id="hack-input" rows="6">{
  "action": "approve",
  "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
}</textarea>
            <div class="actions">
              <button id="run-hack-check" type="button">Run hack check</button>
            </div>
          </div>

          <div class="card">
            <h2>Domain Guard</h2>
            <input id="domain-input" value="https://docs.0g.ai">
            <div class="actions">
              <button id="run-domain-check" type="button">Check URL</button>
            </div>
          </div>
        </div>

        <div class="stack">
          <div class="card">
            <h2>Decision Output</h2>
            <pre id="result-output">Awaiting evaluation.</pre>
          </div>
          <div class="card">
            <h2>External Action Contract</h2>
            <pre id="contract-output">Loading contract.</pre>
          </div>
        </div>
      </section>
    </main>

    <aside class="inspector" aria-label="Safety posture">
      <h2>Safety Inspector</h2>
      <div class="status"><span>Wallet signatures</span><strong id="wallet-status">blocked</strong></div>
      <div class="status"><span>Transactions</span><strong id="tx-status">blocked</strong></div>
      <div class="status"><span>X posting</span><strong id="x-status">dry-run default</strong></div>
      <div class="status"><span>Telegram sends</span><strong id="telegram-status">dry-run default</strong></div>
      <div class="status"><span>0G deploys</span><strong id="deploy-status">CLI confirm only</strong></div>
      <div class="status"><span>Secrets</span><strong id="secret-status">not displayed</strong></div>
      <p class="mini" style="margin-top:18px">Live external actions require explicit local CLI confirmation and are not reachable from this workbench.</p>
    </aside>
  </div>

  <script>
    const denySample = {
      action: 'swap',
      mode: 'live_transaction',
      value_eth: 0.05,
      calldata: '0x095ea7b3000000000000000000000000a0b86a33e6776808dc56eb68bb0a0f74ff38ffff',
      requires_signature: true
    };
    const allowSample = {
      action: 'simulate',
      mode: 'simulation',
      value_eth: 0,
      method: 'eth_call',
      requires_signature: false
    };

    function writeJson(id, value){
      document.getElementById(id).textContent = JSON.stringify(value, null, 2);
    }
    function updateDecision(decision){
      const pill = document.getElementById('decision-pill');
      pill.className = 'pill ' + (decision || 'review');
      pill.textContent = decision || 'review';
    }
    async function evaluateIntent(){
      const body = JSON.parse(document.getElementById('intent-input').value);
      const r = await fetch('/api/evaluate', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({intent: body})
      });
      const j = await r.json();
      updateDecision(j.decision);
      writeJson('result-output', j);
    }
    async function hackCheck(){
      const body = JSON.parse(document.getElementById('hack-input').value);
      const r = await fetch('/api/hack-check', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(body)
      });
      const j = await r.json();
      writeJson('result-output', j);
    }
    async function domainCheck(){
      const url = encodeURIComponent(document.getElementById('domain-input').value);
      const r = await fetch('/api/domain?url=' + url);
      const j = await r.json();
      writeJson('result-output', j);
    }
    async function loadContracts(){
      const r = await fetch('/api/external-action-contracts');
      const j = await r.json();
      writeJson('contract-output', j);
    }
    document.getElementById('run-evaluate').addEventListener('click', evaluateIntent);
    document.getElementById('run-hack-check').addEventListener('click', hackCheck);
    document.getElementById('run-domain-check').addEventListener('click', domainCheck);
    document.getElementById('load-deny-sample').addEventListener('click', () => {
      document.getElementById('intent-input').value = JSON.stringify(denySample, null, 2);
    });
    document.getElementById('load-allow-sample').addEventListener('click', () => {
      document.getElementById('intent-input').value = JSON.stringify(allowSample, null, 2);
    });
    loadContracts();
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_DASHBOARD)


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
    app.run(host="127.0.0.1", port=8109, debug=False)


if __name__ == "__main__":
    main()
