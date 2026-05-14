# 0guard Handoff

Current handoff for the 0G APAC Hackathon submission.

## Built

- Pre-wallet intent firewall with `allow` / `review` / `deny` verdicts.
- April 2026 incident dataset, detector coverage, and signature gap mapping.
- Rights-aware OSINT source registry and canonical provenance evidence.
- Read-only 0G Galileo status proof and receipt-anchor preflight payloads.
- Storage-ready threat-intel receipt/root-hash output.
- Public Pages proof packet section.
- Copy-ready HackQuest submission packet and final readiness audit.

## Current Proof Boundary

The workbench is safe by default: no keys, no signing, no broadcasts, no live
X/Telegram sends, and no money movement. It proves the integration shape, but
HackQuest-final proof still requires Ari to provide a 0G mainnet contract
address and Explorer link.

## Ari-Only Tasks

1. Deploy/anchor `PolicyReceiptAnchor` on 0G mainnet.
2. Record and upload the <=3 minute demo video.
3. Publish the required X post with the prepared screenshot or demo clip.
4. Submit the HackQuest form.

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
