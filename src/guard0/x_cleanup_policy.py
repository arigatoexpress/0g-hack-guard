"""Shared X cleanup allowlist policy for 0guard launch posts."""

from __future__ import annotations

import re

X_CLEANUP_MANIFEST_SCHEMA = "0guard.x_media_cleanup_manifest.v1"
DEFAULT_KEEP_TWEET_IDS = {"2054779961425461542", "2055041461218140204"}
DEFAULT_HACKATHON_KEYWORDS = (
    "0guard",
    "0g",
    "@0g_labs",
    "@0g_cn",
    "@0g_eco",
    "@hackquest_",
    "hackquest",
    "#0ghackathon",
    "#buildon0g",
    "buildon0g",
    "policyreceiptanchor",
    "chainscan.0g.ai",
    "arigatoexpress.github.io/0guard",
)


def is_hackathon_related(text: str, keep_keywords: set[str]) -> bool:
    """Return true when text clearly belongs to the 0guard / 0G launch scope.

    A bare substring search is too loose for X cleanup because short links such
    as `t.co/0ga...` can accidentally contain `0g`. Strip short URLs and only
    treat bare `0g` as a standalone token.
    """
    lowered = text.lower()
    text_without_short_urls = re.sub(r"https?://t\.co/\S+", " ", lowered)
    compact = re.sub(r"\s+", " ", text_without_short_urls).strip()
    for keyword in keep_keywords:
        key = keyword.lower().strip()
        if not key:
            continue
        if key == "0g":
            if re.search(r"(?<![a-z0-9])0g(?![a-z0-9])", compact):
                return True
            continue
        if "." in key or "/" in key:
            if key in lowered:
                return True
            continue
        if key in compact:
            return True
    return False
