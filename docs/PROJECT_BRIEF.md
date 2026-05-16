# 0guard Project Brief

0guard is a pre-wallet firewall for AI agents. In normal language: an agent
asks to do something, 0guard checks the intent before a wallet prompt appears,
and risky signing paths stop before the signer is touched.

## What Is Live

- A Flask API and browser workbench for allow/review/deny evaluations.
- A live Telegram Mini App at `https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram`.
- A live Telegram bot at `https://t.me/Raris0guardBot` with outbound sends disabled.
- A public proof hub at `https://arigatoexpress.github.io/0guard/hackathon-0g/`.
- A 0G mainnet receipt anchor recorded in the hackathon proof packet.
- A source-linked incident dataset with full detector coverage for the current corpus.
- A native preflight developer kit for wallets, agents, x402 flows, Telegram/TON, and Ika/dWallet-style signing systems.

## What The System Does

1. Reads an agent or app intent before wallet access.
2. Checks policy, calldata, prompt text, domains, counterparties, labels, and source evidence.
3. Compares the action with source-linked exploit patterns and local indicators.
4. Returns `allow`, `review`, or `deny`.
5. Produces deterministic receipts that are ready for 0G Chain / 0G Storage workflows.
6. Shows human-readable Telegram/Mira/wallet explanations without sending messages or moving funds.

## Why It Matters

Most wallet safety tools show up when a signature is already on screen. 0guard
moves the checkpoint earlier, where AI agents form actions. That makes it useful
for wallets, agent frameworks, Telegram Mini Apps, dWallet/MPC systems, CI
deployment gates, and x402-style paid APIs.

## Current Product Surfaces

| Surface | Route / artifact | Status |
|---|---|---|
| Product brief | `/api/product/brief` | Live |
| Threat case file | `/api/threat-case-file` | Live preview, no side effects |
| Frontier experiment lab | `/api/experiments/frontier`, `/api/experiments/run` | Live read-only |
| Native preflight | `/api/native-preflight` | Live |
| Reputation probe | `/api/reputation/probe` | Live, local/derived |
| Reputation connector manifest | `/api/reputation/connectors` | Live, no external calls |
| Developer kit | `/api/developer-kit` | Live |
| Telegram Mini App | `/telegram` | Live preview, no sends |
| TON risk passport | `/api/ton/wallet-risk-preview` | Live preview, no wallet prompts |
| Ika/Ikavery preflight | `/api/integrations/ika/evaluate` | Live preview, no signing |
| External guardrails | `/api/integrations/external-guardrails/evaluate` | Live read-only |
| Submission proof | `docs/hackathon-0g/` | Public Pages artifact |

## Honest Limits

- External GoPlus, Chainabuse, Forta, TONAPI, Tenderly, and BlockSec feeds are
  activation-ready but disabled until credentials, terms, and retention rules
  are reviewed.
- The Mini App and bot are live, but outbound Telegram sends are disabled.
- 0guard does not sign transactions, broadcast transactions, bridge, swap,
  settle x402 payments, create wallets, import keys, or place exchange orders.
- Social posting is prepared as reviewed content and dry-run tooling unless an
  operator-controlled posting path is explicitly used.

## Next Best Builds

1. Use the threat case file as the default judge/operator walkthrough: one
   risky intent, one verdict, one evidence packet, one 0G-ready receipt.
2. Enable one external reputation connector first, likely GoPlus or Chainabuse,
   behind credentials and derived-output tests.
3. Add operator-approved 0G Storage upload/readback for receipt payloads.
4. Add EVM simulation summaries from Tenderly or BlockSec.
5. Deepen Telegram/TON with read-only TON Center or TONAPI account context.
