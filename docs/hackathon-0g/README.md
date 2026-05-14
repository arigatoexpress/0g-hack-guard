# 0G Hackathon Submission Pack

This folder is the judge-facing copy pack for the 0guard 0G hackathon
submission. It is intentionally written from the live demo posture: read-only
0G RPC proof, deterministic receipts, operator-controlled anchoring, and no
private keys or real writes in the workbench.

## Recommended Judge Path

1. Start with `submission-copy.md` for the project summary, track fit, and
   field-ready HackQuest copy.
2. Use `demo-judge-walkthrough.md` while recording or presenting the live demo.
3. Reference `mainnet-gap-register.md` when judges ask what is real today
   versus what remains before a production/mainnet launch.
4. Use `/api/hackathon/submission-brief` for a machine-readable final brief
   with deadline, repo/demo links, data stats, manual TODOs, and claims to
   avoid.

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
unsafe boundaries: live/read-only 0G Galileo status, deterministic Storage
payload/root-hash receipts, chain-anchor preflight payloads, and explicit gaps
before mainnet broadcast or live decentralized storage writes.

The new OSINT layer strengthens the evidence story: `data/osint_sources.json`
tracks source ownership, URLs, retrieval mode, rights envelopes, TTLs, and
caveats; `/api/osint/signals?live=1` normalizes public incident/research
metadata into source-cited records with hashes; `/api/data/signature-map`
explains detector coverage gaps instead of hiding them.

## Safety Posture

- No private keys in the repo or workbench.
- No transaction signing or broadcasting.
- No real 0G writes from the demo path.
- No trading or money movement claims.
- No Telegram sends unless a separate operator uses an explicit live-send
  confirmation outside the judge workbench.
- Mainnet work is documented as future work, not represented as complete.
