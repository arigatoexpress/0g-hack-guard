"""Tests for composed threat case files."""

import json

from guard0.case_file import build_threat_case_file


def test_threat_case_file_composes_policy_reputation_provenance_and_receipts():
    case_file = build_threat_case_file(
        {
            "intent": {
                "action": "approve",
                "mode": "live_transaction",
                "requires_signature": True,
                "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "target_contract": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
                "prompt_text": "Urgent wallet verification asks for maximum approval.",
            },
            "wallet": "0x885b0892D241Cb5033C9995e09cA521d54f936b5",
            "url": "https://docs.0g.ai.evil.example/claim",
        }
    )

    assert case_file["schema"] == "0guard.threat_case_file.v1"
    assert case_file["mode"] == "case_file_preview_no_live_actions"
    assert case_file["decision"]["decision"] == "deny"
    assert len(case_file["plainEnglish"]) >= 4
    assert case_file["technicalSummary"]["policyDecision"] == "deny"
    assert case_file["technicalSummary"]["walletAlertCount"] >= 1
    assert case_file["technicalSummary"]["datasetCoverage"]["incidentCount"] == 28
    assert case_file["technicalSummary"]["datasetCoverage"]["gapCount"] == 0
    assert {row["id"] for row in case_file["evidence"]} >= {
        "policy_engine",
        "hack_signatures",
        "reputation_probe",
        "reputation_adapter_evidence",
        "wallet_alert_quality",
        "incident_provenance",
        "signature_coverage",
        "zero_g_threat_passport",
    }
    assert case_file["receipt"]["zeroGStorageReady"] is True
    assert case_file["receipt"]["liveUploadPerformed"] is False
    assert case_file["sourceRights"]["rawPayloadsReturned"] is False
    assert case_file["safety"]["telegramSendsEnabled"] is False
    assert case_file["safety"]["transactionSigningEnabled"] is False
    assert case_file["safety"]["moneyMovementEnabled"] is False
    assert case_file["safety"]["rawPayloadsReturned"] is False
    encoded = json.dumps(case_file)
    assert "docs.0g.ai.evil.example" not in encoded


def test_threat_case_file_promotes_normalized_adapter_evidence_without_raw_payloads():
    case_file = build_threat_case_file(
        {
            "intent": {
                "action": "upgrade",
                "mode": "live_transaction",
                "requires_signature": True,
                "target_contract": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
            },
            "url": "https://docs.0g.ai.evil.example/claim",
            "reputationAdapter": {
                "sourceId": "chainabuse",
                "subject": {
                    "url": "https://docs.0g.ai.evil.example/claim",
                    "address": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
                    "chain": "eip155:1",
                },
                "payload": {
                    "reports": [
                        {
                            "checked": True,
                            "confidence_score": 91,
                            "category": "phishing",
                            "reportUrl": "https://chainabuse.example/private/report",
                        }
                    ]
                },
            },
        }
    )

    assert case_file["adapterEvidence"]["enabled"] is True
    assert case_file["adapterEvidence"]["sourceIds"] == ["chainabuse"]
    assert case_file["adapterEvidence"]["derivedEvidenceCount"] == 1
    assert case_file["adapterEvidence"]["rawPayloadsReturned"] is False
    assert case_file["technicalSummary"]["adapterEvidenceCount"] == 1
    assert case_file["technicalSummary"]["adapterSourceIds"] == ["chainabuse"]
    adapter_row = {
        row["id"]: row for row in case_file["evidence"]
    }["reputation_adapter_evidence"]
    assert adapter_row["sourceIds"] == ["chainabuse"]
    encoded = json.dumps(case_file)
    assert "chainabuse.example" not in encoded
    assert "private/report" not in encoded
    assert case_file["sourceRights"]["rawPayloadsReturned"] is False


def test_threat_case_file_redacts_secret_like_content():
    case_file = build_threat_case_file(
        {
            "intent": {
                "action": "scout",
                "mode": "simulation",
                "prompt_text": (
                    "private key 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                ),
            }
        }
    )

    encoded = json.dumps(case_file).lower()
    assert "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" not in encoded
    assert "private key" not in encoded
    assert "walletSignaturesRequested".lower() in encoded.lower()
    assert case_file["safety"]["walletSignaturesRequested"] is False
