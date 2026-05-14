# 0guard Final HackQuest Submission Checklist

Snapshot date: May 14, 2026.

Official source: https://www.hackquest.io/hackathons/0G-APAC-Hackathon

Hard deadline: May 16, 2026 at 23:59 UTC+8, which is May 16, 2026 at
09:59 MDT in Denver.

## Ready to Paste

- Project name: `0guard`
- Track: `Track 5: Privacy & Sovereign Infrastructure`
- Backup track: `Track 1: Agentic Infrastructure & OpenClaw Lab`
- One-liner: `0guard is a 0G-native pre-wallet firewall that checks AI-agent intents against exploit intelligence before any signer can act.`
- Repository: https://github.com/arigatoexpress/0guard
- Public demo page: https://arigatoexpress.github.io/0guard/
- Screenshot asset: `docs/hackathon-0g/assets/0guard-workbench-provenance.png`
- Copy/paste form packet: `docs/hackathon-0g/submission-form-fields.md`
- Judge proof drill: `docs/hackathon-0g/threat-receipt-passport.md`

## Mainnet Proof Required

HackQuest requires a 0G mainnet contract address and a 0G Explorer link showing
verifiable activity. The local workbench currently stays safe by default: it
reads Galileo/testnet state, creates receipt-anchor preflight payloads, and
returns Storage-ready root hashes without keys, signing, or broadcasts.

Before final submission, Ari needs to provide:

- `OPERATOR_REQUIRED_0G_MAINNET_CONTRACT_ADDRESS`
- `OPERATOR_REQUIRED_0G_MAINNET_EXPLORER_URL`
- the transaction or event that proves at least one receipt was anchored

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

Record from `docs/DEMO_VIDEO_SCRIPT.md` and show:

- intent firewall blocking a risky agent action
- live `/api/0g/status` readback
- `/api/evaluate` with `enable_0g_anchor=true` and `enable_0g_storage=true`
- `/api/data/provenance` and `/api/data/provenance?live=1`
- the mainnet contract/explorer proof if it is ready

Placeholder until uploaded:

```text
OPERATOR_REQUIRED_DEMO_VIDEO_URL
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

Placeholder until posted:

```text
OPERATOR_REQUIRED_X_POST_URL
```

## Final Submit Order

1. Run the readiness audit and verify only operator-only blockers remain.
2. Deploy and anchor a receipt on 0G mainnet, then save contract and explorer URLs.
3. Record and upload the demo video.
4. Publish the required X post with the screenshot or demo clip.
5. Open the public repo and Pages URL from a logged-out/incognito window.
6. Paste `docs/hackathon-0g/submission-form-fields.md` into HackQuest.
7. Submit before May 16, 2026 at 09:59 MDT.

## Claims to Avoid

- Do not claim live 0G mainnet writes until the mainnet contract/explorer URL exists.
- Do not claim live 0G Compute inference.
- Do not imply the browser can sign, trade, bridge, send Telegram messages, or move funds.
- Do not mirror or resell raw upstream OSINT payloads.
