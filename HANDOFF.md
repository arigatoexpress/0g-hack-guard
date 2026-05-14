# 0guard Handoff

Current handoff for the 0G APAC Hackathon submission.

## Built

- Pre-wallet intent firewall with `allow` / `review` / `deny` verdicts.
- April 2026 incident dataset, detector coverage, and signature gap mapping.
- Rights-aware OSINT source registry and canonical provenance evidence.
- Read-only 0G mainnet status proof and receipt-anchor preflight payloads.
- Storage-ready threat-intel receipt/root-hash output.
- Public Pages proof packet section.
- Copy-ready HackQuest submission packet and final readiness audit.
- Public 0G mainnet `PolicyReceiptAnchor` proof with one anchored deny receipt.
- Final demo video and submitted public X proof URL.

## Current Proof Boundary

The workbench is safe by default: no keys, no signing, no broadcasts, no live
X/Telegram sends, and no money movement. The HackQuest-final proof packet now
includes the 0G mainnet contract address, Explorer transaction, final demo
video URL, and submitted public X proof URL.

## Ari-Only Tasks

1. Review any refreshed video/social copy before public follow-up posts.
2. Approve any live Storage upload, Compute call, x402 settlement, Virtuals
   launch, bridge, trade, or Lighter action before it happens.
3. Keep submitted proof URLs unchanged unless replacing them intentionally.

## Commands

```bash
cd /Users/aribs/Code/0guard
.venv/bin/python scripts/submission_readiness.py --format markdown
.venv/bin/python scripts/x_post.py --file content/hackquest_x_post.json --media docs/hackathon-0g/assets/0guard-workbench-provenance.png --dry-run --verbose
```

## Pointers

- `docs/hackathon-0g/final-submission-checklist.md`
- `docs/hackathon-0g/submission-form-fields.md`
- `docs/hackathon-0g/mainnet-gap-register.md`
- `docs/hackathon-0g/market-intel.md`
