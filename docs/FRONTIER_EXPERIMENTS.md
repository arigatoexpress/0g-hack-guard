# 0guard Frontier Experiments

The frontier lab is where research becomes a safe product experiment. It does
not perform live uploads, inference, signing, broadcasts, Telegram sends,
social posts, bridge transfers, swaps, payment settlement, or exchange orders.

## Live Routes

| Route | Purpose |
|---|---|
| `/api/experiments/frontier` | Ranked experiment backlog with official source links and activation order. |
| `/api/experiments/run` | Deterministic preview for one experiment. |

## Current Experiments

1. `zero_g_storage_receipt_readback` prepares the exact 0G Storage receipt
   payload and readback plan while keeping `stored: false`.
2. `reputation_connector_shadow` starts with open PhishDestroy,
   CryptoScamDB, and Forta labelled evidence, then ranks GoPlus, Chainabuse,
   TON, simulation, and cross-chain connectors for the subject without network
   calls.
3. `evm_simulation_delta_digest` turns a local native preflight into a
   synthetic state-delta digest that shows the future Tenderly/BlockSec shape
   without storing raw traces.
4. `telegram_ton_activity_passport` generates a TON risk passport with syntax
   and policy only; no `sendTransaction`, `signData`, or `tonProof`.
5. `zero_g_compute_shadow_score` builds a redacted prompt envelope and
   deterministic local score instead of calling 0G Compute.
6. `mira_claim_verification_packet` creates a Mira-ready claim packet with
   evidence hashes and no external Mira call.

## Official Sources Used For The Roadmap

- 0G Storage SDK: `https://docs.0g.ai/developer-hub/building-on-0g/storage/sdk`
- 0G Compute inference: `https://docs.0g.ai/developer-hub/building-on-0g/compute-network/inference`
- GoPlus: `https://docs.gopluslabs.io/`
- Chainabuse Get Reports: `https://docs.chainabuse.com/docs/get-reports-parameters`
- Forta GraphQL API: `https://docs.forta.network/en/latest/forta-api-reference/`
- Tenderly simulation docs: `https://docs.tenderly.co/`
- TON Center v3: `https://docs.ton.org/ecosystem/api/toncenter/v3/overview`
- Telegram Mini Apps validation: `https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app`

## Safety Contract

Every preview reports:

- `networkCalls: false`
- `liveStorageUpload: false`
- `liveComputeInference: false`
- `transactionSigningEnabled: false`
- `telegramSendsEnabled: false`
- `socialPostingEnabled: false`
- `bridgingEnabled: false`
- `moneyMovementEnabled: false`
- `rawPayloadsReturned: false`
