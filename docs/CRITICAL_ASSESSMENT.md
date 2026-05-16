# 0guard Critical Assessment

## Strongest Current Wedge

0guard is strongest when it owns one moment: before an AI agent reaches a
signer. The project is not trying to be a wallet, bridge, exchange, or generic
chain scanner. It is a pre-wallet checkpoint that produces an explainable
allow/review/deny verdict and a receipt.

## What Was Missing

1. **Comprehension surface.** The project had many strong parts, but no single
   route or document that explained what exists, what is live, what is only
   planned, and where the safety boundaries are.
2. **Social narrative update.** The public copy still mostly described the
   hackathon submission. It did not reflect the Telegram Mini App, native
   preflight developer kit, reputation connector manifest, and production
   Cloud Run deployment.
3. **Connector story.** The external intelligence plan existed, but needed a
   clear subject-aware activation view that says which sources matter next
   without pretending those feeds are live.
4. **Experiment surface.** The repo needed a safe way to keep researching
   future integrations without creating false live claims.
5. **Adapter proof surface.** The system needed a visible path from reviewed
   upstream reputation payloads to public-safe evidence in the case file and
   Telegram preview.
6. **0G proof ladder contract.** The public proof page described Chain,
   Storage, DA, Compute, and Alignment readiness, but the live API did not yet
   expose that ladder as a machine-readable packet.

## Improvements Shipped

- Added `/api/product/brief`, a plain-English system map with live proof links,
  built systems, honest limits, and next best builds.
- Added a dashboard `Product brief` button so the brief is visible in the
  workbench.
- Added `docs/PROJECT_BRIEF.md` for a stable human-readable explanation.
- Added `content/0guard_current_update_x_thread.json`, a dry-run-valid X thread
  for the project account or Ari's main account.
- Added `content/substack_0guard_launch_draft.md`, a review-ready long-form
  launch/update post.
- Updated the public proof hub to reference `/api/product/brief` and
  `/api/reputation/connectors`.
- Added `/api/threat-case-file`, a composed proof dossier for one agent intent
  across policy, exploit signatures, reputation, wallet alert gates,
  provenance, and 0G-ready receipts.
- Added `/api/experiments/frontier` and `/api/experiments/run`, a read-only
  frontier lab for 0G Storage/Compute, GoPlus/Chainabuse/Forta, Tenderly or
  BlockSec simulation, Telegram/TON, and Mira.
- Added `/api/reputation/adapters` and `/api/reputation/adapters/normalize`
  for no-network PhishDestroy, CryptoScamDB, Forta labelled datasets, GoPlus,
  Chainabuse, and Forta GraphQL payload normalization.
- Promoted normalized adapter evidence into `/api/threat-case-file` and the
  Telegram Mini App preview surface without exposing raw source payloads.
- Added `/api/0g/proof-ladder`, a five-stage no-side-effect proof packet for
  Chain receipt, Storage packet, DA availability, Compute preview, and
  Alignment verifier readiness.

## Next Technical Priorities

1. **Make the threat case file the default demo.** It is the clearest single
   surface for judges, wallet teams, agent frameworks, and operators.
2. **Activate one fetch worker behind the normalizer.** Start with PhishDestroy
   or CryptoScamDB before keyed GoPlus or Chainabuse, keep public routes
   no-network, test with fixtures, and return only derived signals.
3. **Add 0G Storage readback.** Store a receipt payload only through an
   operator-approved path, then prove retrieval.
4. **Add transaction simulation summaries.** Use Tenderly or BlockSec to turn
   risky calls into simple asset-delta explanations.
5. **Deepen Telegram/TON.** Add read-only TON account/Jetton context through
   TON Center or TONAPI, without tonProof or transaction prompts.

## Non-Negotiable Boundaries

- No secret exposure.
- No key import.
- No wallet creation from the workbench.
- No signing or broadcasting.
- No bridge, swap, x402 settlement, exchange order, or money movement.
- No live Telegram/X/LinkedIn/Substack posting without an operator-reviewed
  posting path.
