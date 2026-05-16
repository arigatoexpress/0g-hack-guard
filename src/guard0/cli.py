"""
CLI for 0G Hack Guard
=====================
Usage:
  0guard evaluate --intent-json '{...}'
  0guard hack-check --intent-json '{...}'
  0guard native-preflight --payload-json '{...}'
  0guard proof-ladder --payload-json '{...}'
  0guard normalize-reputation-adapter --payload-json '{...}'
  0guard reputation-shadow-cache --payload-json '{...}'
  0guard health
  0guard serve
"""
from __future__ import annotations

import argparse
import json
import sys

from guard0.app import app
from guard0.crypto_hack_guard import check_crypto_hack_signatures
from guard0.native_preflight import build_native_preflight
from guard0.policy import evaluate_intent
from guard0.proof_ladder import build_proof_ladder
from guard0.reputation_adapters import normalize_reputation_adapter_payload
from guard0.reputation_shadow import build_reputation_shadow_cache


def _print_json(obj: dict) -> None:
    print(json.dumps(obj, indent=2))


def cmd_evaluate(args: argparse.Namespace) -> int:
    intent = json.loads(args.intent_json)
    budget = json.loads(args.budget_json) if args.budget_json else None
    decision = evaluate_intent(
        intent,
        budget=budget,
        agent_id=args.agent_id,
        enable_0g_anchor=args.anchor,
        enable_0g_storage=args.storage,
    )
    _print_json(decision.to_dict())
    return 0 if decision.decision == "allow" else 1


def cmd_hack_check(args: argparse.Namespace) -> int:
    from guard0.policy import normalize_intent
    intent = json.loads(args.intent_json)
    result = check_crypto_hack_signatures(normalize_intent(intent))
    _print_json(result.to_dict())
    return 1 if result.blockers else 0


def cmd_native_preflight(args: argparse.Namespace) -> int:
    payload = json.loads(args.payload_json)
    result = build_native_preflight(payload)
    _print_json(result)
    return 0 if result.get("decision") == "allow" else 1


def cmd_proof_ladder(args: argparse.Namespace) -> int:
    payload = json.loads(args.payload_json)
    result = build_proof_ladder(payload)
    _print_json(result)
    return 0


def cmd_normalize_reputation_adapter(args: argparse.Namespace) -> int:
    payload = json.loads(args.payload_json)
    result = normalize_reputation_adapter_payload(payload)
    _print_json(result)
    decision = result.get("reputationPreview", {}).get("decision", {}).get("decision")
    return 0 if decision != "deny" else 1


def cmd_reputation_shadow_cache(args: argparse.Namespace) -> int:
    payload = json.loads(args.payload_json) if args.payload_json else None
    result = build_reputation_shadow_cache(payload)
    _print_json(result)
    decision = result.get("probePreview", {}).get("decision", {}).get("decision")
    return 0 if decision != "deny" else 1


def cmd_health(_args: argparse.Namespace) -> int:
    with app.test_client() as client:
        resp = client.get("/api/health")
        _print_json(resp.get_json())
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="0guard", description="0G Hack Guard CLI")
    sub = parser.add_subparsers(dest="command")

    p_eval = sub.add_parser("evaluate", help="Evaluate an intent")
    p_eval.add_argument("--intent-json", required=True)
    p_eval.add_argument("--budget-json", default="{}", help="Optional budget caps as JSON")
    p_eval.add_argument("--agent-id", default="")
    p_eval.add_argument("--anchor", action="store_true", help="Anchor receipt on 0G Chain")
    p_eval.add_argument("--storage", action="store_true", help="Store threat intel on 0G Storage")
    p_eval.set_defaults(func=cmd_evaluate)

    p_hack = sub.add_parser("hack-check", help="Run hack-signature check only")
    p_hack.add_argument("--intent-json", required=True)
    p_hack.set_defaults(func=cmd_hack_check)

    p_native = sub.add_parser(
        "native-preflight",
        help="Run unified native preflight before a signer or payment surface",
    )
    p_native.add_argument("--payload-json", required=True)
    p_native.set_defaults(func=cmd_native_preflight)

    p_proof = sub.add_parser(
        "proof-ladder",
        help="Build a no-side-effect 0G proof ladder packet",
    )
    p_proof.add_argument("--payload-json", required=True)
    p_proof.set_defaults(func=cmd_proof_ladder)

    p_adapter = sub.add_parser(
        "normalize-reputation-adapter",
        help="Normalize caller-provided PhishDestroy, CryptoScamDB, Forta, GoPlus, or Chainabuse evidence without fetching",
    )
    p_adapter.add_argument("--payload-json", required=True)
    p_adapter.set_defaults(func=cmd_normalize_reputation_adapter)

    p_shadow = sub.add_parser(
        "reputation-shadow-cache",
        help="Build a derived no-fetch reputation shadow cache from reviewed adapter payloads",
    )
    p_shadow.add_argument("--payload-json", default="", help="Optional payload JSON; defaults to a sanitized demo")
    p_shadow.set_defaults(func=cmd_reputation_shadow_cache)

    p_health = sub.add_parser("health", help="Health check")
    p_health.set_defaults(func=cmd_health)

    p_serve = sub.add_parser("serve", help="Run API server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8109)
    p_serve.add_argument("--debug", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
