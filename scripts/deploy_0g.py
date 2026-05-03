#!/usr/bin/env python3
"""
Deploy PolicyReceiptAnchor to 0G Chain.

Usage:
    export PRIVATE_KEY=0x...
    python3 scripts/deploy_0g.py --network testnet

Networks:
    testnet -> 0G-Galileo-Testnet (Chain ID 16601)
    mainnet -> 0G-Aristotle-Mainnet (Chain ID 16661)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from web3 import Web3
from eth_account import Account

NETWORKS = {
    "testnet": {
        "rpc": "https://evmrpc-testnet.0g.ai",
        "chain_id": 16601,
        "explorer": "https://chainscan-galileo.0g.ai",
    },
    "mainnet": {
        "rpc": "https://evmrpc.0g.ai",
        "chain_id": 16661,
        "explorer": "https://chainscan.0g.ai",
    },
}


def deploy(network: str, private_key: str) -> dict:
    cfg = NETWORKS[network]
    w3 = Web3(Web3.HTTPProvider(cfg["rpc"]))
    account = Account.from_key(private_key)

    # Load compiled artifact
    artifact_path = os.path.join(
        os.path.dirname(__file__), "..", "contracts", "PolicyReceiptAnchor.json"
    )
    with open(artifact_path) as f:
        artifact = json.load(f)
    abi = artifact["abi"]
    bytecode = artifact["bytecode"]["object"]

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = Contract.constructor().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 800000,
        "gasPrice": w3.to_wei("1", "gwei"),
        "chainId": cfg["chain_id"],
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "contract_address": receipt.contractAddress,
        "tx_hash": tx_hash.hex(),
        "explorer_url": f"{cfg['explorer']}/tx/{tx_hash.hex()}",
        "network": network,
        "chain_id": cfg["chain_id"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy PolicyReceiptAnchor to 0G")
    parser.add_argument("--network", choices=["testnet", "mainnet"], default="testnet")
    args = parser.parse_args()

    pk = os.getenv("PRIVATE_KEY")
    if not pk:
        print("ERROR: Set PRIVATE_KEY env var")
        return 1

    result = deploy(args.network, pk)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
