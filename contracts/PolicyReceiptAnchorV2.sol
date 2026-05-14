// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PolicyReceiptAnchorV2
 * @notice Anchors 0guard policy receipts with explorer-readable context.
 * @dev Full receipt JSON should live in 0G Storage or another content-addressed
 *      artifact store. This contract keeps readable event fields plus hashes.
 */
contract PolicyReceiptAnchorV2 {
    struct Receipt {
        bytes32 receiptHash;
        string decision;
        string severity;
        string agentId;
        string policyVersion;
        bytes32 datasetFingerprint;
        bytes32 evidenceRoot;
        bytes32 storageRoot;
        string shortMemo;
        string sourceIds;
        uint256 timestamp;
        address submitter;
    }

    mapping(bytes32 => Receipt) public receipts;
    bytes32[] public receiptIndex;

    event ReceiptAnchoredV2(
        bytes32 indexed receiptHash,
        string decision,
        string severity,
        string agentId,
        string policyVersion,
        bytes32 datasetFingerprint,
        bytes32 evidenceRoot,
        bytes32 storageRoot,
        string shortMemo,
        string sourceIds,
        uint256 timestamp,
        address submitter
    );

    function anchorReadable(
        bytes32 _receiptHash,
        string calldata _decision,
        string calldata _severity,
        string calldata _agentId,
        string calldata _policyVersion,
        bytes32 _datasetFingerprint,
        bytes32 _evidenceRoot,
        bytes32 _storageRoot,
        string calldata _shortMemo,
        string calldata _sourceIds
    ) external {
        require(receipts[_receiptHash].timestamp == 0, "Receipt already anchored");
        require(bytes(_shortMemo).length <= 160, "Memo too long");
        require(bytes(_sourceIds).length <= 256, "Source IDs too long");

        Receipt memory r = Receipt({
            receiptHash: _receiptHash,
            decision: _decision,
            severity: _severity,
            agentId: _agentId,
            policyVersion: _policyVersion,
            datasetFingerprint: _datasetFingerprint,
            evidenceRoot: _evidenceRoot,
            storageRoot: _storageRoot,
            shortMemo: _shortMemo,
            sourceIds: _sourceIds,
            timestamp: block.timestamp,
            submitter: msg.sender
        });

        receipts[_receiptHash] = r;
        receiptIndex.push(_receiptHash);

        emit ReceiptAnchoredV2(
            _receiptHash,
            _decision,
            _severity,
            _agentId,
            _policyVersion,
            _datasetFingerprint,
            _evidenceRoot,
            _storageRoot,
            _shortMemo,
            _sourceIds,
            block.timestamp,
            msg.sender
        );
    }

    function getReceipt(bytes32 _receiptHash) external view returns (Receipt memory) {
        return receipts[_receiptHash];
    }

    function totalReceipts() external view returns (uint256) {
        return receiptIndex.length;
    }
}
