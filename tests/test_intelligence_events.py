"""Tests for the polling intelligence event snapshot."""

import pytest

from guard0.intelligence_events import intelligence_events_snapshot


def test_intelligence_events_snapshot_is_polling_and_read_only_without_network():
    snapshot = intelligence_events_snapshot(live=False, limit=5)

    assert snapshot["schema"] == "0guard.intelligence_events_snapshot.v1"
    assert snapshot["live"] is False
    assert snapshot["mode"] == "polling_snapshot_read_only"
    assert snapshot["streamingTransport"] == "none_yet"
    assert snapshot["liveReadsPerformed"]["sourceReachability"] == 0
    assert snapshot["liveReadsPerformed"]["rpcProbes"] == 0
    assert snapshot["sourceRegistry"]["sourceCount"] >= 8
    assert snapshot["safety"]["transactionSigningEnabled"] is False
    assert snapshot["safety"]["rawPayloadsReturned"] is False
    assert any("not mempool" in limit for limit in snapshot["honestLimits"])


def test_intelligence_events_snapshot_rejects_bad_limit():
    with pytest.raises(ValueError, match="limit must be between 1 and 50"):
        intelligence_events_snapshot(live=False, limit=0)
