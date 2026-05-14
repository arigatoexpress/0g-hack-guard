#!/usr/bin/env python3
"""
Deploy PolicyReceiptAnchor to 0G Chain.

Usage:
    export PRIVATE_KEY=0x...
    python3 scripts/deploy_0g.py --network testnet
    python3 scripts/deploy_0g.py --network mainnet --private-key-file ~/.0guard-secrets/wallets/deployer.private-key

Networks:
    testnet -> 0G-Galileo-Testnet (live RPC Chain ID 16602)
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
        "chain_id": 16602,
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
    w3 = Web3(Web3.HTTPProvider(cfg["rpc"], request_kwargs={"timeout": 30}))
    account = Account.from_key(private_key)
    if int(w3.eth.chain_id) != cfg["chain_id"]:
        raise RuntimeError(f"RPC chain ID mismatch for {network}: {w3.eth.chain_id}")

    # Load compiled artifact
    artifact_path = os.path.join(
        os.path.dirname(__file__), "..", "contracts", "PolicyReceiptAnchor.json"
    )
    with open(artifact_path) as f:
        artifact = json.load(f)
    abi = artifact["abi"]
    bytecode = artifact["bytecode"]["object"]

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    sender = Web3.to_checksum_address(account.address)
    constructor = Contract.constructor()
    gas_estimate = constructor.estimate_gas({"from": sender})
    gas_price = int(w3.eth.gas_price)
    nonce = w3.eth.get_transaction_count(sender, "pending")
    tx = constructor.build_transaction({
        "from": sender,
        "nonce": nonce,
        "gas": int(gas_estimate * 1.25) + 50_000,
        "gasPrice": gas_price,
        "chainId": cfg["chain_id"],
    })
    max_cost = tx["gas"] * gas_price
    balance = w3.eth.get_balance(sender)
    if max_cost > balance:
        raise RuntimeError(
            "insufficient native token for deployment max cost: "
            f"need {w3.from_wei(max_cost, 'ether')}, have {w3.from_wei(balance, 'ether')}"
        )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "contract_address": receipt.contractAddress,
        "tx_hash": tx_hash.hex(),
        "explorer_url": f"{cfg['explorer']}/tx/{tx_hash.hex()}",
        "network": network,
        "chain_id": cfg["chain_id"],
        "deployer": sender,
        "gas_used": receipt.gasUsed,
        "gas_price_wei": gas_price,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy PolicyReceiptAnchor to 0G")
    parser.add_argument("--network", choices=["testnet", "mainnet"], default="testnet")
    parser.add_argument(
        "--private-key-file",
        help="Read the deployer private key from a local secure file instead of PRIVATE_KEY.",
    )
    args = parser.parse_args()

    pk = None
    if args.private_key_file:
        with open(os.path.expanduser(args.private_key_file), encoding="utf-8") as handle:
            pk = handle.read().strip()
    else:
        pk = os.getenv("PRIVATE_KEY")
    if not pk:
        print("ERROR: Set PRIVATE_KEY env var or pass --private-key-file")
        return 1

    result = deploy(args.network, pk)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
