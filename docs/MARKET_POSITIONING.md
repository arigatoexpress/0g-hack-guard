# 0guard Market Positioning

## Position

0guard is an AI-agent pre-wallet firewall: it converts autonomous crypto intent
into a dry-run, explainable policy verdict before any signer, Telegram send, or
external action is allowed.

The wedge is not "another wallet scanner." The wedge is agent runtime safety:
goal, prompt, calldata, policy, exploit signatures, receipt proof, and explicit
operator-controlled escalation.

## Why Now

- Agent wallets and onchain agent tooling are becoming real infrastructure.
  Coinbase AgentKit gives agents wallet and onchain action capabilities:
  https://docs.cdp.coinbase.com/agent-kit/welcome
- Turnkey positions agentic wallets around programmable policy and signing
  control:
  https://docs.turnkey.com/products/embedded-wallets/features/agentic-wallets
- Losses remain large enough for judges to immediately understand the problem.
  Chainalysis reported over $3.4B in stolen crypto in 2025:
  https://www.chainalysis.com/blog/crypto-hacking-stolen-funds-2026/
- Hacken's Q1 2026 report calls out AI/Web3 risks around wallet signer abuse,
  irreversibility, and MEV exposure:
  https://hacken.io/insights/q1-2026-security-report/

## 0G Fit

0G is positioned as blockchain infrastructure for AI agents:
https://0g.ai/

0guard uses that angle in a way judges can verify:

- Live read-only 0G Galileo RPC status in `/api/0g/status`.
- Receipt hashes that can be anchored to 0G Chain once an operator deploys the
  contract.
- Deterministic threat-intel payloads/root hashes ready for 0G Storage.
- No custody, no signing, no broadcast, no fake "autonomous trading" claim.

Useful 0G references:

- Galileo testnet docs:
  https://docs.0g.ai/developer-hub/testnet/testnet-overview
- 0G Storage SDK and proof flows:
  https://docs.0g.ai/developer-hub/building-on-0g/storage/sdk

## Competitive Landscape

| Alternative | Strength | 0guard angle |
|---|---|---|
| Blockaid | Transaction validation, wallet integrations, EIP-712/EIP-4337 coverage: https://www.blockaid.io/transaction-security | 0guard gates agent intent before a wallet/security API sees a transaction. |
| Blowfish | Transaction and message simulation APIs used by wallets: https://blowfish.xyz/ | 0guard adds agent context: prompt, goal, tool plan, and policy. |
| Webacy | Transaction, approval, wallet, and poisoning risk APIs: https://docs.webacy.com/guides/transaction-simulation | Webacy can be an upstream signal; 0guard is the policy brain. |
| GoPlus | Token/security and transaction simulation APIs: https://docs.gopluslabs.io/docs/getting-started | GoPlus can enrich signals; 0guard controls the agent workflow. |
| Forta | Real-time threat detection and firewall positioning: https://www.forta.org/ | Forta protects networks/protocols; 0guard protects the agent action pipeline. |
| Harpie | Wallet firewall/recovery posture: https://harpie.io/ | Human-wallet protection; 0guard protects autonomous agent actions. |
| Rabby/Tenderly | Simulation, preview, and debugging: https://www.rabby.is/en/features.html and https://docs.tenderly.co/ | Simulation is one input; 0guard converts findings into enforceable agent policy. |

## OSINT Wedge

The next product edge is a provenance-backed evidence layer for agents:

1. Fetch or catalog public source leads from DeFiLlama, Chainalysis, Forta,
   CryptoScamDB, Rekt, SlowMist, and other reviewed feeds.
2. Preserve source owner, URL, rights envelope, TTL, caveats, and normalized
   record hashes.
3. Convert source signals into detector coverage and human-readable gaps.
4. Return guardrail decisions with evidence, confidence, and a 0G receipt path.

This is how 0guard avoids becoming a thin wallet-warning clone. It is the
agent-readable layer that explains why an action is blocked and what evidence
supports the verdict.

## Demo Message

The strongest short pitch:

1. AI agents are gaining wallets faster than safety controls are maturing.
2. 0guard intercepts intent before the signing key.
3. It checks exploit signatures, behavioral risks, calldata, and domain posture.
4. It returns allow/review/deny plus a receipt hash.
5. It proves the 0G Galileo connection live without a private key.
6. Telegram Mira adds a user-facing opt-in channel without surprise sends.

Judge-safe claim:

> 0guard does not custody funds. It gates agent behavior before custody risk
> begins.
