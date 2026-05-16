"""Tests for prepared social/newsletter content."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_current_x_update_thread_is_review_ready_and_within_limits():
    path = REPO_ROOT / "content" / "0guard_current_update_x_thread.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    tweets = data["tweets"]
    assert len(tweets) == 5
    assert all(1 <= len(tweet) <= 280 for tweet in tweets)
    combined = "\n".join(tweets).lower()
    assert "pre-wallet firewall" in combined
    assert "no signing" in combined
    assert "no fund movement" in combined
    assert "0guard" in combined


def test_substack_draft_is_plain_english_and_safety_bounded():
    text = (REPO_ROOT / "content" / "substack_0guard_launch_draft.md").read_text(
        encoding="utf-8"
    )

    assert text.startswith("# 0guard:")
    assert "AI agents should not get to the wallet first" in text
    assert "does not sign transactions" in text
    assert "GoPlus" in text
    assert "0G" in text
