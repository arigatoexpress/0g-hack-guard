# HackQuest Submission Form Fields

Generated for final operator submission on May 14, 2026.

Use this as the copy/paste packet for HackQuest. Values marked
`OPERATOR_REQUIRED` need Ari to provide the final public link before
submission.

## Project

HackQuest draft URL:

```text
https://www.hackquest.io/projects/setup/f8333543-559e-48f4-b6fa-4ff447777966
```

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
0guard is a pre-wallet firewall for AI agents. It evaluates prompts, action mode, calldata, target contracts, domains, policy context, and incident-derived exploit intelligence before an agent can reach a signer. The product returns allow/review/deny verdicts, deterministic receipt hashes, a live 0G mainnet receipt anchor, Storage-ready threat-intel root hashes, and a read-only cross-chain integration fabric for Virtuals/Base, x402, EVM expansion chains, Lighter/LIT exchange guardrails, and Celestia/TIA proof lanes. The workbench stays read-only and never holds keys, signs, broadcasts, trades, stakes LIT, launches agents, settles payments, or sends Telegram messages.
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
0guard uses 0G Chain for policy receipt anchoring, 0G Storage for portable threat-intel receipt payloads and root hashes, and a planned 0G Compute layer for agent-risk anomaly scoring. A PolicyReceiptAnchor contract is deployed on 0G mainnet with one anchored deny receipt; the browser workbench remains read-only and returns deterministic Storage-ready root hashes without private keys or browser-side broadcasts.
```

Proof routes to show:

```text
/api/0g/status
/api/evaluate with enable_0g_anchor=true and enable_0g_storage=true
/api/data/provenance
/api/data/provenance?live=1
/api/integrations/cross-chain
/api/integrations/virtuals-facilitator
docs/hackathon-0g/mainnet-proof.json
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
docs/hackathon-0g/final-demo-video-script.md
```

Demo video URL:

```text
https://arigatoexpress.github.io/0guard/hackathon-0g/assets/0guard-hackquest-demo-final.mp4
```

X post URL:

```text
https://x.com/rariwrldd/status/2054779961425461542
```

0G contract address:

```text
0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc
```

0G explorer URL:

```text
https://chainscan.0g.ai/tx/64ff260ccd02aa69fc18d5727eb4530d8774003bc7df63ec7d5cda036fc438ed
```

0G contract page:

```text
https://chainscan.0g.ai/address/0xBaC59b1571b7c7195915c5B36D8A719Ed7182abc
```

Anchored receipt hash:

```text
0x9739dbd4afb6ab21f15ccb634b49dabc9144550ef06d346cb4e7cd363e74afd1
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

1. Open the HackQuest draft URL above.
2. Verify the saved name/intro, then paste the remaining fields above.
3. Use the public demo video URL and published X URL already listed in this packet.
4. Re-open the public repo, Pages URL, demo video URL, X post URL, and 0G Explorer links from an incognito window.
5. Submit before May 16, 2026 at 23:59 UTC+8.

## Manual Recovery Note

The signed-in HackQuest draft exists, but browser-coordinate automation proved
unreliable on the form. Do not continue blind UI automation. The fastest safe
path is manual copy/paste from this packet into the draft URL above.

## Claims To Avoid

- Do not claim live 0G Compute inference.
- Do not imply the browser can sign, trade, bridge, send Telegram messages, or
  move funds.
- Do not claim live Virtuals launch, x402 settlement, or custom 0G x402
  facilitation until those paths are separately configured and verified.
- Do not claim live Lighter orders, LIT staking/fee credits, transfers, or
  withdrawals from the workbench.
- Do not mirror or resell raw upstream OSINT payloads.
