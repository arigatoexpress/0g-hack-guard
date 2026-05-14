# 0guard Finish Guide

This file is now a short pointer to the current HackQuest submission packet.
Older testnet-first instructions were intentionally removed because HackQuest's
current requirement is a 0G mainnet contract address plus a 0G Explorer link.

## Current Source of Truth

- Final checklist: `docs/hackathon-0g/final-submission-checklist.md`
- Copy/paste fields: `docs/hackathon-0g/submission-form-fields.md`
- Demo script: `docs/DEMO_VIDEO_SCRIPT.md`
- Machine packet: `/api/hackathon/submission-packet`
- Readiness audit: `/api/hackathon/readiness`

## Safe Local Audit

```bash
cd /Users/aribs/Code/0guard
.venv/bin/python scripts/submission_readiness.py --format markdown
```

The expected state before Ari performs manual actions is `submittable now:
false`. The remaining blockers should be operator-only: 0G mainnet
contract/explorer proof, demo video URL, and public X post URL.

## Operator-Only Final Tasks

1. Deploy and anchor one receipt with `PolicyReceiptAnchor` on 0G mainnet.
2. Save the 0G mainnet contract address and Explorer transaction URL.
3. Record and upload the <=3 minute demo video.
4. Post the required X post with screenshot or short clip.
5. Paste the packet into HackQuest before May 16, 2026 at 09:59 MDT.

## Safety Rules

- Do not put private keys or API credentials into this repo.
- Do not commit `.env` files.
- Do not use the browser workbench to sign, broadcast, trade, bridge, send
  Telegram messages, or move funds.
- Do not claim live 0G mainnet writes until the mainnet contract/explorer proof
  exists.
