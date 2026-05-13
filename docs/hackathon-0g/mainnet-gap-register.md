# 0guard Mainnet Gap Register

This register keeps the hackathon submission honest. It separates what judges
can verify now from what remains before a production/mainnet launch.

## Verified or Demo-Ready Now

- Intent firewall: browser/API/CLI policy evaluation returns allow/review/deny
  verdicts. Evidence: `/api/evaluate`, `python3 -m guard0.cli evaluate`, and
  `scripts/demo_april_2026.py`.
- Incident signatures: April 2026 exploit signatures and behavioral checks are
  wired into the detector. Evidence: `data/april_2026_incidents.json` and
  `/api/data/detection-coverage`.
- Dataset validation: incident data is schema-checked, summarized,
  fingerprinted, and filterable. Evidence: `/api/data/summary` and
  `/api/data/incidents`.
- 0G Galileo read: live read-only RPC status check reports chain ID, latest
  block, latency, and safety flags. Evidence: `/api/0g/status`.
- 0G Chain payload: receipt anchor payloads are produced when
  `enable_0g_anchor=true`. Evidence: `zero_g.chain_anchor.status: preflight`.
- 0G Storage payload: Storage-ready receipts and deterministic root hashes are
  produced for matching threat intel. Evidence:
  `zero_g.storage_receipt.root_hash`.
- Telegram Mira preview: local opt-in and response preview exist without
  sending Telegram messages. Evidence: `/api/telegram/status` and
  `/api/telegram/mira-preview`.

## Mainnet/Testnet Gaps

- Receipt contract deployment: judges can inspect preflight payloads, but
  on-chain audit requires deployed bytecode. Next step: deploy
  `PolicyReceiptAnchor.sol` to 0G Galileo with a dedicated testnet deployer,
  then configure `ZGG_RECEIPT_CONTRACT`.
- On-chain verifier readback: a complete verifier loop must prove the receipt
  exists on-chain, not only that the payload was prepared. Next step: implement
  contract readback for receipt events or receipt-hash lookup and expose
  verified/not-verified status.
- Live 0G Storage upload: current Storage receipts are deterministic and
  Storage-ready but not uploaded by default. Next step: wire the 0G Storage
  SDK/gateway upload behind explicit operator config and add readback by key or
  root hash.
- 0G Compute scoring: current scoring is deterministic policy/signature logic,
  not live 0G Compute inference. Next step: add a Compute-backed anomaly scorer
  as an optional signal with clear provenance in the verdict.
- Key custody: the workbench correctly contains no private keys, but production
  anchoring needs signer custody. Next step: use a dedicated deployer/signer
  path outside the browser workbench, with explicit confirmation and no custody
  in repo.
- Mainnet launch: mainnet requires real tokens, audit, monitoring, and rollback
  plans. Next step: complete testnet verification first, then prepare a
  reversible mainnet runbook.

## Claims to Avoid

- Do not say 0guard is writing to 0G mainnet today.
- Do not say 0guard has live 0G Compute inference today.
- Do not say the workbench can deploy, sign, trade, bridge, or move funds.
- Do not imply Telegram messages are sent during the judge demo.
- Do not use "fully decentralized" until Storage upload, Chain anchoring, and
  verifier readback are live.

## Strong Honest Claim

0guard demonstrates the end-to-end safety architecture on 0G without crossing
dangerous boundaries: live Galileo read proof, deterministic policy receipts,
Chain anchor preflight, Storage-ready threat-intel receipts, and a clear path to
testnet/mainnet verification.
