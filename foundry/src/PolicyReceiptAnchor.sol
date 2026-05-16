// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

/**
 * @title PolicyReceiptAnchor
 * @notice Anchors SHA-256 policy receipt hashes from 0G Hack Guard on 0G Chain.
 * @dev This is a minimal, event-driven contract for hackathon demo purposes.
 */
contract PolicyReceiptAnchor {
    struct Receipt {
        bytes32 receiptHash;
        string decision;
        string severity;
        string agentId;
        uint256 timestamp;
        address submitter;
    }

    mapping(bytes32 => Receipt) public receipts;
    bytes32[] public receiptIndex;

    event ReceiptAnchored(
        bytes32 indexed receiptHash,
        string decision,
        string severity,
        string agentId,
        uint256 timestamp,
        address submitter
    );

    function anchor(
        bytes32 _receiptHash,
        string calldata _decision,
        string calldata _severity,
        string calldata _agentId
    ) external {
        require(receipts[_receiptHash].timestamp == 0, "Receipt already anchored");

        Receipt memory r = Receipt({
            receiptHash: _receiptHash,
            decision: _decision,
            severity: _severity,
            agentId: _agentId,
            timestamp: block.timestamp,
            submitter: msg.sender
        });

        receipts[_receiptHash] = r;
        receiptIndex.push(_receiptHash);

        emit ReceiptAnchored(
            _receiptHash,
            _decision,
            _severity,
            _agentId,
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
