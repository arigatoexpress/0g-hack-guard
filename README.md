# 🔒 0G Hack Guard

> **AI Agent Firewall + Signature/Behavioral Detection for Crypto Hacks**  
> Built on [0G](https://0g.ai) — the first decentralized AI operating system.

[![CI](https://github.com/arigatoexpress/0g-hack-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/arigatoexpress/0g-hack-guard/actions)

---

## One-Sentence Pitch

0G Hack Guard is a read-only, pre-wallet safety layer that uses real exploit signatures from April 2026 (the worst month on record for DeFi hacks) to detect and block crypto hacks before an AI agent ever reaches a signing key.

---

## Problem

- **April 2026 saw $635M+ stolen across 28 DeFi/DEX incidents** — the worst month on record.
- **76% of losses were attributed to North Korea's Lazarus Group** using social engineering, bridge misconfiguration, and admin-key compromise.
- **The two largest exploits involved zero smart-contract bugs**; they were pure operational-security failures.
- AI agents operating on fast L1s/L2s can make wallet mistakes *instantly* — there is no pre-flight safety layer designed specifically for autonomous agents.

## Solution

0G Hack Guard gives every AI agent a **pre-wallet security copilot**:

1. **Intent Firewall** — Evaluates every action as `allow`, `review`, or `deny` before it reaches a wallet.
2. **Hack Signature Detection** — Built-in IOCs, calldata selectors, and behavioral sequences derived from **real April 2026 exploits** (Drift, Kelp DAO, Wasabi, Rhea, Volo, Giddy, HyperBridge, Aftermath, Sweat Foundation).
3. **0G-Native Persistence** — Anchors policy receipts on **0G Chain** and persists threat intel to **0G Storage** for censorship-resistant, federated defense.
4. **Zero Trust by Default** — Refuses signing, raw transactions, bridges, swaps, and approvals unless explicitly cleared.

---

## 0G Integration

| 0G Component | How We Use It | Hackathon Track Fit |
|---|---|---|
| **0G Chain** (EVM-compatible) | Anchors SHA-256 policy receipt hashes on-chain for tamper-evident audit trails. | Agentic Infrastructure |
| **0G Storage** (KV + Log) | Persists threat-intel signatures, IOCs, and incident receipts at ultra-low cost. | Privacy & Sovereign Infrastructure |
| **0G Compute** (Inference) | Pluggable AI inference layer for behavioral anomaly detection on agent prompts. | Agentic Infrastructure |
| **Agent ID** (ERC-7857) | Every evaluation is tagged with a persistent agent identity for accountability. | Agentic Economy |

### Smart Contract

`contracts/PolicyReceiptAnchor.sol` — A minimal 0G Chain contract that stores `(receipt_hash, decision, severity, agent_id, timestamp)` events. Fully auditable and queryable via 0G Explorer.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Agent      │────▶│  0G Hack Guard   │────▶│  Wallet / RPC   │
│  (OpenClaw,     │     │  (Intent Eval)   │     │  (only if allow)│
│   LangChain)    │     └──────────────────┘     └─────────────────┘
└─────────────────┘              │
                                 ▼
              ┌──────────────────────────────────────┐
              │  Crypto Hack Guard (Signatures)      │
              │  • IOC blocklist (Lazarus wallets)   │
              │  • Selector analysis (approve,       │
              │    upgradeTo, grantRole, lzReceive)  │
              │  • Behavioral sequences (flash-loan  │
              │    → swap → withdraw)                │
              │  • Social-engineering language       │
              └──────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
         0G Chain         0G Storage          0G Compute
    (Receipt Anchor)   (Threat Intel KV)   (AI Anomaly Model)
```

---

## Quickstart

```bash
git clone https://github.com/arigatoexpress/0g-hack-guard.git
cd 0g-hack-guard
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m zg_hack_guard.app
```

Open `http://127.0.0.1:8109` for the dashboard.

---

## CLI

```bash
# Evaluate an intent
python3 -m zg_hack_guard.cli evaluate \
  --intent-json '{"action":"swap","mode":"live_transaction","value_eth":0.05,"requires_signature":true}'

# Run hack-signature check only
python3 -m zg_hack_guard.cli hack-check \
  --intent-json '{"action":"approve","calldata":"0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}'

# Start API server
python3 -m zg_hack_guard.cli serve --port 8109
```

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/api/health` | Service health + 0G config |
| `POST` | `/api/evaluate` | Full intent evaluation |
| `POST` | `/api/hack-check` | Hack signature check only |
| `GET`  | `/api/domain?url=...` | Domain allowlist check |

### Example: Evaluate Intent

```bash
curl -X POST http://127.0.0.1:8109/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {
      "action": "approve",
      "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "mode": "live_transaction",
      "requires_signature": true
    },
    "enable_0g_storage": true,
    "agent_id": "agent-7857-0xabc..."
  }'
```

**Response:**
```json
{
  "decision": "deny",
  "severity": "high",
  "action": "approve",
  "mode": "live_transaction",
  "blockers": [
    "Unlimited ERC-20 approval (max uint256) detected.",
    "Intent requires a wallet signature in non-simulation mode."
  ],
  "warnings": [],
  "receipt_hash": "a1b2c3...",
  "generated_at": "2026-05-03T17:45:00+00:00"
}
```

---

## Real-World Signatures Built-In

| April 2026 Incident | Signature in 0G Hack Guard |
|---|---|
| **Drift Protocol** ($285M) — Durable nonce social engineering | `durable_nonce_admin_transfer` blocker |
| **Kelp DAO** ($293M) — LayerZero 1-of-1 DVN bridge forgery | `single_dvn_bridge` warning |
| **Wasabi Protocol** ($5M) — UUPS upgrade via compromised deployer | `sequence_grant_upgrade` blocker |
| **Rhea Finance** ($18.4M) — Flash-loan + fake collateral | `sequence_flash_swap_withdraw` warning |
| **Giddy Finance** ($1.3M) — EIP-712 signature replay | `critical_selector` on malformed `approve` |
| **HyperBridge** ($2.5M) — MMR proof replay | `lzReceive` critical selector flag |
| **Aftermath Perps** ($1.14M) — Signedness mismatch | `high_value` + `risk_pair` warnings |
| **Sweat Foundation** ($3.5M) — Refund logic drain | `drain_language` blocker |
| **Volo Protocol** ($3.5M) — Admin key leak | `grantRole`/`transferOwnership` critical flags |

---

## Tests

```bash
pytest -q
python3 -m compileall src scripts
ruff check src tests scripts
gitleaks detect --no-git --source . --redact --verbose
```

---

## Safety Boundary

- **No private keys** in this repo.
- **No transaction signing** or broadcasting.
- **No real fund movements** — read-only and evaluative only.
- Live mode calls public HTTP endpoints and read-only RPC methods.

---

## Roadmap

1. ✅ Signature/behavioral detection for April 2026 exploits
2. ✅ 0G Chain receipt anchoring
3. ✅ 0G Storage threat-intel persistence
4. 🔄 Real-time mempool monitoring via 0G DA subscription
5. 🔄 TEE-sealed inference for private risk scoring
6. 🔄 On-chain bounty program for community-submitted signatures

---

## Team

- **Security / Engineering** — Sapphire Security
- **Product / Strategy** — arigatoexpress

---

## Links

- **Hackathon:** [0G APAC Hackathon on HackQuest](https://hackquest.io/en/hackathons/0G-APAC-Hackathon)
- **0G Docs:** [docs.0g.ai](https://docs.0g.ai)
- **0G Explorer:** [chainscan.0g.ai](https://chainscan.0g.ai)
- **Twitter/X:** `#0GHackathon` `#BuildOn0G`

---

## License

MIT — see [LICENSE](LICENSE).
