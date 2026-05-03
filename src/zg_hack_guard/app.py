"""
Flask API & Dashboard for 0G Hack Guard
========================================
Endpoints:
  GET  /api/health
  GET  /api/catalog
  POST /api/evaluate
  POST /api/hack-check
  GET  /api/domain
"""
from __future__ import annotations

import os
from typing import Any

from flask import Flask, jsonify, request, render_template_string

from zg_hack_guard.policy import evaluate_intent
from zg_hack_guard.crypto_hack_guard import check_crypto_hack_signatures, HackCheckResult
from zg_hack_guard.zg_storage import store_threat_intel, fetch_threat_intel
from zg_hack_guard.zg_chain import anchor_receipt

app = Flask(__name__)

HTML_DASHBOARD = """
<!doctype html>
<html>
<head><title>0G Hack Guard</title>
<style>
  body{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;background:#0b0c10;color:#c5c6c7}
  h1{color:#66fcf1} h2{color:#45a29e}
  .card{background:#1f2833;border-radius:8px;padding:20px;margin:16px 0}
  .badge{display:inline-block;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:700;text-transform:uppercase}
  .allow{background:#2e7d32;color:#fff} .review{background:#f9a825;color:#000}
  .deny{background:#c62828;color:#fff} .critical{background:#ad1457;color:#fff}
  pre{background:#0b0c10;padding:12px;border-radius:6px;overflow-x:auto}
  button{background:#66fcf1;color:#0b0c10;border:none;padding:10px 18px;border-radius:6px;cursor:pointer;font-weight:700}
  textarea{width:100%;background:#1f2833;color:#c5c6c7;border:1px solid #45a29e;border-radius:6px;padding:12px;font-family:monospace}
</style>
</head>
<body>
  <h1>🔒 0G Hack Guard</h1>
  <p>Signature & behavioral detection for crypto hacks — powered by <strong>0G</strong>.</p>
  <div class="card">
    <h2>Evaluate Intent</h2>
    <textarea id="intent" rows="8">{\n  "action": "swap",\n  "mode": "live_transaction",\n  "value_eth": 0.05,\n  "calldata": "0x095ea7b3000000000000000000000000a0b86a33e6776808dc56eb68bb0a0f74ff38ffff",\n  "requires_signature": true\n}</textarea><br><br>
    <button onclick="evaluateIntent()">Evaluate</button>
    <pre id="result"></pre>
  </div>
  <div class="card">
    <h2>Hack Check Only</h2>
    <textarea id="hackintent" rows="6">{\n  "action": "approve",\n  "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"\n}</textarea><br><br>
    <button onclick="hackCheck()">Run Hack Check</button>
    <pre id="hackresult"></pre>
  </div>
  <script>
    async function evaluateIntent(){
      const body = JSON.parse(document.getElementById('intent').value);
      const r = await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({intent:body})});
      const j = await r.json();
      document.getElementById('result').textContent = JSON.stringify(j,null,2);
    }
    async function hackCheck(){
      const body = JSON.parse(document.getElementById('hackintent').value);
      const r = await fetch('/api/hack-check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const j = await r.json();
      document.getElementById('hackresult').textContent = JSON.stringify(j,null,2);
    }
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_DASHBOARD)


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "service": "zg-hack-guard",
        "version": "0.1.0",
        "0g_chain_id": int(os.getenv("ZGG_CHAIN_ID", "16600")),
        "0g_storage_node": os.getenv("ZGS_NODE_URL", "not_configured"),
        "safety_flags": {"read_only": True, "wallet_signatures_blocked": True},
    })


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
    from zg_hack_guard.policy import normalize_intent
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
    return jsonify({
        "url": url,
        "decision": "allow" if is_allowed else "review",
        "reasons": [] if is_allowed else ["Domain not in curated allowlist"],
    })


def main() -> None:
    app.run(host="127.0.0.1", port=8109, debug=False)


if __name__ == "__main__":
    main()
