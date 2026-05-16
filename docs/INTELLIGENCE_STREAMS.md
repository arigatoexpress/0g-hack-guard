# 0guard Intelligence Stream Plan

This is the current build order for making 0guard evolve beyond the April 2026
incident dataset without pretending raw feeds are ours to resell.

## Priority Streams

| Phase | Stream | Why | Integration | Rights posture |
|---|---|---|---|---|
| 1 | GoPlus + Chainabuse + CryptoScamDB / Scam Sniffer / MetaMask phishing feeds | Highest near-term value for address, token, approval, dApp, and domain risk. | The live `/api/reputation/probe` contract now feeds `/api/native-preflight`, wallet alerts, and Telegram previews; `/api/reputation/adapters/normalize` converts reviewed upstream payloads into derived evidence. External live fetches stay disabled until keys/terms are reviewed. | Derived verdicts, links, hashes, source ids, and confidence only. |
| 1 | Forta labels and attack alerts | Emerging exploit-stage intelligence before it becomes a hard blocker. | Digest-only queue using Forta alert/label metadata; promote to wallet alert only with direct detector/source evidence. | Respect public label attribution and any premium feed terms. |
| 2 | Tenderly or BlockSec simulation | Adds state-change previews for approvals, swaps, and contract calls. | Optional `simulate_intent` adapter returning asset deltas and dangerous calls. | Do not persist/resell full traces unless vendor terms allow it. |
| 2 | TON Center / TONAPI | Makes Telegram wallet alerts native to TON instead of EVM-shaped. | TON account, transaction, Jetton, NFT, and message activity enrichment for risk passports. | Derived activity features only; no raw indexer dumps. |
| 2 | Helius Solana | Adds Solana read-only account/token risk without making a bridge story. | Parsed transaction and SPL-token watchlists feeding alert quality gates. | Vendor terms; derived features and links only. |
| 2 | LayerZero Scan / Wormholescan | Lets 0guard protect cross-chain message risk without initiating transfers. | Read message state, DVN config, VAA status, and stuck-message context. | Derived message metadata only. |
| 3 | Hyperliquid Info/WebSocket APIs | Useful for exposure and fill context while avoiding exchange actions. | Read-only exposure monitor; no order, cancel, transfer, or withdrawal endpoints. | Market context only, not advice or execution. |
| 3 | Dune, Allium, or Bitquery | Backfills behavior features across chains when native adapters are not enough. | Nightly feature store for fan-out, mixer proximity, and new-contract exposure. | Paid terms vary; sell derived features, not raw query exports. |

## What To Buy First

1. GoPlus or Chainabuse only after free/keyed access materially improves alert
   quality or the demo hits rate limits.
2. Tenderly or BlockSec simulation once the reputation adapter is already used
   by real product flows.
3. Dune, Allium, or Bitquery only when native adapters cannot cover a chain or
   historical feature quickly enough.

## Current API Proof

- `/api/intelligence/data-streams` exposes this as a source-rights-aware JSON
  roadmap.
- `/api/experiments/frontier` turns the roadmap into a ranked lab bench for 0G
  Storage/Compute, reputation, simulation, TON, and Mira.
- `/api/experiments/run` previews one experiment at a time and always reports
  `networkCalls: false`, `liveStorageUpload: false`,
  `liveComputeInference: false`, and `rawPayloadsReturned: false`.
- `/api/osint/sources` now includes the planned stream metadata and keeps those
  adapters disabled by default until terms, keys, and retention rules are clear.
- `/api/reputation/probe` is the first live adapter contract. It accepts local
  or caller-supplied evidence and returns only derived signals, hashes,
  redactions, confidence, and receipt metadata.
- `/api/reputation/connectors` turns the source registry into an activation
  manifest for the subject being checked. It does not call external networks;
  it tells an integrator which GoPlus, Chainabuse, Forta, TON, simulation, or
  cross-chain connector applies and what rights boundary must be preserved.
- `/api/reputation/adapters` and `/api/reputation/adapters/normalize` are the
  first no-network adapter contracts for GoPlus, Chainabuse, and Forta. They
  accept caller-provided payloads from a reviewed worker, return only derived
  evidence, and feed the threat case file plus wallet/Telegram previews.
