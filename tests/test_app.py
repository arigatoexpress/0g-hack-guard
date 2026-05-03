"""Smoke tests for Flask app."""
import pytest

from zg_hack_guard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["service"] == "zg-hack-guard"


def test_evaluate_deny_live_tx(client):
    r = client.post("/api/evaluate", json={
        "intent": {"action": "swap", "mode": "live_transaction", "requires_signature": True}
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["decision"] == "deny"


def test_hack_check_endpoint(client):
    r = client.post("/api/hack-check", json={
        "action": "approve",
        "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    })
    assert r.status_code == 200
    data = r.get_json()
    assert any("Unlimited" in b for b in data["blockers"])


def test_domain_check(client):
    r = client.get("/api/domain?url=https://docs.0g.ai")
    assert r.status_code == 200
    data = r.get_json()
    assert data["decision"] == "allow"
