# HackQuest Submission Form Fields

Generated for final operator submission on May 14, 2026.

Use this as the copy/paste packet for HackQuest. Values marked
`OPERATOR_REQUIRED` need Ari to provide the final public link or proof before
submission.

## Project

Project name:

```text
0guard
```

Recommended track:

```text
Track 5: Privacy & Sovereign Infrastructure
```

Alternate track:

```text
Track 1: Agentic Infrastructure & OpenClaw Lab
```

One-line description:

```text
0guard is a 0G-native pre-wallet firewall that checks AI-agent intents against exploit intelligence before any signer can act.
```

## Summary

```text
0guard is a pre-wallet firewall for AI agents. It evaluates prompts, action mode, calldata, target contracts, domains, policy context, and incident-derived exploit intelligence before an agent can reach a signer. The product returns allow/review/deny verdicts, deterministic receipt hashes, 0G Chain anchor preflight payloads, and Storage-ready threat-intel root hashes. The current submission is intentionally read-only: it proves live 0G Galileo status and the full receipt shape without holding keys, signing, broadcasting, trading, or sending Telegram messages.
```

## Problem

```text
AI agents are gaining wallet and bridge tooling faster than their safety controls are maturing. Most security checks happen near signing time, after an agent has already formed a risky action. 0guard moves the review point earlier: intent first, signer later.
```

## Solution

```text
0guard checks agent intent against deterministic policy rules, known exploit signatures, behavioral sequences, domain context, and source-cited incident intelligence. Risky actions are blocked before wallet custody begins, and every evaluation can become a tamper-evident receipt for 0G Chain and 0G Storage workflows.
```

## 0G Integration

```text
0guard uses 0G Chain for policy receipt anchoring, 0G Storage for portable threat-intel receipt payloads and root hashes, and a planned 0G Compute layer for agent-risk anomaly scoring. Today the app reads 0G Galileo live in read-only mode, prepares receipt-anchor payloads for PolicyReceiptAnchor.sol, and returns deterministic Storage-ready root hashes without private keys or broadcasts.
```

Proof routes to show:

```text
/api/0g/status
/api/evaluate with enable_0g_anchor=true and enable_0g_storage=true
/api/data/provenance
/api/data/provenance?live=1
```

## Links

Repository:

```text
https://github.com/arigatoexpress/0guard
```

Public demo page:

```text
https://arigatoexpress.github.io/0guard/
```

Screenshot asset:

```text
docs/hackathon-0g/assets/0guard-workbench-provenance.png
```

Final readiness checklist:

```text
docs/hackathon-0g/final-submission-checklist.md
```

Demo script:

```text
docs/DEMO_VIDEO_SCRIPT.md
```

Demo video URL:

```text
OPERATOR_REQUIRED_DEMO_VIDEO_URL
```

X post URL:

```text
OPERATOR_REQUIRED_X_POST_URL
```

0G contract address:

```text
OPERATOR_REQUIRED_0G_MAINNET_CONTRACT_ADDRESS
```

0G explorer URL:

```text
OPERATOR_REQUIRED_0G_MAINNET_EXPLORER_URL
```

## X Post

Required tags and hashtags:

```text
@0G_labs @0g_CN @0g_Eco @HackQuest_
#0GHackathon #BuildOn0G
```

Dry-run command:

```bash
.venv/bin/python scripts/x_post.py --file content/hackquest_x_post.json --media docs/hackathon-0g/assets/0guard-workbench-provenance.png --dry-run --verbose
```

Live command after Ari review:

```bash
.venv/bin/python scripts/x_post.py --file content/hackquest_x_post.json --media docs/hackathon-0g/assets/0guard-workbench-provenance.png --live-post-confirm POST_TO_X_FROM_0GUARD
```

Readiness audit:

```bash
.venv/bin/python scripts/submission_readiness.py --format markdown
```

## Final Submit Order

1. Record and upload the demo video.
2. Deploy/configure `PolicyReceiptAnchor` on 0G mainnet and save the contract
   address plus explorer URL.
3. Post the required X post with screenshot or clip.
4. Paste the fields above into HackQuest.
5. Re-open the public repo and Pages URL from an incognito window.
6. Submit before May 16, 2026 at 23:59 UTC+8.

## Claims To Avoid

- Do not claim live mainnet writes.
- Do not claim live 0G Compute inference.
- Do not imply the browser can sign, trade, bridge, send Telegram messages, or
  move funds.
- Do not mirror or resell raw upstream OSINT payloads.
