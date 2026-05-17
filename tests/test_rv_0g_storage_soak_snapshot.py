"""Tests for the read-only RV 0G storage soak snapshot collector."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rv_0g_storage_soak_snapshot.py"
SPEC = importlib.util.spec_from_file_location("rv_0g_storage_soak_snapshot", SCRIPT_PATH)
assert SPEC and SPEC.loader
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


def test_expansion_blockers_keep_large_funding_gated():
    blockers = snapshot.expansion_blockers_for(
        storage_rpc={"status": "ok", "connectedPeers": 4},
        relay={"tcp1234": {"ok": True}},
        tasks={
            "0GStorageMainnetFunded": {"Status": "Running"},
            "0GStorageRelayFrpc": {"Status": "Running"},
            "0GDaRelayTunnel": {"Status": "Ready"},
        },
        process={"running": True},
        config={"minerKeyPresent": True},
        sync_gap=7_239_411,
        balances={"activeMiner": {"balanceOg": 0.25}},
    )

    assert "connected_peers_below_target_8" in blockers
    assert "storage_log_sync_gap_too_large" in blockers
    assert "adjacent_da_relay_task_not_running" in blockers
    assert "active_config_missing_miner_key" not in blockers


def test_expansion_blockers_notice_unexpected_miner_balance():
    blockers = snapshot.expansion_blockers_for(
        storage_rpc={"status": "ok", "connectedPeers": 8},
        relay={"tcp1234": {"ok": True}},
        tasks={
            "0GStorageMainnetFunded": {"Status": "Running"},
            "0GStorageRelayFrpc": {"Status": "Running"},
            "0GDaRelayTunnel": {"Status": "Running"},
        },
        process={"running": True},
        config={"minerKeyPresent": True},
        sync_gap=99,
        balances={"activeMiner": {"balanceOg": 100.25}},
    )

    assert blockers == ["active_miner_balance_not_prior_test_amount"]


def test_schtasks_parser_and_redaction_are_public_safe():
    parsed = snapshot.parse_schtasks_list(
        "TaskName: \\\\0GStorageMainnetFunded\n"
        "Status: Running\n"
        "Task To Run: wsl.exe -d Ubuntu-24.04 -- start.sh\n"
    )
    command = snapshot.redact_command("./bin/zgs_node --miner-key 0xabc --other ok")

    assert parsed["TaskName"] == "\\\\0GStorageMainnetFunded"
    assert parsed["Status"] == "Running"
    assert "0xabc" not in command
    assert "<redacted>" in command
