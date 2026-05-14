# 0G APAC Hackathon Market Intel

Snapshot date: May 14, 2026.

## Official Submission Facts

Source: [0G APAC Hackathon on HackQuest](https://www.hackquest.io/hackathons/0G-APAC-Hackathon)

- Final submission deadline: May 16, 2026 at 23:59 UTC+8.
- Denver equivalent: May 16, 2026 at 09:59 MDT.
- Prize pool: $150,000 total, split across grand prizes, excellence awards,
  and community awards.
- Valid submissions need basic project info, a public or judge-accessible
  GitHub repo, 0G integration proof, a demo video of no more than 3 minutes,
  README/docs, and a public X post.
- The 0G proof needs a mainnet contract address and 0G Explorer link showing
  verifiable on-chain activity. Testnet/Galileo proof is useful demo evidence
  but should not be framed as the final mainnet proof.
- The X post is mandatory and must include the project name, a demo screenshot
  or short clip, `#0GHackathon`, `#BuildOn0G`, and tags for `@0G_labs`,
  `@0g_CN`, `@0g_Eco`, and `@HackQuest_`.
- The core risk is proof depth: HackQuest says projects without actual 0G
  integration may be invalid or heavily penalized.

## Track Fit

Primary recommendation: Track 5, Privacy & Sovereign Infrastructure.

0guard is strongest as a verifiable safety/provenance layer for AI agents
before wallet custody begins. That maps cleanly to privacy, security,
sovereign infrastructure, and MEV/front-running-adjacent risk prevention.

Secondary recommendation: Track 1, Agentic Infrastructure & OpenClaw Lab.

Use this only if the final demo emphasizes agent workflows, specialized
skills, and data-processing pipelines more than security proof infrastructure.

## Competitive Pattern

Visible strong submissions package a public proof chain, not just a product
claim. The recurring pattern is:

- live app or CLI;
- public repo with hackathon-period progress;
- contract address or transaction hash;
- storage root or durable proof artifact;
- explorer links;
- judge walkthrough;
- clear statement of what is mainnet, testnet, simulated, or future work.

Examples worth tracking:

- [0G Forge](https://www.hackquest.io/projects/0G-Forge): terminal-native
  agent framework with 0G Compute, Storage, and Chain anchoring.
- [0G Build Proof](https://www.hackquest.io/en/projects/0g-Build-Proof):
  judge-ready evidence passport with repo inspection, Storage roots, and
  Chain anchors.
- [0G Thermidora](https://www.hackquest.io/projects/0G-Thermidora): managed
  agent platform with 0G chain/storage/KV skills and live network data.
- [0G SkillCapsule](https://www.hackquest.io/projects/0g-skillcapsule):
  proof-native AI agent marketplace using Storage, Compute Router, and an
  onchain registry.
- [Synapse](https://www.hackquest.io/projects/Synapse): decentralized agent
  memory with 0G Storage and Galileo hash verification.

## 0guard Positioning

Do not pitch 0guard as a generic wallet scanner. The best wedge is:

> 0guard is the pre-wallet firewall and provenance layer for AI agents. It
> checks intent, calldata, domain context, and incident intelligence before an
> autonomous agent can reach a signer.

Winning proof sequence:

1. Intent enters `/api/evaluate`.
2. 0guard returns allow/review/deny plus a deterministic receipt hash.
3. `enable_0g_anchor=true` exposes the exact Chain anchor payload in preflight.
4. `enable_0g_storage=true` exposes a Storage-ready threat-intel receipt and
   root hash.
5. `/api/0g/status` proves live, read-only Galileo connectivity.
6. `/api/data/provenance?live=1` proves the incident dataset can be correlated
   against live public source records without returning raw upstream payloads.

## Current Submission State

- The 0G mainnet `PolicyReceiptAnchor` contract and anchor transaction are
  live and included in the submitted proof packet.
- The final public demo video is ready at
  `https://arigatoexpress.github.io/0guard/hackathon-0g/assets/0guard-hackquest-demo-final.mp4`.
- The submitted X proof URL is
  `https://x.com/rariwrldd/status/2054779961425461542`.
- A prepared screenshot still exists at
  `docs/hackathon-0g/assets/0guard-workbench-provenance.png`.
- Per-incident source evidence is now promoted for 28 of 28 records.
- The detector map covers 27 of 28 incident-derived patterns. `Quant` remains
  research-only until stronger public root-cause evidence exists.
- Remaining production gaps are live 0G Storage upload/readback and 0G Compute
  inference, both documented as future work rather than submitted live claims.

## Demo Advice

Lead with the product and proof trail, not architecture. In three minutes:

1. Show a risky agent wallet intent being denied.
2. Show 0G status readback.
3. Show receipt preflight/root hash.
4. Show provenance/source match counts.
5. Close with the honesty boundary: no keys, no signing, no broadcasts, no
   Telegram sends from the workbench.
