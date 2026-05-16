# 0guard: A Pre-Wallet Firewall For AI Agents

AI agents are getting wallets faster than they are getting judgment.

That is the reason I built 0guard.

The simple model is this: an agent asks to do something, 0guard checks the
intent before a wallet prompt appears, and the wallet stays out of it unless
the request earns a clean verdict.

Most crypto safety products appear when a signature is already on screen.
0guard moves the checkpoint earlier. It looks at intent, calldata, policy
context, domains, counterparties, labels, and source-linked exploit intelligence
before any signer is touched.

## What exists now

0guard now has a live Telegram Mini App, a public proof hub, a native preflight
API, a reputation probe, a developer kit, and a 0G mainnet receipt proof.

The live Mini App is here:

https://guard0-miniapp-s77j6bxyra-uc.a.run.app/telegram

The public proof packet is here:

https://arigatoexpress.github.io/0guard/hackathon-0g/

The current system checks agent and app intents, returns `allow`, `review`, or
`deny`, and can produce deterministic receipts that are ready for 0G proof
workflows. The Telegram surface can show wallet-alert and Mira-style
explanations, while keeping outbound Telegram sends disabled.

## What changed recently

The newest layer is a threat case file plus a frontier experiment lab.

`/api/threat-case-file`

This route takes one risky agent request and turns it into a proof dossier:
policy verdict, exploit signatures, reputation context, wallet-alert quality
gates, provenance coverage, signature coverage, and 0G-ready receipt hashes.
It is the cleanest way to explain what happened and why a signer should or
should not be touched.

`/api/experiments/frontier`

This route ranks the next integrations as safe experiments: 0G Storage
readback, GoPlus/Chainabuse/Forta reputation, Tenderly or BlockSec simulation,
Telegram/TON wallet context, 0G Compute shadow scoring, and Mira claim
verification. Each preview proves that live uploads, inference, sends, signing,
bridges, swaps, settlement, and raw payload resale are still off.

The existing no-network reputation connector manifest remains important:

`/api/reputation/connectors`

It turns the external-intelligence roadmap into something concrete. The current
activation plan covers GoPlus, Chainabuse, CryptoScamDB, Forta, TON Center,
TONAPI, Tenderly, BlockSec Phalcon, LayerZero Scan, and Wormholescan.

The important boundary is that 0guard does not pretend these paid or keyed feeds
are already live. It exposes the connector plan, use case, credential posture,
rights boundary, and applicability to the subject being checked. When these
feeds are activated, the system should return derived verdicts, source IDs,
confidence, links, hashes, and redacted addresses, not raw payload resale.

## What 0guard is not

0guard is not a wallet custodian.

It does not import private keys. It does not sign transactions. It does not
broadcast transactions. It does not bridge, swap, settle x402 payments, create
wallets, or place exchange orders from the workbench.

That is intentional. The product is the checkpoint before those systems.

## The roadmap

The next practical builds are:

1. Make the threat case file the default demo and operator review packet.
2. Enable one external reputation connector first, probably GoPlus or
   Chainabuse, behind reviewed credentials and derived-output tests.
3. Add operator-approved 0G Storage upload and readback for receipt payloads.
4. Add EVM simulation summaries from Tenderly or BlockSec.
5. Deepen Telegram and TON with read-only wallet risk passports.

The long-term goal is safety middleware for agentic crypto: a small,
deterministic preflight layer that wallets, agents, Mini Apps, x402 services,
dWallet systems, and deployment pipelines can call before a signer is ever
reached.

That is the wedge.

AI agents should not get to the wallet first.
