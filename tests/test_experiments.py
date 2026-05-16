"""Tests for the frontier experiment lab."""

import pytest

from guard0.experiments import frontier_experiments, run_frontier_experiment_preview


def test_frontier_experiments_are_ranked_and_non_mutating():
    lab = frontier_experiments()

    assert lab["schema"] == "0guard.frontier_experiments.v1"
    assert lab["mode"] == "frontier_lab_read_only"
    assert lab["experimentCount"] >= 6
    assert lab["recommendedSequence"][0] == "zero_g_storage_receipt_readback"
    assert lab["experiments"][0]["officialSources"]
    assert lab["safety"]["readOnly"] is True
    assert lab["safety"]["networkCalls"] is False
    assert lab["safety"]["transactionSigningEnabled"] is False
    assert lab["safety"]["telegramSendsEnabled"] is False
    assert lab["safety"]["moneyMovementEnabled"] is False
    assert lab["safety"]["rawPayloadsReturned"] is False


@pytest.mark.parametrize(
    ("experiment_id", "expected_key"),
    [
        ("zero_g_storage_receipt_readback", "storageReceipt"),
        ("reputation_connector_shadow", "connectors"),
        ("evm_simulation_delta_digest", "derivedDeltaDigest"),
        ("telegram_ton_activity_passport", "riskSignals"),
        ("zero_g_compute_shadow_score", "promptEnvelope"),
        ("mira_claim_verification_packet", "claims"),
    ],
)
def test_frontier_experiment_previews_are_safe_and_actionable(experiment_id, expected_key):
    preview = run_frontier_experiment_preview({"experimentId": experiment_id})

    assert preview["schema"] == "0guard.frontier_experiment_preview.v1"
    assert preview["mode"] == "no_side_effect_preview"
    assert preview["experiment"]["id"] == experiment_id
    assert expected_key in preview["preview"]
    assert preview["receipt"]["zeroGStorageReady"] is True
    assert preview["receipt"]["liveUploadPerformed"] is False
    assert preview["safety"]["networkCalls"] is False
    assert preview["safety"]["liveStorageUpload"] is False
    assert preview["safety"]["liveComputeInference"] is False
    assert preview["safety"]["transactionSigningEnabled"] is False
    assert preview["safety"]["telegramSendsEnabled"] is False
    assert preview["safety"]["socialPostingEnabled"] is False
    assert preview["safety"]["rawPayloadsReturned"] is False


def test_frontier_experiment_rejects_unknown_id():
    with pytest.raises(ValueError):
        run_frontier_experiment_preview({"experimentId": "not_real"})
