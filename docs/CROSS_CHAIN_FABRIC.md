# 0guard Cross-Chain Integration Fabric

0guard now exposes a read-only integration fabric for expansion beyond 0G while
preserving the same proof-first safety posture.

## What Is Live In This Repo

- `/api/integrations/cross-chain` returns a source-cited catalog for 0G
  mainnet, Base, Arbitrum, Polygon, MegaETH, Monad, HyperEVM, Tempo, and
  Celestia/TIA.
- `/api/integrations/cross-chain/readiness` returns catalog readiness by
  default; add `?live=1` to run read-only EVM JSON-RPC probes on configured
  default endpoints.
- `/api/integrations/virtuals-facilitator` returns a deployable manifest for a
  `0guard Facilitator` agent on Base/Virtuals, but does not launch it.

## Honest Network Posture

| Target | Current 0guard role | Live claim allowed |
|---|---|---|
| 0G Mainnet | Receipt proof anchor and eventual Storage proof lane | Yes: mainnet receipt proof is live |
| Base | Virtuals agent identity and x402-first payment lane | Prepared, not launched |
| Polygon PoS | x402 supported payment/readiness lane | Prepared, not live settlement |
| Arbitrum One | x402 supported payment/readiness lane | Prepared, not live settlement |
| MegaETH | Fast EVM testnet/readiness lane | Read-only testnet probes only |
| Monad | EVM expansion watchlist | Catalog plus env-configured probes only |
| HyperEVM | HYPE ecosystem EVM guardrail lane | Read-only probes only |
| Tempo | Payment-chain watchlist | Testnet/readiness only |
| Celestia/TIA | Data availability and Blobstream proof lane | DA/proof lane, not EVM settlement |

## Payment And Agent Boundaries

x402 is a good fit for paid access to derived threat-intelligence artifacts, but
payment is not permission. Paid endpoints should sell:

- derived threat-receipt packets;
- source IDs and links;
- detector coverage and gaps;
- provenance hashes and receipt proofs;
- cross-chain readiness checklists.

They should not sell raw upstream OSINT payload mirrors or imply that payment
authorizes private scraping.

Virtuals/Base integration is prepared as an agent manifest only. Any live
Virtuals launch, token action, x402 settlement, bridge, swap, or wallet
signature is an external side effect and requires an explicit operator run.

## Readable Tx Log Upgrade

The current `PolicyReceiptAnchor` event already exposes readable `decision`,
`severity`, `agentId`, `timestamp`, and `submitter` fields. The next contract
upgrade is drafted at `contracts/PolicyReceiptAnchorV2.sol`. It keeps the full
receipt JSON in Storage or another content-addressed artifact store and emits
concise readable fields on-chain:

- `receiptHash`
- `decision`
- `severity`
- `agentId`
- `policyVersion`
- `datasetFingerprint`
- `evidenceRoot`
- `storageRoot`
- `shortMemo`
- `sourceIds`

Example `shortMemo`: `Blocked unlimited ERC20 approval before signer`.

That gives explorers useful human context without turning chain logs into a raw
database.
