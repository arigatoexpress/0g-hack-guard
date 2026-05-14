from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal

import requests

from guard0.hackquest_public_readback import parse_hackquest_project_html


@dataclass(frozen=True)
class HackQuestPublicReadback:
    fetched_at: str
    url: str
    http_status: int
    open_source_link: str | None
    mvp_link: str | None
    x_link: str | None
    contract_addresses: list[str]
    chainscan_tx_urls: list[str]


def fetch_hackquest_project(url: str) -> HackQuestPublicReadback:
    resp = requests.get(url, timeout=30)
    open_source_link, mvp_link, x_link, contracts, chainscan_txs = parse_hackquest_project_html(
        resp.text
    )
    return HackQuestPublicReadback(
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        url=url,
        http_status=resp.status_code,
        open_source_link=open_source_link,
        mvp_link=mvp_link,
        x_link=x_link,
        contract_addresses=contracts,
        chainscan_tx_urls=chainscan_txs,
    )


def _to_markdown(result: HackQuestPublicReadback) -> str:
    lines: list[str] = []
    lines.append("# HackQuest Public Readback")
    lines.append("")
    lines.append(f"- Fetched at: {result.fetched_at}")
    lines.append(f"- URL: {result.url}")
    lines.append(f"- HTTP status: {result.http_status}")
    lines.append(f"- Repo link: {result.open_source_link or '(not found)'}")
    lines.append(f"- Demo/MVP link: {result.mvp_link or '(not found)'}")
    lines.append(f"- X link: {result.x_link or '(not found)'}")
    lines.append(f"- Contract addresses found: {len(result.contract_addresses)}")
    for addr in result.contract_addresses[:10]:
        lines.append(f"  - {addr}")
    if len(result.contract_addresses) > 10:
        lines.append("  - (truncated)")
    lines.append(f"- chainscan tx URLs found: {len(result.chainscan_tx_urls)}")
    for tx in result.chainscan_tx_urls[:10]:
        lines.append(f"  - {tx}")
    if len(result.chainscan_tx_urls) > 10:
        lines.append("  - (truncated)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read back public HackQuest project fields from HTML.")
    parser.add_argument(
        "--url",
        default="https://www.hackquest.io/projects/0guard",
        help="HackQuest project URL to read back.",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    result = fetch_hackquest_project(args.url)
    fmt: Literal["json", "markdown"] = args.format
    if fmt == "json":
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
        return 0
    print(_to_markdown(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
