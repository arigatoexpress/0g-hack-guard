"""Tests for local inference mesh, x402 products, and backfill plans."""

from __future__ import annotations

import requests

from guard0.local_inference import (
    build_historical_backfill_plan,
    build_local_inference_mesh,
    build_telegram_local_inference_preview,
    build_x402_data_products,
)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


def test_local_inference_mesh_defaults_to_no_prompt_execution():
    mesh = build_local_inference_mesh(live=False)

    assert mesh["schema"] == "0guard.local_inference_mesh.v1"
    assert mesh["mode"] == "configured_mesh_no_network"
    assert mesh["summary"]["promptExecutionEnabled"] is False
    assert mesh["summary"]["telegramSendsEnabled"] is False
    assert mesh["safety"]["paidInferenceEnabled"] is False
    assert mesh["safety"]["transactionSigningEnabled"] is False
    assert any(node["id"] == "windows_ollama" for node in mesh["nodes"])


def test_local_inference_mesh_live_probe_detects_windows_model_and_pi_status():
    def fake_get(url: str, timeout: float) -> FakeResponse:
        assert timeout == 3.0
        if "192.168.1.61" in url:
            return FakeResponse({"models": [{"name": "llama3.2:3b"}]})
        if "192.168.1.111" in url:
            return FakeResponse({"host": "rvpi-a", "role": "primary", "mode": "telemetry_only"})
        if "10.77.4.12" in url:
            raise requests.ConnectTimeout("connection refused")
        raise AssertionError(f"unexpected URL {url}")

    mesh = build_local_inference_mesh(live=True, http_get=fake_get)

    by_id = {node["id"]: node for node in mesh["nodes"]}
    assert by_id["windows_ollama"]["status"] == "ready"
    assert by_id["windows_ollama"]["modelNames"] == ["llama3.2:3b"]
    assert by_id["rvpi_a_edge"]["status"] == "edge_ready"
    assert by_id["rvpi_b_ollama_candidate"]["status"] == "unreachable"
    assert mesh["summary"]["modelServingNodes"] == 1
    assert mesh["safety"]["promptExecutionEnabled"] is False


def test_telegram_local_inference_preview_is_no_send():
    preview = build_telegram_local_inference_preview(build_local_inference_mesh(live=False))

    assert preview["schema"] == "0guard.telegram_local_inference_preview.v1"
    assert preview["delivery"] == "preview_no_send"
    assert preview["telegram_send"] is False
    assert "Delivery: preview only" in preview["message"]
    assert preview["safety"]["telegramSendsEnabled"] is False


def test_x402_data_products_are_rights_cleared_and_unsettled():
    products = build_x402_data_products()

    assert products["schema"] == "0guard.x402_data_products.v1"
    assert products["protocolPosture"]["paymentRequiredStatus"] == 402
    assert products["protocolPosture"]["initialSettlement"].startswith("disabled")
    assert products["safety"]["x402SettlementEnabled"] is False
    assert products["safety"]["moneyMovementEnabled"] is False
    assert all(item["rawPayloadResaleAllowed"] is False for item in products["products"])
    assert any(item["id"] == "node_health_snapshot" for item in products["products"])
    assert "https://docs.cdp.coinbase.com/x402/network-support" in products["sources"]


def test_historical_backfill_plan_keeps_raw_and_private_data_out():
    plan = build_historical_backfill_plan()

    assert plan["schema"] == "0guard.historical_backfill_plan.v1"
    assert plan["mode"] == "backfill_plan_no_fetch"
    assert plan["safety"]["rawPayloadsReturned"] is False
    assert plan["safety"]["privateKeysReturned"] is False
    assert plan["backfillLanes"][0]["id"] == "incident_corpus_2020_present"
    assert any(lane["id"] == "x402_receipt_metadata" for lane in plan["backfillLanes"])
