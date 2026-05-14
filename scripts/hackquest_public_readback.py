from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal

import requests


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


_RE_URL = re.compile(r'https?://[^\s"<>]+')
_RE_CONTRACT = re.compile(r"0x[a-fA-F0-9]{40}")
_RE_CHAINSCAN_TX = re.compile(r"https://chainscan\.0g\.ai/tx/[a-fA-F0-9]{64}")


def _normalize_x_link(raw: str) -> str:
    if raw.startswith("https://"):
        return raw
    if raw.startswith("http://"):
        return "https://" + raw[len("http://") :]
    # HackQuest sometimes renders just `user/status/<id>` as a link.
    return f"https://x.com/{raw.lstrip('/')}"


def parse_hackquest_project_html(html: str) -> tuple[str | None, str | None, str | None, list[str], list[str]]:
    open_source_link: str | None = None
    mvp_link: str | None = None
    x_link: str | None = None

    # Prefer explicit `href="..."` occurrences; fall back to any URL.
    hrefs = re.findall(r'href="([^"]+)"', html)
    for href in hrefs:
        if open_source_link is None and "github.com/" in href:
            open_source_link = href
        if mvp_link is None and ("github.io/" in href or "vercel.app" in href):
            mvp_link = href
        if x_link is None and ("x.com/" in href or re.match(r"^[^/]+/status/\d+$", href) or "status/" in href):
            x_link = _normalize_x_link(href)

    if open_source_link is None or mvp_link is None or x_link is None:
        for url in _RE_URL.findall(html):
            if open_source_link is None and "github.com/" in url:
                open_source_link = url
            if mvp_link is None and ("github.io/" in url or "vercel.app" in url):
                mvp_link = url
            if x_link is None and "x.com/" in url:
                x_link = url

    contract_addresses = sorted(set(_RE_CONTRACT.findall(html)), key=str.lower)
    chainscan_tx_urls = sorted(set(_RE_CHAINSCAN_TX.findall(html)))
    return open_source_link, mvp_link, x_link, contract_addresses, chainscan_tx_urls


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
