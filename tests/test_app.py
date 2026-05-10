"""Smoke tests for Flask app."""

from pathlib import Path
import subprocess
import sys

import pytest

import guard0.app as app_module
from guard0.app import app

REPO_ROOT = Path(__file__).resolve().parents[1]


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
    assert data["safety_flags"]["external_sends_blocked_from_workbench"] is True
    assert data["safety_flags"]["money_movement_enabled"] is False


def test_module_entrypoint_honors_container_host_env(monkeypatch):
    run_args = {}

    def fake_run(**kwargs):
        run_args.update(kwargs)

    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8110")
    monkeypatch.setattr(app_module.app, "run", fake_run)

    app_module.main()

    assert run_args == {"host": "0.0.0.0", "port": 8110, "debug": False}


def test_frontend_contract_is_browser_smoke_ready_and_non_mutating(client):
    r = client.get("/api/frontend-contract")
    assert r.status_code == 200
    data = r.get_json()
    assert data["schema"] == "0guard.frontend_contract.v1"
    assert data["route"] == "/"
    assert data["mode"] == "read_only_pre_wallet"
    assert data["safety"]["workbenchCanTriggerLiveActions"] is False
    assert data["safety"]["livePostingEnabled"] is False
    assert data["safety"]["telegramSendsEnabled"] is False
    assert data["safety"]["transactionSigningEnabled"] is False
    assert data["safety"]["moneyMovementEnabled"] is False
    assert "/api/external-action-contracts" in data["apiRoutes"]
    assert "#run-evaluate" in data["requiredSelectors"]
    assert "#contract-output" in data["requiredSelectors"]


def test_frontend_contract_selectors_match_static_shell(client):
    contract = client.get("/api/frontend-contract").get_json()
    html = client.get("/").get_data(as_text=True)
    for selector in contract["requiredSelectors"]:
        assert f'id="{selector.removeprefix("#")}"' in html
    for expected_text in contract["requiredText"]:
        assert expected_text in html
    assert 'href="/static/styles.css"' in html
    assert 'src="/static/app.js"' in html


def test_frontend_uses_packaged_template_and_static_assets():
    package_root = REPO_ROOT / "src" / "guard0"
    source = (package_root / "app.py").read_text()
    assert "render_template_string" not in source
    assert "HTML_DASHBOARD" not in source
    assert (package_root / "templates" / "index.html").read_text().startswith("<!doctype html>")
    assert "run-evaluate" in (package_root / "static" / "app.js").read_text()
    assert ".shell" in (package_root / "static" / "styles.css").read_text()


def test_external_action_contracts_keep_live_paths_out_of_workbench(client):
    r = client.get("/api/external-action-contracts")
    assert r.status_code == 200
    data = r.get_json()
    assert data["defaultMode"] == "dry_run"
    assert data["workbenchCanTriggerLiveActions"] is False
    by_id = {item["id"]: item for item in data["actions"]}
    assert by_id["x-post"]["liveConfirmationFlag"] == "--live-post-confirm POST_TO_X_FROM_0GUARD"
    assert (
        by_id["telegram-post"]["liveConfirmationFlag"]
        == "--live-send-confirm SEND_TO_TELEGRAM_FROM_0GUARD"
    )
    assert by_id["0g-contract-deploy"]["reachableFromWorkbench"] is False


def test_evaluate_deny_live_tx(client):
    r = client.post(
        "/api/evaluate",
        json={"intent": {"action": "swap", "mode": "live_transaction", "requires_signature": True}},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["decision"] == "deny"


def test_hack_check_endpoint(client):
    r = client.post(
        "/api/hack-check",
        json={
            "action": "approve",
            "calldata": "0x095ea7b3ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        },
    )
    assert r.status_code == 200
    data = r.get_json()
    assert any("Unlimited" in b for b in data["blockers"])


def test_domain_check(client):
    r = client.get("/api/domain?url=https://docs.0g.ai")
    assert r.status_code == 200
    data = r.get_json()
    assert data["decision"] == "allow"


def test_x_post_cli_requires_live_confirmation_before_credentials():
    result = subprocess.run(
        [sys.executable, "scripts/x_post.py", "--text", "hello"],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--live-post-confirm POST_TO_X_FROM_0GUARD" in result.stderr
    assert "Missing environment variables" not in result.stderr


def test_x_post_cli_dry_run_does_not_require_credentials():
    result = subprocess.run(
        [sys.executable, "scripts/x_post.py", "--text", "hello", "--dry-run"],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Dry-run complete" in result.stderr


def test_telegram_post_cli_requires_live_confirmation_before_credentials():
    result = subprocess.run(
        [sys.executable, "scripts/telegram_post.py", "--text", "hello"],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--live-send-confirm SEND_TO_TELEGRAM_FROM_0GUARD" in result.stderr
    assert "TELEGRAM_BOT_TOKEN" not in result.stderr


def test_telegram_post_cli_text_dry_run_does_not_require_credentials():
    result = subprocess.run(
        [sys.executable, "scripts/telegram_post.py", "--text", "hello", "--dry-run"],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[DRY RUN] Would post 1 message to Telegram" in result.stdout


def test_x_auto_post_workflow_is_manual_and_dry_run_by_default():
    workflow = (REPO_ROOT / ".github/workflows/x-auto-post.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "push:" not in workflow
    assert "live_post_confirm" in workflow
    assert "--live-post-confirm POST_TO_X_FROM_0GUARD" in workflow
    assert "--dry-run" in workflow
