#!/usr/bin/env python3
"""Read-only HackQuest submission readiness audit for 0guard."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from guard0.osint import hackquest_readiness_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit 0guard HackQuest submission readiness")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 2 when operator-required blockers remain.",
    )
    args = parser.parse_args()

    audit = hackquest_readiness_audit()
    if args.format == "markdown":
        print(_to_markdown(audit))
    else:
        print(json.dumps(audit, indent=2, sort_keys=True))

    if args.strict and not audit["submittableNow"]:
        return 2
    return 0


def _to_markdown(audit: dict) -> str:
    lines = [
        "# 0guard HackQuest Readiness Audit",
        "",
        f"Generated: {audit['generatedAt']}",
        f"Deadline: {audit['event']['deadline']['utc8']} / {audit['event']['deadline']['denver']}",
        f"Submittable now: {str(audit['submittableNow']).lower()}",
        "",
        "## Mainnet Requirement",
        "",
        f"- Chain ID: {audit['mainnetRequirement']['chainId']}",
        f"- RPC: {audit['mainnetRequirement']['rpc']}",
        f"- Explorer: {audit['mainnetRequirement']['explorer']}",
        "",
        "## Current 0G Config",
        "",
        f"- Chain ID: {audit['current0GConfig']['chainId']}",
        f"- RPC: {audit['current0GConfig']['rpc']}",
        f"- Receipt contract configured: {audit['current0GConfig']['receiptContractConfigured']}",
        f"- Explorer URL configured: {audit['current0GConfig']['explorerUrlConfigured']}",
        "",
        "## Requirements",
        "",
    ]
    for item in audit["requirements"]:
        lines.append(f"- `{item['status']}` {item['label']} ({item['id']})")
        lines.append(f"  Action: {item['operatorAction']}")
    lines.extend(["", "## Operator Blockers", ""])
    if audit["operatorBlockers"]:
        for item in audit["operatorBlockers"]:
            lines.append(f"- {item['label']}: {item['operatorAction']}")
    else:
        lines.append("- None.")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
