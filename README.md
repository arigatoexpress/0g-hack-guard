# 🔒 0guard

> **AI Agent Firewall + Signature/Behavioral Detection for Crypto Hacks**  
> Built on [0G](https://0g.ai) — the first decentralized AI operating system.

[![CI](https://github.com/arigatoexpress/0guard/actions/workflows/ci.yml/badge.svg)](https://github.com/arigatoexpress/0guard/actions)

---

## One-Sentence Pitch

0guard is a read-only, pre-wallet safety layer that uses real exploit signatures from April 2026 (the worst month on record for DeFi hacks) to detect and block crypto hacks before an AI agent ever reaches a signing key.

---

## Problem

- **April 2026 saw $635M+ stolen across 28 DeFi/DEX incidents** — the worst month on record.
- **76% of losses were attributed to North Korea's Lazarus Group** using social engineering, bridge misconfiguration, and admin-key compromise.
- **The two largest exploits involved zero smart-contract bugs**; they were pure operational-security failures.
- AI agents operating on fast L1s/L2s can make wallet mistakes *instantly* — there is no pre-flight safety layer designed specifically for autonomous agents.

## Solution

0guard gives every AI agent a **pre-wallet security copilot**:

1. **Intent Firewall** — Evaluates every action as `allow`, `review`, or `deny` before it reaches a wallet.
2. **Hack Signature Detection** — Built-in IOCs, calldata selectors, and behavioral sequences derived from **real April 2026 exploits** (Drift, Kelp DAO, Wasabi, Rhea, Volo, Giddy, HyperBridge, Aftermath, Sweat Foundation).
3. **0G-Native Proofs** — Reads live 0G Galileo RPC status, prepares policy receipt hashes, and keeps chain/storage writes operator-controlled.
4. **Telegram Mira Opt-In** — Provides secure Telegram Mini App registration primitives and Mira response previews without live sends.
5. **Zero Trust by Default** — Refuses signing, raw transactions, bridges, swaps, and approvals unless explicitly cleared.

---

## 0G Integration

| 0G Component | How We Use It | Hackathon Track Fit |
|---|---|---|
| **0G Chain** (EVM-compatible) | Live read-only Galileo RPC proof today; operator-deployed receipt anchor contract when configured. | Agentic Infrastructure |
| **0G Storage** (KV + Log) | Deterministic threat-intel payload/root-hash preparation; external writes stay opt-in. | Privacy & Sovereign Infrastructure |
| **0G Compute** (Inference) | Pluggable AI inference layer for behavioral anomaly detection on agent prompts. | Agentic Infrastructure |
| **Agent ID** (ERC-7857) | Every evaluation is tagged with a persistent agent identity for accountability. | Agentic Economy |

### Smart Contract

`contracts/PolicyReceiptAnchor.sol` — A minimal 0G Chain contract that stores `(receipt_hash, decision, severity, agent_id, timestamp)` events. Fully auditable and queryable via 0G Explorer.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Agent      │────▶│  0guard   │────▶│  Wallet / RPC   │
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
git clone https://github.com/arigatoexpress/0guard.git
cd 0guard
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
python3 -m guard0.app
```

Open `http://127.0.0.1:8109` for the dashboard.

---

## CLI

```bash
# Evaluate an intent
python3 -m guard0.cli evaluate \
  --intent-json '{"action":"swap","mode":"live_transaction","value_eth":0.05,"requires_signature":true}'

# Run hack-signature check only
python3 -m guard0.cli hack-check \
  --intent-json '{"action":"approve","calldata":"0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}'

# Start API server
python3 -m guard0.cli serve --port 8109
```

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/api/health` | Service health + 0G config |
| `GET`  | `/api/0g/status` | Live read-only 0G Galileo RPC proof, chain ID, latest block, and receipt-anchor config |
| `GET`  | `/api/data/summary` | Validated incident dataset summary, aggregate stats, and dataset fingerprint |
| `GET`  | `/api/data/incidents` | Filterable public incident records by chain, vector, loss, and limit |
| `GET`  | `/api/data/detection-coverage` | Runs incident-derived seeds through the signature engine and reports coverage |
| `GET`  | `/api/telegram/status` | Telegram/Mira registration posture, Mini App auth support, and no-send safety flags |
| `POST` | `/api/telegram/registrations` | Create a local HMAC registration challenge; no Telegram send |
| `POST` | `/api/telegram/opt-ins` | Complete a local redacted Telegram opt-in record from a verified challenge |
| `POST` | `/api/telegram/webapp/verify` | Validate Telegram Mini App `initData` server-side when `TELEGRAM_BOT_TOKEN` is configured |
| `POST` | `/api/telegram/webhook` | Inbound `/start`, `/stop`, and Mira preview handling with Telegram secret-header verification; no send |
| `POST` | `/api/telegram/mira-preview` | Build a Telegram-safe Mira security response preview; no send |
| `GET`  | `/api/frontend-contract` | Browser smoke contract, selectors, and safety posture |
| `GET`  | `/api/external-action-contracts` | Dry-run/default contract for X, Telegram, deploy, and signing paths |
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
  "zero_g": {
    "chain_anchor": {
      "status": "preflight",
      "chain_id": 16602
    },
    "storage_receipt": {
      "stored": true,
      "root_hash": "..."
    }
  },
  "generated_at": "2026-05-03T17:45:00+00:00"
}
```

Check live 0G RPC proof without any private key:

```bash
curl -s http://127.0.0.1:8109/api/0g/status | python3 -m json.tool
```

### Incident Data Flow

The incident dataset is loaded from `data/april_2026_incidents.json`, validated
against a required schema, fingerprinted, summarized, and run through the
signature engine as detection-coverage seeds.

```bash
curl -s http://127.0.0.1:8109/api/data/summary | python3 -m json.tool
curl -s http://127.0.0.1:8109/api/data/detection-coverage | python3 -m json.tool
```

The validator fails on bad totals, duplicate IDs, malformed dates, missing
required fields, or invalid losses. It also reports provenance warnings when
records lack per-incident source URLs.

### Telegram Mira Opt-In Preview

Create a local registration challenge, complete a redacted opt-in record, and
build a Mira response preview. These calls do not contact Telegram or send any
message.

```bash
curl -s -X POST http://127.0.0.1:8109/api/telegram/registrations \
  -H "Content-Type: application/json" \
  -d '{"user_label":"demo-operator","scopes":["mira_alerts","security.digest"]}' \
  | python3 -m json.tool

curl -s http://127.0.0.1:8109/api/telegram/status | python3 -m json.tool
```

For a real Telegram Mini App, send `window.Telegram.WebApp.initData` to
`/api/telegram/webapp/verify`; the backend validates Telegram's signed init
data with `TELEGRAM_BOT_TOKEN` before trusting user identity.

See also:
- `docs/DATA_FLOWS.md`
- `docs/TELEGRAM_MIRA_INTEGRATION.md`
- `docs/MARKET_POSITIONING.md`

---

## Real-World Signatures Built-In

| April 2026 Incident | Signature in 0guard |
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
python3 scripts/browser_smoke.py
gitleaks detect --no-git --source . --redact --verbose
```

---

## Safety Boundary

- **No private keys** in this repo.
- **No transaction signing** or broadcasting.
- **No real fund movements** — read-only and evaluative only.
- Live mode calls public HTTP endpoints and read-only RPC methods.
- X and Telegram posting CLIs default to dry-run unless the operator supplies
  the exact live confirmation flag.
- Telegram/Mira registration and preview routes are local-only by default:
  they validate tokens, redact identifiers, and never send Telegram messages.
- The browser workbench cannot trigger external sends, deploys, signatures, or
  transaction broadcasts.

---

## Roadmap

1. ✅ Signature/behavioral detection for April 2026 exploits
2. ✅ Live read-only 0G Galileo proof + receipt-anchor preflight
3. ✅ 0G Storage threat-intel payload/root-hash preparation
4. ✅ Telegram Mira secure registration primitives and no-send preview
5. 🔄 Persistent Telegram opt-in registry behind admin auth
6. 🔄 Real-time mempool monitoring via 0G DA subscription
7. 🔄 TEE-sealed inference for private risk scoring
8. 🔄 On-chain bounty program for community-submitted signatures

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
