# 0G Hackathon Submission Pack

This folder is the judge-facing copy pack for the 0guard 0G hackathon
submission. It is intentionally written from the live demo posture: read-only
0G RPC proof in the workbench, deterministic receipts, public mainnet anchoring
proof, and no private keys or real writes in the workbench.

## Recommended Judge Path

1. Start with `submission-copy.md` for the project summary, track fit, and
   field-ready HackQuest copy.
2. Use `demo-judge-walkthrough.md` while recording or presenting the live demo.
3. Use `submission-form-fields.md` as the final copy/paste packet for the
   HackQuest form.
4. Run `scripts/submission_readiness.py --format markdown` or open
   `/api/hackathon/readiness` for the final readiness audit.
5. Use `final-submission-checklist.md` for the manual submission sequence,
   mainnet proof requirement, demo video, and X post.
6. Use `threat-receipt-passport.md` as the one-page judge proof drill: intent,
   verdict, provenance, receipt hash, and 0G proof slots.
7. Use `market-intel.md` for current HackQuest requirements, track fit, and
   competitor positioning.
8. Reference `mainnet-gap-register.md` when judges ask what is real today
   versus what remains before a production/mainnet launch.
9. Use `/api/hackathon/submission-brief` for a machine-readable final brief
   with deadline, repo/demo links, data stats, manual TODOs, and claims to
   avoid.
10. Use `/api/hackathon/submission-packet` for copy-ready HackQuest fields and
   remaining operator placeholders.

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
derived evidence for 26 of 28 records; `Silo V2` and `Denaria Finance` are the
two explicit source-proof gaps.

## Safety Posture

- No private keys in the repo or workbench.
- No transaction signing or broadcasting.
- No real 0G writes from the browser demo path.
- Public 0G mainnet proof is limited to the deployed receipt anchor and one
  anchored deny receipt.
- No trading or money movement claims.
- No Telegram sends unless a separate operator uses an explicit live-send
  confirmation outside the judge workbench.
- Live Storage upload and Compute scoring are documented as future work, not
  represented as complete.
