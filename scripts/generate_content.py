#!/usr/bin/env python3
"""
CLI for 0G Hack Guard Content Engine
=====================================
Reads incident JSON and outputs tweet-ready content.

Usage:
    python scripts/generate_content.py --incident data/april_2026_incidents.json
    python scripts/generate_content.py --incident data/april_2026_incidents.json --protocol "Drift Protocol"
    python scripts/generate_content.py --incident data/april_2026_incidents.json --format json --out content_output.json
    python scripts/generate_content.py --single '{"protocol":"X","loss_usd":5000000,...}'
"""
from __future__ import annotations

import argparse
import json
import sys
import os

# Ensure src is on path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zg_hack_guard.content_engine import generate_content, generate_batch, batch_to_json


def load_incidents(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "incidents" in data:
        return data["incidents"]
    if isinstance(data, list):
        return data
    raise ValueError("Incident file must contain a list or an object with an 'incidents' key.")


def pretty_print(output) -> None:
    print("=" * 60)
    print(f"  Protocol : {output.protocol}")
    print(f"  Loss     : ${output.loss_usd:,.0f}")
    print(f"  Severity : {output.severity.upper()}")
    print(f"  Hashtags : {output.hashtags}")
    print("=" * 60)
    print("\n🚨 ALERT TWEET")
    print("-" * 40)
    print(output.alert_tweet)
    print(f"  [chars: {len(output.alert_tweet)}/280]")
    print("\n🧵 THREAD BREAKDOWN")
    print("-" * 40)
    for i, tweet in enumerate(output.thread_breakdown, 1):
        print(f"\n[{i}/{len(output.thread_breakdown)}] ({len(tweet)} chars)")
        print(tweet)
    print("\n📚 SUMMARY POST")
    print("-" * 40)
    print(output.summary_post)
    print(f"  [chars: {len(output.summary_post)}/280]")
    print("\n🔗 SIGNATURES MATCHED")
    print("-" * 40)
    for sig in output.signatures_matched:
        print(f"  • {sig}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate_content",
        description="Generate X/Twitter content from crypto hack threat intelligence",
    )
    parser.add_argument(
        "--incident",
        metavar="PATH",
        help="Path to JSON file containing incident data",
    )
    parser.add_argument(
        "--single",
        metavar="JSON",
        help="Single incident JSON string",
    )
    parser.add_argument(
        "--protocol",
        metavar="NAME",
        help="Filter to a specific protocol name (requires --incident)",
    )
    parser.add_argument(
        "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty)",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "major", "mid"],
        help="Filter incidents by severity (requires --incident)",
    )

    args = parser.parse_args(argv)

    if not args.incident and not args.single:
        parser.print_help()
        return 2

    if args.single:
        incident = json.loads(args.single)
        outputs = [generate_content(incident)]
    else:
        incidents = load_incidents(args.incident)
        if args.protocol:
            incidents = [i for i in incidents if i.get("protocol") == args.protocol]
        if args.severity:
            from zg_hack_guard.content_engine import _get_severity

            incidents = [i for i in incidents if _get_severity(float(i.get("loss_usd", 0))) == args.severity]
        outputs = generate_batch(incidents)

    if args.format == "json":
        result = json.dumps([o.to_dict() for o in outputs], indent=2, ensure_ascii=False)
    else:
        # Pretty print collects into a single string for optional file write
        import io

        buf = io.StringIO()
        for out in outputs:
            # Redirect print to buffer
            old_stdout = sys.stdout
            sys.stdout = buf
            pretty_print(out)
            sys.stdout = old_stdout
        result = buf.getvalue()

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(result)
        print(f"Wrote output to {args.out}")
    else:
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
