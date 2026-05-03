# 🚀 PolicyReceiptAnchor Deployment Guide

> Deploy the `PolicyReceiptAnchor` smart contract to **0G Testnet (Galileo)** or **0G Mainnet (Aristotle)**.

---

## 1. Pre-Deployment Checklist

Before you start, make sure you have the following ready:

| # | Requirement | Details |
|---|-------------|---------|
| 1 | **EVM Wallet** | MetaMask, Rabby, or any EVM-compatible wallet. Create a new wallet or use a dedicated deployer address. **Do not reuse a wallet that holds mainnet funds.** |
| 2 | **Wallet funded with 0G** | Testnet: Request from [https://faucet.0g.ai](https://faucet.0g.ai) (0.1 0G/day per wallet). Mainnet: Acquire 0G via exchange or bridge. |
| 3 | **Python environment** | Python ≥3.10 with the project installed: `python3 -m pip install -e '.[dev]'` |
| 4 | **`PRIVATE_KEY` env var** | Export your deployer private key (with `0x` prefix). **Never commit this to git.** |
| 5 | **Verify artifact exists** | `contracts/PolicyReceiptAnchor.json` must contain the compiled ABI + bytecode. |

### Quick Pre-Flight

```bash
cd /Users/aribs/Code/0g-hack-guard

# 1. Check Python
python3 --version  # >= 3.10

# 2. Check dependencies are installed
python3 -c "import web3, eth_account; print('web3:', web3.__version__)"

# 3. Verify artifact exists
ls contracts/PolicyReceiptAnchor.json

# 4. Set your private key (DO NOT paste into committed files)
export PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

# 5. Check wallet balance (testnet example)
python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://evmrpc-testnet.0g.ai'))
addr = w3.eth.account.from_key('$PRIVATE_KEY').address
print('Address:', addr)
print('Balance:', w3.from_wei(w3.eth.get_balance(addr), 'ether'), '0G')
"
```

---

## 2. Step-by-Step Deployment (Python Script)

The recommended deployment path uses the included Python script: `scripts/deploy_0g.py`.

### 2.1 Deploy to Testnet (Galileo)

```bash
cd /Users/aribs/Code/0g-hack-guard
export PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE

python3 scripts/deploy_0g.py --network testnet
```

**Expected output:**
```json
{
  "contract_address": "0x...",
  "tx_hash": "0x...",
  "explorer_url": "https://chainscan-galileo.0g.ai/tx/0x...",
  "network": "testnet",
  "chain_id": 16601
}
```

### 2.2 Deploy to Mainnet (Aristotle)

```bash
export PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
python3 scripts/deploy_0g.py --network mainnet
```

**Expected output:**
```json
{
  "contract_address": "0x...",
  "tx_hash": "0x...",
  "explorer_url": "https://chainscan.0g.ai/tx/0x...",
  "network": "mainnet",
  "chain_id": 16661
}
```

### 2.3 What the Script Does

1. Connects to the selected RPC (`https://evmrpc-testnet.0g.ai` or `https://evmrpc.0g.ai`).
2. Loads the compiled artifact from `contracts/PolicyReceiptAnchor.json`.
3. Builds a deployment transaction with:
   - `gas: 800_000`
   - `gasPrice: 1 gwei`
   - `chainId`: 16601 (testnet) or 16661 (mainnet)
4. Signs and broadcasts the transaction.
5. Waits up to 120 seconds for confirmation.
6. Prints the deployed contract address + explorer link.

---

## 3. Alternative: Foundry Deployment

If you prefer Foundry (`forge`), you can deploy with a one-liner using the compiled artifact.

### Prerequisites
- [Foundry](https://book.getfoundry.sh/getting-started/installation) installed (`forge`, `cast`)
- `ETHERSCAN_API_KEY` or equivalent is **not required** for basic deployment.

### 3.1 Extract Bytecode from Artifact

```bash
cd /Users/aribs/Code/0g-hack-guard

# Extract the raw bytecode (strip leading "0x" if needed for forge)
BYTECODE=$(python3 -c "import json; print(json.load(open('contracts/PolicyReceiptAnchor.json'))['bytecode']['object'])")
echo $BYTECODE
```

### 3.2 Deploy with `forge create`

**Testnet:**
```bash
forge create \
  --rpc-url https://evmrpc-testnet.0g.ai \
  --private-key $PRIVATE_KEY \
  --chain-id 16601 \
  --broadcast \
  contracts/PolicyReceiptAnchor.sol:PolicyReceiptAnchor
```

**Mainnet:**
```bash
forge create \
  --rpc-url https://evmrpc.0g.ai \
  --private-key $PRIVATE_KEY \
  --chain-id 16661 \
  --broadcast \
  contracts/PolicyReceiptAnchor.sol:PolicyReceiptAnchor
```

> **Note:** If `forge create` cannot locate the source file directly, use the JSON artifact path with `jq` to feed bytecode:
> ```bash
> forge create \
>   --rpc-url https://evmrpc-testnet.0g.ai \
>   --private-key $PRIVATE_KEY \
>   --chain-id 16601 \
>   $(echo $BYTECODE | sed 's/^0x//')
> ```

---

## 4. Verification Steps

After deployment, verify the contract is live and accessible on 0G Explorer.

### 4.1 Check Transaction on Explorer

Open the `explorer_url` from the deployment output:
- Testnet: `https://chainscan-galileo.0g.ai/tx/<TX_HASH>`
- Mainnet: `https://chainscan.0g.ai/tx/<TX_HASH>`

Confirm:
- Status: **Success**
- Contract Address: displayed in the "To" or "Contract Creation" field
- Gas Used: ~300k–600k (well within the 800k limit)

### 4.2 Verify Contract Source (Explorer)

0G Explorer supports Solidity source verification. To verify:

1. Go to the contract address page on the explorer.
2. Click **"Verify & Publish"** (or similar).
3. Select:
   - **Compiler:** `v0.8.20+commit.a1b79de6` (as noted in `PolicyReceiptAnchor.json` metadata)
   - **License:** MIT
   - **Optimization:** Disabled (matches the artifact: `"optimizer": { "enabled": false }`)
4. Paste the full source from `contracts/PolicyReceiptAnchor.sol`.
5. Submit and wait for confirmation.

### 4.3 Smoke Test via `cast` or Python

**Using `cast` (Foundry):**
```bash
# Replace with your deployed address
CONTRACT=0xYOUR_DEPLOYED_ADDRESS

# Check total receipts (should be 0)
cast call $CONTRACT "totalReceipts()(uint256)" --rpc-url https://evmrpc-testnet.0g.ai
```

**Using Python:**
```python
from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://evmrpc-testnet.0g.ai"))

with open("contracts/PolicyReceiptAnchor.json") as f:
    abi = json.load(f)["abi"]

contract = w3.eth.contract(address="0xYOUR_DEPLOYED_ADDRESS", abi=abi)
print("Total receipts:", contract.functions.totalReceipts().call())
```

---

## 5. Post-Deployment Config

After deploying, update the Python application so it anchors receipts to the live contract instead of returning pre-flight stubs.

### 5.1 Environment Variables

Set these in your shell, `.env` file, or deployment platform:

| Variable | Testnet Value | Mainnet Value |
|----------|---------------|---------------|
| `ZGG_CHAIN_RPC` | `https://evmrpc-testnet.0g.ai` | `https://evmrpc.0g.ai` |
| `ZGG_CHAIN_ID` | `16601` | `16661` |
| `ZGG_RECEIPT_CONTRACT` | `0xYOUR_TESTNET_CONTRACT_ADDRESS` | `0xYOUR_MAINNET_CONTRACT_ADDRESS` |

### 5.2 Update `src/guard0/chain.py`

The app currently defaults to placeholder values. After deployment, update **or** override via env vars:

```bash
# Preferred: export env vars (no code change needed)
export ZGG_CHAIN_RPC="https://evmrpc-testnet.0g.ai"
export ZGG_CHAIN_ID=16601
export ZGG_RECEIPT_CONTRACT="0xYOUR_DEPLOYED_CONTRACT_ADDRESS"
```

If you want to hardcode defaults for a specific environment, edit `src/guard0/chain.py`:

```python
# Example: hardcoded testnet defaults
ZGG_CHAIN_RPC = os.getenv("ZGG_CHAIN_RPC", "https://evmrpc-testnet.0g.ai")
ZGG_CHAIN_ID = int(os.getenv("ZGG_CHAIN_ID", "16601"))
ZGG_RECEIPT_CONTRACT = os.getenv(
    "ZGG_RECEIPT_CONTRACT",
    "0xYOUR_DEPLOYED_CONTRACT_ADDRESS",  # <-- replace placeholder
)
```

### 5.3 Verify App Integration

Restart the app and confirm the health endpoint reflects the new contract:

```bash
python3 -m guard0.cli serve --port 8109 &
curl http://127.0.0.1:8109/api/health
```

Expected response should show the correct `chain_id` and contract address in the 0G config section.

---

## 6. Troubleshooting Guide

| Error / Symptom | Likely Cause | Fix |
|-----------------|--------------|-----|
| `ERROR: Set PRIVATE_KEY env var` | `PRIVATE_KEY` not exported | `export PRIVATE_KEY=0x...` |
| `insufficient funds for gas * price + value` | Wallet has < 0.1 0G | Visit [faucet.0g.ai](https://faucet.0g.ai) for testnet; fund wallet for mainnet. |
| `wrong chain id` | `chainId` mismatch in tx vs. network | Ensure `--network` flag matches the RPC (testnet = 16601, mainnet = 16661). |
| `RPC timeout` / `ConnectionError` | 0G RPC is slow or rate-limited | Retry after 10–30 seconds. Test RPC health: `curl -X POST https://evmrpc-testnet.0g.ai -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'` |
| `nonce too low` | Previous tx pending or already mined | Check wallet nonce on explorer; wait for pending tx or manually set nonce. |
| `receipt.contractAddress is None` | Tx failed (out of gas, revert, etc.) | Check explorer for revert reason. Increase `gas` in script if needed. |
| `ModuleNotFoundError: No module named 'web3'` | Dependencies not installed | Run `python3 -m pip install -e '.[dev]'` inside project root. |
| `FileNotFoundError: PolicyReceiptAnchor.json` | Contract not compiled | Ensure the JSON artifact exists at `contracts/PolicyReceiptAnchor.json`. Recompile with Foundry if missing. |
| `Receipt already anchored` (contract revert) | Duplicate `receiptHash` submitted | The contract enforces uniqueness on `receiptHash`. Generate a unique hash per evaluation. |

### Debug Script

Run this to test connectivity before deploying:

```bash
python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://evmrpc-testnet.0g.ai'))
print('Connected:', w3.is_connected())
print('Block:', w3.eth.block_number)
print('Chain ID:', w3.eth.chain_id)
"
```

---

## 7. Mainnet Migration Checklist

When you're ready to move from testnet to mainnet, complete this checklist:

- [ ] **Re-audit the contract** — Even though `PolicyReceiptAnchor.sol` is minimal, consider a lightweight review before mainnet.
- [ ] **Fund mainnet deployer wallet** — Acquire real 0G tokens via exchange or bridge.
- [ ] **Use a fresh deployer key** — Do not reuse testnet keys that may have been exposed in logs or CI.
- [ ] **Run the mainnet deployment**:
  ```bash
  export PRIVATE_KEY=0xMAINNET_DEPLOYER_KEY
  python3 scripts/deploy_0g.py --network mainnet
  ```
- [ ] **Verify contract on mainnet explorer** — `https://chainscan.0g.ai`
- [ ] **Update production env vars**:
  ```bash
  export ZGG_CHAIN_RPC="https://evmrpc.0g.ai"
  export ZGG_CHAIN_ID=16661
  export ZGG_RECEIPT_CONTRACT="0xMAINNET_CONTRACT_ADDRESS"
  ```
- [ ] **Rotate any testnet credentials** — If the same infra handles both networks, isolate them.
- [ ] **Monitor first anchor tx** — Submit a test receipt and verify it appears on-chain via `getReceipt()`.
- [ ] **Document the mainnet contract address** — Add it to README, runbooks, and any frontend configs.
- [ ] **Back up the deployer mnemonic/key** — Store offline in a password manager or hardware wallet.

---

## Quick Reference

| Network | Chain ID | RPC | Explorer | Faucet |
|---------|----------|-----|----------|--------|
| Testnet (Galileo) | 16601 | `https://evmrpc-testnet.0g.ai` | `https://chainscan-galileo.0g.ai` | [faucet.0g.ai](https://faucet.0g.ai) |
| Mainnet (Aristotle) | 16661 | `https://evmrpc.0g.ai` | `https://chainscan.0g.ai` | — |

| File | Purpose |
|------|---------|
| `contracts/PolicyReceiptAnchor.sol` | Solidity source |
| `contracts/PolicyReceiptAnchor.json` | Compiled ABI + bytecode |
| `scripts/deploy_0g.py` | Python deployment script |
| `src/guard0/chain.py` | App integration point (env vars) |
| `foundry/foundry.toml` | Foundry config (default chain_id = 16601) |

---

*Last updated: 2026-05-03*
