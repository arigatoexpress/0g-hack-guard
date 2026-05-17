"""Tests for the read-only RV Raspberry Pi mesh snapshot collector."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rv_pi_mesh_snapshot.py"
SPEC = importlib.util.spec_from_file_location("rv_pi_mesh_snapshot", SCRIPT_PATH)
rv_pi_mesh_snapshot = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(rv_pi_mesh_snapshot)


def test_parse_peer_check_marks_ethernet_peer_ok():
    parsed = rv_pi_mesh_snapshot.parse_peer_check(
        "peer_wifi          fail 192.168.1.144\n"
        "peer_eth           ok 10.77.4.12\n"
        "eth0_carrier       1\n"
    )

    assert parsed["peer_wifi"]["ok"] is False
    assert parsed["peer_eth"]["ok"] is True
    assert parsed["peer_eth"]["target"] == "10.77.4.12"
    assert parsed["eth0_carrier"]["ok"] is True


def test_cluster_blockers_keep_unverified_peer_blocked():
    blockers = rv_pi_mesh_snapshot.cluster_blockers(
        {
            "reachable": True,
            "edgeApiReady": True,
            "eth0": {"carrier": True},
        },
        {
            "ethernetReachable": True,
            "identityVerified": False,
            "edgeApiReady": False,
        },
    )

    assert blockers == ["rvpi_b_identity_unverified", "rvpi_b_edge_api_not_ready"]


def test_peer_status_distinguishes_unverified_ssh_from_online_health():
    ports = {"22": {"ok": True}}

    assert (
        rv_pi_mesh_snapshot.peer_status(ports, None)
        == "ethernet_ssh_reachable_identity_unverified"
    )
    assert rv_pi_mesh_snapshot.peer_status(ports, {"hostname": "rvpi-b"}) == "online_verified"
