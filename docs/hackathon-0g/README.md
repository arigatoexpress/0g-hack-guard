# 0G Hackathon Submission Pack

This folder is the judge-facing copy pack for the 0guard 0G hackathon
submission. It is intentionally written from the live demo posture: read-only
0G RPC proof in the workbench, deterministic receipts, public mainnet anchoring
proof, and no private keys or real writes in the workbench.

## Recommended Judge Path

Submitted public project: https://www.hackquest.io/projects/0guard

Submission proof artifact: `hackquest-submission-proof.json`

Live Telegram Mini App preview:
https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram

1. Start with `final-submission-checklist.md` for the submitted HackQuest
   readback, public project URL, 0G proof, demo video, and X post.
2. Use `submission-copy.md` for the project summary, track fit, and
   field-ready HackQuest copy.
3. Use `final-demo-video-script.md` as the reproducible source script for the
   generated public MP4, and `ai-submission-production-package.md` if a later
   Veo/Gemini-enhanced cut is desired.
4. Use `demo-judge-walkthrough.md` while recording or presenting the live demo.
5. Use `submission-form-fields.md` as the historical copy/paste packet for the
   submitted HackQuest form.
6. Run `scripts/submission_readiness.py --format markdown` or open
   `/api/hackathon/readiness` for the final readiness audit.
7. Use `threat-receipt-passport.md` as the one-page judge proof drill: intent,
   verdict, provenance, receipt hash, and 0G proof slots.
8. Use `market-intel.md` for current HackQuest requirements, track fit, and
   competitor positioning.
9. Reference `mainnet-gap-register.md` when judges ask what is real today
   versus what remains before a production/mainnet launch.
10. Use `/api/hackathon/submission-brief` for a machine-readable final brief
   with deadline, repo/demo links, submitted-state proof, data stats, and
   claims to avoid.
11. Use `/api/hackathon/submission-packet` for copy-ready HackQuest fields and
   submitted-state monitoring notes.
12. Use `x-cleanup-runbook.md` for the dry-run-first X media deletion manifest
    workflow; live deletion is never automatic.
13. Use `/telegram` as the mobile Telegram Mini App demo surface. It opens in
    browser-preview mode locally and becomes a Telegram Web App when launched
    through a BotFather-configured bot URL.

## Winning Thesis

0guard is not a generic wallet scanner. It is a pre-wallet firewall for AI
agents: it evaluates prompt intent, calldata, policy, known exploit signatures,
and agent identity before any signer or external channel can act.

The 0G integration matters because the product needs three things that 0G is
positioned to provide:

- 0G Chain for public, tamper-evident policy receipts.
- 0G Storage for portable threat-intel records and receipt payloads.
- 0G Compute for agent-risk scoring that can sit beside the policy engine.

The current submission demonstrates the full integration shape without crossing
unsafe workbench boundaries: live/read-only 0G status, deterministic Storage
payload/root-hash receipts, chain-anchor preflight payloads, and a public 0G
mainnet `PolicyReceiptAnchor` proof in `mainnet-proof.json`. Live Storage
upload and 0G Compute inference remain explicit gaps.

The new OSINT layer strengthens the evidence story: `data/osint_sources.json`
tracks source ownership, URLs, retrieval mode, rights envelopes, TTLs, and
caveats; `/api/osint/signals?live=1` normalizes public incident/research
metadata into source-cited records with hashes; `/api/data/signature-map`
explains detector coverage gaps instead of hiding them.
`data/incident_provenance_cache.json` keeps a reviewed derived-evidence cache
for offline judge demos, while `/api/data/provenance?live=1` can refresh
against live public source records when the network path is healthy.
The canonical incident dataset now includes per-incident source URLs and
derived evidence for 28 of 28 records. The detector map covers 28 of 28
incident-derived patterns, including the promoted `Quant` EIP-7702 delegated
account / permissionless batch-call access-control detector.

The cross-chain layer is now explicit instead of implied. `/api/integrations/cross-chain`
documents where 0guard can safely plug into Virtuals/Base, x402-supported
payment networks, EVM expansion chains, Lighter exchange/API guardrails,
Chainlink CCIP, LayerZero V2, Wormhole NTT, and Celestia/TIA data availability.
`/api/integrations/virtuals-facilitator` prepares a Base/Virtuals agent manifest
for a future `0guard Facilitator`, while all launch, payment, bridge, swap, and
wallet actions remain operator-only.

The Telegram layer is now demoable as a Mini App at
`https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram`. `/telegram` provides
the mobile wallet-alert surface; `/api/telegram/miniapp/session` validates
Telegram `initData` when present; `/api/telegram/miniapp/preview` returns one
combined wallet-alert + Mira response with quality-gate metadata and
`telegram_send=false`.

## Safety Posture

- No private keys in the repo or workbench.
- No transaction signing or broadcasting.
- No real 0G writes from the browser demo path.
- Public 0G mainnet proof is limited to the deployed receipt anchor and one
  anchored deny receipt.
- No trading or money movement claims.
- No live Virtuals launch, x402 settlement, bridge, swap, Lighter order,
  exchange account action, withdrawal, or cross-chain transaction from the
  workbench.
- No Telegram sends unless a separate operator uses an explicit live-send
  confirmation outside the judge workbench.
- No X media/post deletion unless a reviewed manifest exists and Ari gives
  fresh explicit live deletion confirmation.
- Live Storage upload and Compute scoring are documented as future work, not
  represented as complete.
