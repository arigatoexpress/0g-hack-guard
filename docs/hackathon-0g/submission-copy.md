# 0guard HackQuest Submission Copy

## Project Name

0guard

## One-Sentence Description

0guard is a 0G-native pre-wallet firewall that checks AI-agent intents against
real crypto-hack signatures, returns allow/review/deny verdicts, and prepares
tamper-evident 0G receipt proofs before any signer can act.

## Short Description

AI agents are gaining wallets, bridge access, and transaction tooling faster
than their safety controls are maturing. 0guard sits before the wallet. It
inspects an agent's prompt, action mode, calldata, target contract, domain, and
policy context, then produces an explainable `allow`, `review`, or `deny`
decision with a SHA-256 receipt hash.

For the hackathon demo, 0guard uses real April 2026 exploit patterns as the
judge-comprehensible test set: durable-nonce social engineering, single-DVN
bridge forgery, compromised-deployer UUPS upgrades, flash-loan collateral
manipulation, signature replay, and replayable cross-chain messages. The point
is simple: before an autonomous agent signs, 0guard can stop the class of
mistake that human teams already lost money to.

## What We Built

- A browser workbench for evaluating AI-agent intents before wallet access.
- A Python policy engine that emits deterministic allow/review/deny decisions.
- Signature and behavior checks based on April 2026 crypto incident patterns.
- A validated incident dataset with summary, filtering, fingerprint, and
  detection-coverage API readbacks.
- 0G Galileo read-only network proof through `/api/0g/status`.
- 0G Chain receipt-anchor preflight payloads for `PolicyReceiptAnchor.sol`.
- 0G Storage threat-intel payload/root-hash receipts.
- Telegram Mira opt-in and preview primitives that never send messages from the
  judge workbench.

## 0G Integration

### 0G Chain

The workbench reads Galileo testnet live and prepares policy receipt anchor
payloads for `PolicyReceiptAnchor.sol`. Agent decisions need public,
tamper-evident audit trails.

### 0G Storage

The policy path serializes threat-intel receipts and computes deterministic root
hashes for Storage-ready payloads. Agents need portable, queryable security
memory across runtimes.

### 0G Compute

The architecture reserves the inference layer for behavioral anomaly scoring
alongside deterministic policy checks. Risk scoring should move closer to
decentralized AI infrastructure, not stay trapped in one backend.

### Agent Identity

Evaluation receipts include `agent_id` so verdicts can be tied to an
accountable agent session. Audits need to know which agent attempted which
action and why it was allowed or blocked.

## Verifier Round-Trip

The submission demonstrates the verifier loop in a safe, judge-reviewable form:

1. Submit an intent to `/api/evaluate`.
2. 0guard evaluates signatures, calldata, mode, and policy context.
3. The policy engine returns a verdict plus a deterministic `receipt_hash`.
4. With `enable_0g_anchor=true`, the response includes the exact 0G Chain
   anchor payload in `zero_g.chain_anchor`.
5. With `enable_0g_storage=true`, matching threat intel returns a canonical
   Storage receipt with `root_hash`, `key`, and payload size.
6. `/api/0g/status` proves the app can read 0G Galileo live without a key,
   signing, or broadcast.

The production verifier still needs a deployed receipt contract plus live
contract readback before we claim on-chain verification is complete. The demo
shows the round-trip shape and intentionally labels the current anchor status as
`preflight` until that operator step is complete.

## Demo Script for Judges

1. Show the dashboard and explain the pre-wallet position: no signer yet.
2. Paste the Drift-style durable-nonce prompt. The verdict should be `deny`.
3. Paste the Kelp-style single-DVN bridge prompt/calldata. The verdict should
   surface bridge/verifier risk.
4. Paste the Wasabi-style upgrade intent. The verdict should flag upgrade/admin
   risk and known malicious contract context.
5. Run `/api/0g/status` and zoom into `readMode`, `observedChainId`,
   `latestBlockNumber`, and `signingEnabled: false`.
6. Run `/api/evaluate` with both 0G flags enabled and show
   `zero_g.chain_anchor.status: preflight` plus the Storage `root_hash`.
7. Show `/api/data/detection-coverage` to prove the incident dataset is wired
   through the detector rather than pasted into marketing copy.
8. Show Telegram Mira preview only as a no-send opt-in surface.

## Why This Can Win

- It is legible in under three minutes: AI agent intent goes in, safety verdict
  and 0G proof receipts come out.
- It uses 0G as infrastructure, not branding: Chain for audit, Storage for
  threat intel, Compute for the next scoring layer.
- It is honest about safety: no keys, no live writes, no fake trading bot.
- It is grounded in real exploit patterns, so judges do not have to imagine the
  risk.
- It leaves a clear mainnet path: deploy receipt anchor, enable live Storage
  writes, add verifier readback, then productionize the compute scorer.

## Mainnet Honesty Statement

This submission is testnet/read-only and preflight by design. It does not sign
transactions, broadcast 0G writes, move funds, or claim production mainnet
coverage. The mainnet gap is explicit: deploy and verify the receipt anchor,
wire live 0G Storage uploads/readbacks, harden key custody outside the workbench,
and add a contract-level verifier readback before any production launch.
