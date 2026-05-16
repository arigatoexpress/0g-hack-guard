# Reputation Adapter

0guard should not claim a live global reputation graph until the upstream
source contracts and paid feeds are configured. What is useful today is a
rights-aware adapter contract that accepts domain, counterparty, labels, source
evidence, and intent context, then returns a derived verdict with a 0G-ready
receipt.

## API

```bash
curl -X POST http://127.0.0.1:8109/api/reputation/probe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.0g.ai.evil.example/claim",
    "address": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
    "chain": "eip155:1",
    "sourceEvidence": [
      {"sourceId": "operator_report", "verdict": "phishing", "confidence": 0.91}
    ],
    "intent": {
      "action": "upgrade",
      "mode": "live_transaction",
      "requires_signature": true
    }
  }'
```

Expected result: `deny`, with signals for allowlist suffix spoofing, local IOC
match, source negative vote, and intent policy context.

## What It Uses Today

- Curated allowlist domain matching for official 0G, HackQuest, and GitHub
  surfaces.
- Local IOC matches from the existing 0guard exploit signature module.
- Caller-supplied source votes, converted into derived hashes and labels.
- The existing policy engine for signer, calldata, and prompt-risk context.

## Rights Boundary

The adapter returns derived decisions, source IDs, labels, confidence, hashes,
and redacted addresses. It does not return raw source payloads, scrape private
feeds, custody credentials, or make network calls.

## Where It Fits

- `/api/native-preflight` includes a `reputation_probe` component when the
  caller supplies a domain, counterparty, label, or source evidence.
- `/api/developer-kit` points adapter builders at the route.
- Telegram and wallet alerts can use this as the next enrichment layer before
  stronger claims about live address reputation.
