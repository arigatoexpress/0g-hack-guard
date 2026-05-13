# 0G Hackathon Strategy Deep Dive

## Strategic Frame

The winning submission should make 0guard feel like necessary infrastructure
for agentic crypto, not a security sidecar. The strongest framing is:

> AI agents should not reach a signer until their intent has a policy verdict
> and an audit receipt.

That frame naturally maps to 0G:

- 0G Chain records the decision receipt.
- 0G Storage carries the portable threat-intel and evidence payloads.
- 0G Compute becomes the risk-scoring layer for prompt and behavior anomaly
  detection.

## Judge-Comprehensible Product Story

The demo should avoid abstract "AI security" language and show a concrete
before/after:

1. An agent receives a prompt or tool plan that would require a signature.
2. 0guard inspects the intent before wallet access.
3. The detector flags exploit patterns judges can understand quickly.
4. The policy engine returns `allow`, `review`, or `deny`.
5. The verdict becomes a receipt hash.
6. 0G proof artifacts are prepared or read live.
7. The signer remains untouched unless policy allows the action.

This is easier to judge than a pure whitepaper because every step has a
readback: API JSON, receipt hash, 0G status, Storage root hash, and detection
coverage.

## 0G Layer Narrative

### 0G Chain

Use Chain as the audit rail. The current code prepares receipt-anchor payloads
for `PolicyReceiptAnchor.sol`, and `/api/0g/status` proves live read-only
connectivity to Galileo. The submission should say "preflight anchor payload"
until the contract is deployed and readback verification exists.

### 0G Storage

Use Storage as the threat-intel memory rail. The current code serializes the
policy/threat-intel payload and computes deterministic root hashes. The
submission should say "Storage-ready receipt/root hash" rather than "uploaded"
unless a live upload/readback has actually been configured.

### 0G Compute

Use Compute as the next inference rail. The strongest near-term implementation
is not to replace deterministic checks; it is to add a Compute-backed anomaly
score beside them:

- prompt-risk score
- tool-plan risk score
- social-engineering likelihood
- bridge/admin-operation risk
- confidence/provenance metadata

For this submission, position Compute as the planned scoring layer if it is not
live in the demo.

## Verifier Round-Trip Definition

A judge-safe verifier round-trip is:

1. Generate a policy verdict.
2. Hash the normalized verdict context into `receipt_hash`.
3. Produce a 0G Chain anchor payload.
4. Produce a 0G Storage receipt/root hash when threat intel is present.
5. Read 0G Galileo status live.
6. Later, after deployment, verify the receipt through contract readback.

The phrase "round-trip" should be used carefully: the demo shows the local
verifier and proof-preparation loop now; full on-chain verification remains a
documented gap until the anchor contract is deployed and queried.

## Winner-Oriented Checklist

- Lead with a real security failure mode, not a generic agent pitch.
- Show the product blocking a dangerous intent in under 30 seconds.
- Make every 0G claim visible in JSON readbacks.
- Use the words "read-only", "preflight", and "operator-controlled" where they
  protect credibility.
- Explain the mainnet gap before judges have to ask.
- Do not claim live writes, trading, wallet custody, or Telegram sends.
- Close on the roadmap: deploy anchor, verify readback, live Storage upload,
  Compute-backed anomaly score.
