"""
CLI for 0G Hack Guard
=====================
Usage:
  0guard evaluate --intent-json '{...}'
  0guard hack-check --intent-json '{...}'
  0guard native-preflight --payload-json '{...}'
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
