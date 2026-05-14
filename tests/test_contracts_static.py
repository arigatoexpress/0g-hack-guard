"""Static checks for Solidity receipt-anchor contracts."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_policy_receipt_anchor_v2_exposes_readable_receipt_fields():
    source = (REPO_ROOT / "contracts" / "PolicyReceiptAnchorV2.sol").read_text()

    assert "event ReceiptAnchoredV2" in source
    assert "function anchorReadable" in source
    assert "string shortMemo" in source
    assert "string sourceIds" in source
    assert "bytes32 datasetFingerprint" in source
    assert "bytes32 evidenceRoot" in source
    assert "bytes32 storageRoot" in source
    assert "Memo too long" in source
    assert "Source IDs too long" in source
    assert "private" not in source.lower()
    assert "tx.origin" not in source
