# Local Inference, x402, and Historical Backfill

This document is the operator map for weaving local Windows/Pi inference, x402
data products, and historical data backfill into ZeroGuard without weakening the
safety boundary.

## Current Architecture

| Layer | Route | Status |
| --- | --- | --- |
| Local inference mesh | `/api/local-inference/status` | Read-only live probe when `?live=1`; no prompts. |
| Telegram digest | `/api/telegram/local-inference-preview` | Preview-only message body; no Telegram send. |
| x402 data products | `/api/x402/data-products` | Product manifest only; no 402 settlement. |
| Historical backfill | `/api/data/backfill-plan` | Backfill schema and source plan; no live fetch. |

The Windows machine is treated as the future heavy local inference host. The
Raspberry Pis are treated as sentinels and proof caches, not key holders. The
0G Private Computer path remains the attested external inference layer for
sensitive summaries after an operator-funded server-side key exists.

## Telegram Bridge Shape

The Telegram bot should call ZeroGuard routes in this order:

1. Deterministic status and policy routes first.
2. Local inference mesh status second.
3. A model summary only after a local model is loaded and the prompt is scrubbed.
4. 0G Private Computer only after Router funding, API-key storage, and prompt
   minimization are reviewed.

Allowed Telegram command ideas:

| Command | Backend | Sends? |
| --- | --- | --- |
| `/zg systems` | `/api/local-inference/status?live=1` | Preview only today. |
| `/zg node` | `/api/0g/storage-node/status?snapshot=1` | Preview only today. |
| `/zg risk <address-or-url>` | deterministic reputation/policy routes | Preview only today. |

No route in this repo sends Telegram messages, signs wallet transactions,
broadcasts onchain messages, or executes paid inference from the browser.

## x402 Product Wedge

x402 is useful because it makes defensive intelligence accessible to agents over
ordinary HTTP: a buyer requests a protected route, the server can respond with
`402 Payment Required`, and payment metadata can be settled through a
facilitator. For ZeroGuard, the sellable unit is derived defensive analysis:

| Product | Why someone pays | Raw resale? |
| --- | --- | --- |
| Wallet preflight verdict | Agents can check before requesting a signature. | No |
| Threat packet summary | Wallets get a source-cited explanation. | No |
| Node health snapshot | 0G operators get sync/peer blocker snapshots. | No |
| Reputation shadow digest | Telegram/wallet surfaces get deduped risk features. | No |
| Historical incident features | Builders get pattern features, not raw archives. | No |

Preparation order:

1. Keep `/api/x402/data-products` as a manifest.
2. Add a dry-run protected route that returns fixture 402 metadata.
3. Add MetaMask Smart Account / ERC-7710 permission checks for bounded access.
4. Add 1Shot or CDP facilitator testing on testnet after spend limits are fixed.
5. Only then enable mainnet settlement for a single low-cost route.

Sources:

- https://docs.cdp.coinbase.com/x402/welcome
- https://docs.cdp.coinbase.com/x402/network-support
- https://docs.cdp.coinbase.com/x402/bazaar
- https://www.x402.org/

## Backfill Policy

Backfill is how ZeroGuard becomes durable instead of ephemeral. The priority is
historical incident and reputation data first, then node telemetry, then redacted
Telegram opt-in metadata, then future x402 receipts.

Rules:

- Store derived features, source ids, source URLs, timestamps, and hashes.
- Do not store private keys, mnemonics, raw Telegram chats, payment headers, or
  raw paid-feed payloads.
- Keep each backfill run append-only and fingerprinted.
- Separate public-safe artifacts from operator-only local snapshots.
- Put every paid or licensed source behind a rights envelope before it can affect
  a product route.

The current schema is exposed by `/api/data/backfill-plan`; implementation should
start with append-only JSONL, then graduate to DuckDB or SQLite when query volume
justifies it.
