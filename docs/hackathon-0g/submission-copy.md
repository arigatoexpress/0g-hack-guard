# 0guard HackQuest Submission Copy

## Project Name

0guard

## Recommended Track

Primary: Track 5 - Privacy & Sovereign Infrastructure.

Secondary: Track 1 - Agentic Infrastructure & OpenClaw Lab.

Track 5 is the cleaner judge story because 0guard is a pre-wallet security,
provenance, and receipt-infrastructure layer for autonomous agents.

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
- A rights-aware OSINT registry and live signal route for public incident and
  research metadata.
- A provenance matrix that correlates canonical incidents against live public
  source records without exposing raw upstream payloads, plus a reviewed
  derived-evidence cache for offline judge demos. The canonical dataset now has
  per-incident source evidence for all 28 records; the remaining detector gap
  is the intentionally unpromoted `Quant` row, whose public root-cause naming is
  still ambiguous.
- A signature map that explains detector coverage gaps and recommended rule
  additions.
- 0G read-only network proof through `/api/0g/status`.
- 0G mainnet `PolicyReceiptAnchor` proof with one anchored deny receipt.
- 0G Chain receipt-anchor preflight payloads from the browser workbench.
- 0G Storage threat-intel payload/root-hash receipts.
- A cross-chain integration fabric for Virtuals/Base, x402 payment lanes,
  Arbitrum, Polygon, MegaETH, Monad, HyperEVM, Tempo, Lighter exchange/API
  guardrails, Chainlink CCIP, LayerZero V2, Wormhole NTT, and Celestia/TIA data
  availability, exposed as read-only catalog/readiness APIs.
- A prepared `0guard Facilitator` manifest for future Virtuals/Base deployment;
  live launch, token, payment, bridge, and swap actions stay operator-only.
- Telegram Mira opt-in and preview primitives that never send messages from the
  judge workbench.

## Required HackQuest Materials Status

- Project info: submitted and publicly verified.
- Copy/paste form packet: ready at
  `docs/hackathon-0g/submission-form-fields.md` and
  `/api/hackathon/submission-packet`.
- Public GitHub repository: ready at `https://github.com/arigatoexpress/0guard`.
- README and technical documentation: ready, with remaining Storage/Compute gaps stated openly.
- Demo video: ready at
  `https://arigatoexpress.github.io/0guard/hackathon-0g/assets/0guard-hackquest-demo-final.mp4`.
- Public X post: submitted proof URL is
  `https://x.com/rariwrldd/status/2054779961425461542`. Refreshed single-post
  and thread drafts remain available at `content/hackquest_x_post.json` and
  `content/hack_guard_thread.json` for any follow-up launch posts.
- 0G proof: live read-only status, receipt preflight, and mainnet receipt
  anchor proof are ready. Use `docs/hackathon-0g/mainnet-proof.json`, the
  contract URL, and the anchor transaction URL in the HackQuest form.

## 0G Integration

### 0G Chain

The workbench reads 0G state live and prepares policy receipt anchor payloads
for `PolicyReceiptAnchor.sol`. A dedicated deployer has also anchored one deny
receipt on 0G mainnet so judges can inspect a public, tamper-evident audit
trail.

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
6. `/api/0g/status` proves the app can read 0G live without a key,
   signing, or broadcast.

The demo shows both the safe workbench round-trip and the public mainnet anchor
proof. The browser path intentionally labels its local anchor payload as
`preflight`, while the Explorer link proves the corresponding receipt was
anchored on 0G mainnet by the dedicated deployer.

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
   Then show `docs/hackathon-0g/mainnet-proof.json` and the 0G Explorer anchor
   transaction.
7. Show `/api/data/detection-coverage` to prove the incident dataset is wired
   through the detector rather than pasted into marketing copy.
8. Show `/api/data/provenance?live=1` to prove incidents can be correlated
   against live public source records with confidence and record hashes.
9. Show `/api/osint/sources` or `/api/osint/signals?live=1&limit=10` to prove
   the OSINT pipeline has source owners, rights caveats, links, and hashes.
10. Show `/api/integrations/cross-chain` and
    `/api/integrations/virtuals-facilitator` to prove the Base/Virtuals/x402
    expansion path is prepared without claiming live settlement or launch.
11. Show Telegram Mira preview only as a no-send opt-in surface.

## Why This Can Win

- It is legible in under three minutes: AI agent intent goes in, safety verdict
  and 0G proof receipts come out.
- It uses 0G as infrastructure, not branding: Chain for audit, Storage for
  threat intel, Compute for the next scoring layer.
- It is honest about safety: no keys in the workbench, no fake trading bot,
  and mainnet writes limited to the documented receipt anchor.
- It is grounded in real exploit patterns, so judges do not have to imagine the
  risk.
- It turns open-source intelligence into a source-cited data product, not a
  screenshot or one-off scrape.
- It shows how 0guard can become a cross-chain agent safety/payment layer:
  x402 for paid derived artifacts, Virtuals/Base for agent distribution,
  Lighter exchange/API protection for pre-trade guardrails, bridge-protocol
  checks for CCIP/LayerZero/Wormhole-style intents, and 0G for proof anchoring.
- It leaves a clear production path: enable live Storage writes, add runtime
  verifier config/readback, then productionize the compute scorer.

## Mainnet Honesty Statement

This submission keeps the browser workbench safe/read-only and preflight by
design. It does not hold keys, sign transactions, broadcast 0G writes, move
funds, or claim production custody from the workbench. The mainnet receipt
anchor proof is complete; the remaining production gaps are live 0G Storage
uploads/readbacks, hardened signer custody outside the workbench, and a
contract-level verifier readback in the deployed runtime.
