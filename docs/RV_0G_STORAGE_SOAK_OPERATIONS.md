# RV 0G Storage Soak Operations

Updated: May 17, 2026.

This runbook connects the live RV Windows storage node to ZeroGuard without
turning the workbench into a signer, wallet, Telegram sender, or node-control
panel.

## Current Operating Shape

| Surface | Role |
| --- | --- |
| Windows host | Runs the 0G mainnet storage node inside WSL. |
| FRP relay | Publishes storage P2P on `35.254.123.37:1234`. |
| ZeroGuard collector | Reads process/task/RPC/balance state over SSH and public RPC. |
| ZeroGuard workbench | Displays the latest local snapshot and blocks funding expansion. |

## Refresh The Local Snapshot

From the repo root:

```bash
./scripts/rv_0g_storage_soak_snapshot.py --out content/rv_0g_storage_soak.local.json
```

The output file is intentionally ignored by git. It can contain public wallet
addresses, balances, task names, block heights, and relay health, but it must
never contain private keys, mnemonics, API tokens, or Telegram send capability.

## Read It Through The Workbench

```bash
curl 'http://127.0.0.1:8109/api/0g/storage-node/status?snapshot=1'
```

The browser button is **0G Node Ops -> Storage soak**. It reads the same route
and shows:

- `funded_soak_syncing` while the node is funded only with the small test
  amount and still catching up;
- `activeMinerBalanceOg` for the monitored miner public address;
- `onlyPriorTestFundingObserved`;
- `hundredOgTransferSent`;
- DB size, sync gap, relay state, connected peers, and expansion blockers.

## Expansion Blockers

Do not send larger mainnet funds until these are clear:

- `storage_log_sync_gap_too_large`
- `connected_peers_below_target_8`
- `public_storage_tcp_relay_unreachable`
- `adjacent_da_relay_task_not_running`
- any balance result other than the prior `0.25 0G` test amount on the active
  miner

The DA relay blocker is tracked separately because it gates the future DA lane,
not the storage node's current P2P relay on `1234`.

## Safety Boundary

The collector is read-only. It does not read or return private key material,
does not sign, does not broadcast, does not transfer funds, and does not send
Telegram messages. Any Router deposit, miner top-up, validator action, staking,
delegation, or provider sub-account transfer still needs its own exact manifest
and final confirmation.
