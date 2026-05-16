"""Tests for the rights-aware reputation probe."""

from guard0.reputation import build_reputation_probe, domain_decision


def test_reputation_probe_allows_curated_domain_and_clean_evm_address():
    result = build_reputation_probe(
        {
            "url": "https://docs.0g.ai/build",
            "address": "0x000000000000000000000000000000000000dEaD",
            "chain": "eip155:8453",
            "labels": ["verified"],
        }
    )

    assert result["schema"] == "0guard.reputation_probe.v1"
    assert result["decision"]["decision"] == "allow"
    assert result["rightsPolicy"]["rawPayloadsReturned"] is False
    assert result["safety"]["transactionSigningEnabled"] is False
    assert {signal["id"] for signal in result["signals"]} >= {
        "trusted_domain_allowlist",
        "evm_address_syntax_valid",
    }


def test_reputation_probe_denies_allowlist_suffix_spoof_and_ioc():
    result = build_reputation_probe(
        {
            "url": "https://docs.0g.ai.evil.example/claim",
            "address": "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
            "chain": "eip155:1",
            "labels": ["spoofed support domain"],
            "sourceEvidence": [
                {
                    "sourceId": "operator_report",
                    "verdict": "phishing",
                    "confidence": 0.91,
                    "label": "wallet drainer landing page",
                    "url": "https://example.test/report",
                }
            ],
            "intent": {
                "action": "upgrade",
                "mode": "live_transaction",
                "requires_signature": True,
                "prompt_text": "Urgent support flow asks the agent to sign an admin upgrade.",
            },
        }
    )

    assert result["decision"]["decision"] == "deny"
    assert result["decision"]["severity"] == "critical"
    assert result["receipt"]["zeroGStorageReady"] is True
    ids = {signal["id"] for signal in result["signals"]}
    assert "allowlist_suffix_spoof" in ids
    assert "known_malicious_counterparty" in ids
    assert "source_negative_vote" in ids
    assert all("url" not in signal["evidence"] for signal in result["signals"])


def test_domain_decision_keeps_suffix_spoofs_out_of_allowlist():
    allowed = domain_decision("https://docs.0g.ai")
    spoof = domain_decision("https://docs.0g.ai.evil.example")

    assert allowed["allowed"] is True
    assert allowed["matched"] == "docs.0g.ai"
    assert spoof["allowed"] is False
