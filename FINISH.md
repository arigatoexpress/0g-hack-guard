# 0guard Finish Guide

This file is now a short pointer to the current HackQuest submission packet.
Older testnet-first instructions were intentionally removed because HackQuest's
current requirement is a 0G mainnet contract address plus a 0G Explorer link.

## Current Source of Truth

- Final checklist: `docs/hackathon-0g/final-submission-checklist.md`
- Copy/paste fields: `docs/hackathon-0g/submission-form-fields.md`
- Current demo script: `docs/hackathon-0g/final-demo-video-script.md`
- Professional remake packet: `docs/hackathon-0g/veo3-flow-production-prompt.md`
- Machine packet: `/api/hackathon/submission-packet`
- Readiness audit: `/api/hackathon/readiness`

## Safe Local Audit

```bash
cd /Users/aribs/Code/0guard
.venv/bin/python scripts/submission_readiness.py --format markdown
```

The expected state after the completed submission run is `submittable now:
true`, with a documented 0G mainnet contract/explorer proof, demo video URL,
and public X proof URL. If the readiness audit returns `false`, treat the
reported blocker list as the current source of truth.

## Operator-Only Final Tasks

1. Review the readiness audit and proof packet before any follow-up edits.
2. If the video is rebuilt, verify it remains under three minutes and update
   the public Pages asset.
3. Use the prepared X/LinkedIn drafts for follow-up launch posts only after
   manual review.
4. Preserve the submitted 0G mainnet proof and X proof URL in the packet.

## Safety Rules

- Do not put private keys or API credentials into this repo.
- Do not commit `.env` files.
- Do not use the browser workbench to sign, broadcast, trade, bridge, send
  Telegram messages, or move funds.
- Do not claim new live 0G writes, Storage uploads, Compute inference,
  payments, launches, or trading unless the matching public proof exists.
