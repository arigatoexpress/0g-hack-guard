from __future__ import annotations

import re
from urllib.parse import urlparse

_RE_URL = re.compile(r'https?://[^\s"<>]+')
_RE_CONTRACT = re.compile(r"0x[a-fA-F0-9]{40}")
_RE_CHAINSCAN_TX = re.compile(r"https://chainscan\.0g\.ai/tx/[a-fA-F0-9]{64}")


def normalize_x_link(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        # HackQuest sometimes emits `https://<username>/status/<id>` (no real host).
        if parsed.netloc and "." not in parsed.netloc and "/status/" in parsed.path:
            return f"https://x.com/{parsed.netloc}{parsed.path}"
        if "x.com" in parsed.netloc or "twitter.com" in parsed.netloc:
            return raw.replace("http://", "https://", 1)
        return raw.replace("http://", "https://", 1)
    # HackQuest sometimes renders just `user/status/<id>` as a relative-ish link.
    return f"https://x.com/{raw.lstrip('/')}"


def parse_hackquest_project_html(
    html: str,
) -> tuple[str | None, str | None, str | None, list[str], list[str]]:
    open_source_link: str | None = None
    mvp_link: str | None = None
    x_link: str | None = None

    hrefs = re.findall(r'href="([^"]+)"', html)
    for href in hrefs:
        if open_source_link is None and "github.com/" in href:
            open_source_link = href
        if mvp_link is None and ("github.io/" in href or "vercel.app" in href):
            mvp_link = href
        if x_link is None and (
            "x.com/" in href
            or re.match(r"^[^/]+/status/\d+$", href)
            or "status/" in href
        ):
            x_link = normalize_x_link(href)

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

