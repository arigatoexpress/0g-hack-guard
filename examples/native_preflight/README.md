# Native Preflight Examples

These examples show how another app can call 0guard before it reaches a wallet,
agent signer, dWallet, x402 settlement path, or Telegram/TON approval prompt.

## Run Locally

Start the API:

```bash
python3 -m guard0.cli serve --port 8109
```

Run the Python CI-style gate:

```bash
python3 examples/native_preflight/python_client.py
```

Use the TypeScript helper from a browser, worker, or Node app that already has
`fetch` available.

## Safety

The examples never import keys, never sign, never settle payments, never place
orders, and never send messages. They only request an allow/review/deny verdict
from `/api/native-preflight`.
