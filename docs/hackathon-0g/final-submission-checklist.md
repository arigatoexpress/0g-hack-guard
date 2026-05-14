# 0guard Final HackQuest Submission Checklist

Snapshot date: May 14, 2026.

Official source: https://www.hackquest.io/hackathons/0G-APAC-Hackathon

Hard deadline: May 16, 2026 at 23:59 UTC+8, which is May 16, 2026 at
09:59 MDT in Denver.

## Ready to Paste

- HackQuest draft:
  https://www.hackquest.io/projects/setup/f8333543-559e-48f4-b6fa-4ff447777966
- Project name: `0guard`
- Track: `Track 5: Privacy & Sovereign Infrastructure`
- Backup track: `Track 1: Agentic Infrastructure & OpenClaw Lab`
- One-liner: `0guard is a 0G-native pre-wallet firewall that checks AI-agent intents against exploit intelligence before any signer can act.`
- Repository: https://github.com/arigatoexpress/0guard
- Public demo page: https://arigatoexpress.github.io/0guard/
- Screenshot asset: `docs/hackathon-0g/assets/0guard-workbench-provenance.png`
- 0G mainnet contract:
  `0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc`
- 0G anchor transaction:
  https://chainscan.0g.ai/tx/64ff260ccd02aa69fc18d5727eb4530d8774003bc7df63ec7d5cda036fc438ed
- Copy/paste form packet: `docs/hackathon-0g/submission-form-fields.md`
- Judge proof drill: `docs/hackathon-0g/threat-receipt-passport.md`

## Mainnet Proof Ready

HackQuest requires a 0G mainnet contract address and a 0G Explorer link showing
verifiable activity. 0guard now has both: `PolicyReceiptAnchor` is deployed on
0G mainnet and one deny receipt is anchored. The local workbench still stays
safe by default: it creates receipt-anchor preflight payloads and returns
Storage-ready root hashes without keys, signing, or browser-side broadcasts.

Use these values in HackQuest:

- Contract: `0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc`
- Contract URL:
  https://chainscan.0g.ai/address/0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc
- Anchor transaction:
  https://chainscan.0g.ai/tx/64ff260ccd02aa69fc18d5727eb4530d8774003bc7df63ec7d5cda036fc438ed
- Receipt hash:
  `0x9739dbd4afb6ab21f15ccb634b49dabc9144550ef06d346cb4e7cd363e74afd1`

Mainnet references:

- 0G mainnet RPC: `https://evmrpc.0g.ai`
- 0G mainnet chain ID: `16661`
- 0G mainnet explorer: https://chainscan.0g.ai
- 0G Storage explorer, if used: https://storagescan.0g.ai

## Local Audit

Run the read-only audit before final submission:

```bash
.venv/bin/python scripts/submission_readiness.py --format markdown
```

Run strict mode only when you expect all operator links to be present:

```bash
.venv/bin/python scripts/submission_readiness.py --strict
```

The API equivalent is:

```bash
curl -s http://127.0.0.1:8109/api/hackathon/readiness | python3 -m json.tool
```

## Demo Video

Requirement: public video link, no more than 3 minutes, not slide-only.

Record from `docs/hackathon-0g/final-demo-video-script.md` and show:

- intent firewall blocking a risky agent action
- live `/api/0g/status` readback
- `/api/evaluate` with `enable_0g_anchor=true` and `enable_0g_storage=true`
- `/api/data/provenance` and `/api/data/provenance?live=1`
- the mainnet contract/explorer proof if it is ready
- optional Veo 3 clips only as short cinematic inserts around the live product
  walkthrough

Generated public demo video:

```text
https://arigatoexpress.github.io/0guard/hackathon-0g/assets/0guard-hackquest-demo-final.mp4
```

## Required X Post

Requirement: one public X post with project name, screenshot or short clip,
`#0GHackathon`, `#BuildOn0G`, and tags for `@0G_labs @0g_CN @0g_Eco @HackQuest_`.

Prepared single-post draft:

```bash
.venv/bin/python scripts/x_post.py --file content/hackquest_x_post.json --media docs/hackathon-0g/assets/0guard-workbench-provenance.png --dry-run --verbose
```

Live posting is operator-only:

```bash
.venv/bin/python scripts/x_post.py --file content/hackquest_x_post.json --media docs/hackathon-0g/assets/0guard-workbench-provenance.png --live-post-confirm POST_TO_X_FROM_0GUARD
```

Published X post:

```text
https://x.com/rariwrldd/status/2054779961425461542
```

## Final Submit Order

1. Run the readiness audit and verify only HackQuest form completion remains.
2. Open the HackQuest draft URL above.
3. Paste `docs/hackathon-0g/submission-form-fields.md` into HackQuest.
4. Use the already-published demo video and X post URLs from this checklist.
5. Open the public repo, Pages URL, demo video URL, X post URL, and 0G Explorer URLs from a logged-out/incognito window.
6. Submit before May 16, 2026 at 09:59 MDT.

## Manual Recovery Note

The HackQuest draft was created under the signed-in `rari` account, but
coordinate-based browser filling was unreliable. Continue manually from the
draft URL; do not run blind UI automation against the form.

## Claims to Avoid

- Do not claim live 0G Compute inference.
- Do not imply the browser can sign, trade, bridge, send Telegram messages, or move funds.
- Do not mirror or resell raw upstream OSINT payloads.
