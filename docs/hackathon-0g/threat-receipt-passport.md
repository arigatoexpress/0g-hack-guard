# Threat Receipt Passport

This is the judge-facing proof drill for 0guard. It compresses the product into
one falsifiable flow: agent intent in, safety verdict out, receipt hash created,
source evidence attached, and 0G proof fields made explicit.

## Passport Fields

| Field | Current value |
|---|---|
| Product | `0guard` |
| Track | `Track 5: Privacy & Sovereign Infrastructure` |
| Agent session | `agent-7857-demo` |
| Sample intent | Unlimited ERC-20 approval in `live_transaction` mode |
| Expected verdict | `deny` |
| Expected severity | `critical` |
| Detector hits | `critical_selector:approve(address,uint256)`, `unlimited_approval` |
| Provenance layer | `/api/data/provenance` and canonical dataset evidence |
| Receipt hash | returned by `/api/evaluate` |
| 0G Chain status today | `preflight` until operator mainnet deployment |
| 0G Storage status today | Storage-ready root hash and payload, no default upload |
| HackQuest-final gap | 0G mainnet contract address and Explorer URL |

## Reproduce Locally

Start the server:

```bash
cd /Users/aribs/Code/0guard
.venv/bin/python -m guard0.app
```

Create the passport receipt:

```bash
curl -s http://127.0.0.1:8109/api/hackathon/threat-passport | python3 -m json.tool
```

Or run the underlying evaluation route directly:

```bash
curl -s -X POST http://127.0.0.1:8109/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {
      "action": "approve",
      "mode": "live_transaction",
      "requires_signature": true,
      "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    },
    "enable_0g_anchor": true,
    "enable_0g_storage": true,
    "agent_id": "agent-7857-demo"
  }' | python3 -m json.tool
```

Expected proof fields:

- `decision: deny`
- `severity: critical`
- `zero_g.chain_anchor.status: preflight`
- `zero_g.chain_anchor.chain_id: 16602` unless mainnet env vars are configured
- `zero_g.storage_receipt.root_hash`
- `receipt_hash`

Check source evidence:

```bash
curl -s http://127.0.0.1:8109/api/data/provenance | python3 -m json.tool
curl -s 'http://127.0.0.1:8109/api/data/provenance?live=1' | python3 -m json.tool
```

Check final readiness:

```bash
.venv/bin/python scripts/submission_readiness.py --format markdown
```

## Mainnet Completion Slot

After Ari deploys and anchors a receipt on 0G mainnet, fill these fields before
final HackQuest submission:

```text
0G_MAINNET_CONTRACT_ADDRESS=
0G_MAINNET_EXPLORER_URL=
ANCHORED_RECEIPT_HASH=
ANCHOR_TRANSACTION_HASH=
```

Do not present this passport as HackQuest-valid mainnet proof until those fields
exist and the explorer link opens publicly.
