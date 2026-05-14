"""Regression checks for the public GitHub Pages surface."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_public_pages_demo_examples_match_real_routes_and_assets():
    html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    assert "https://0guard.example" not in html
    assert "docs/og-image.png" not in html
    assert "0guard-workbench-provenance.png" in html
    assert "/api/hackathon/threat-passport" in html
    assert (
        REPO_ROOT / "docs" / "hackathon-0g" / "assets" / "0guard-workbench-provenance.png"
    ).exists()
    assert "http://127.0.0.1:8109/api/evaluate" in html
    assert "http://127.0.0.1:8109/api/hack-check" in html
    assert "0guard</span> evaluate --intent-json" in html
    assert '"decision"</span>: <span class="string">"deny"' in html
    assert "matched_signatures" not in html
    assert "risk_score" not in html
