# 0guard Threat Case File

The threat case file is the clearest single product walkthrough for 0guard. It
takes one wallet-adjacent agent intent and returns a judge/operator-readable
proof dossier.

## Live Route

`POST /api/threat-case-file`

The route composes:

- policy engine verdict
- hack-signature matches and IOC hits
- reputation probe decision
- wallet-alert quality gate
- incident provenance coverage
- signature coverage
- 0G-ready receipt hashes

## Example

```bash
curl -s -X POST http://127.0.0.1:8109/api/threat-case-file \
  -H "Content-Type: application/json" \
  -d '{"intent":{"action":"approve","mode":"live_transaction","requires_signature":true,"target_contract":"0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab"}}' \
  | python3 -m json.tool
```

## Output Shape

- `decision`: allow/review/deny rollup
- `plainEnglish`: short explanation for non-technical reviewers
- `technicalSummary`: counts and source-backed status
- `subject`: redacted wallet/counterparty plus hashes
- `evidence`: source IDs, summaries, and hashes
- `operatorNextSteps`: what a human should do next
- `receipt`: deterministic case-file receipt hash
- `sourceRights`: raw payloads are not returned or resold
- `safety`: no signing, no broadcasting, no sends, no uploads, no money movement

This route is intentionally a proof dossier, not an execution adapter.
