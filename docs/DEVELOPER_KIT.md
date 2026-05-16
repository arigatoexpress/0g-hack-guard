# 0guard Developer Kit

The most portable 0guard product is a small pre-signer guard: one deterministic
call that returns `allow`, `review`, or `deny` before an agent, wallet, dWallet,
payment rail, Telegram Mini App, or L2 deployment flow can request a signature.

## Local Quickstart

```bash
python3 -m guard0.cli serve --port 8109
```

```bash
python3 -m guard0.cli native-preflight \
  --payload-json '{"surface":"evm","operation":"read_status","chain":"eip155:8453"}'
```

Expected result: an `allow` verdict for read-only status checks, with a
0G-ready canonical receipt hash and no live anchor/upload side effects.

## API

```bash
curl -X POST http://127.0.0.1:8109/api/native-preflight \
  -H "Content-Type: application/json" \
  -d '{
    "surface": "ika_dwallets",
    "sourceProject": "ikavery",
    "operation": "sweep",
    "chain": "solana:devnet",
    "liveSigning": true,
    "intentText": "Autonomous agent proposes a recovery sweep through a dWallet signer."
  }'
```

Expected result: `deny`. The important product behavior is not that 0guard
understands every chain perfectly; it is that dangerous live signing paths fail
closed before the wallet or MPC signer is asked.

## Integration Recipes

Use `GET /api/developer-kit` for the machine-readable manifest. It includes:

- EVM agent/wallet recipe for AgentKit, Turnkey, Safe, and L2 apps.
- Ika, Ikavery, MPCKit, and OdWS dWallet preflight recipe.
- x402 prepared-payment recipe before settlement.
- Telegram/TON Mini App recipe before tonProof or transaction prompts.
- Arbitrum/EVM CI recipe for upgrades, grants, approvals, and deployments.

## Examples

- `examples/native_preflight/python_client.py`: stdlib Python CI/backend gate.
- `examples/native_preflight/nativePreflight.ts`: fetch-based TypeScript helper.

## Safety Boundary

The developer kit is read-only. It does not import keys, create wallets, sign,
settle payments, place exchange orders, bridge assets, post to social media, or
send Telegram messages. It returns a verdict and a receipt payload that a
separate, operator-approved production path can store or anchor.
