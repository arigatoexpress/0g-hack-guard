#!/usr/bin/env python3
"""Generate an X cleanup manifest from the active Brave/Chromium session.

This is a credentialless fallback for Ari's local browser: it connects to an
already-running Chrome DevTools Protocol endpoint, captures the authenticated
`UserTweets` request, paginates the same timeline in-page, and writes a
review-first manifest. It never saves cookies, CSRF tokens, bearer tokens, or
request headers.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from playwright.sync_api import sync_playwright

from guard0.x_cleanup_policy import (
    DEFAULT_HACKATHON_KEYWORDS,
    DEFAULT_KEEP_TWEET_IDS,
    X_CLEANUP_MANIFEST_SCHEMA,
    is_hackathon_related,
)

SAFE_HEADER_NAMES = {
    "accept",
    "authorization",
    "content-type",
    "x-csrf-token",
    "x-twitter-active-user",
    "x-twitter-auth-type",
    "x-twitter-client-language",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an X cleanup manifest from Brave CDP")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--account", default="rariwrldd")
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument("--keep-tweet-id", action="append", default=[])
    parser.add_argument("--keep-keyword", action="append", default=[])
    args = parser.parse_args(argv)

    keep_ids = set(DEFAULT_KEEP_TWEET_IDS)
    keep_ids.update(str(item).strip() for item in args.keep_tweet_id if str(item).strip())
    keep_keywords = set(DEFAULT_HACKATHON_KEYWORDS)
    keep_keywords.update(str(item).strip().lower() for item in args.keep_keyword if str(item).strip())

    payload = build_manifest(
        cdp_url=args.cdp_url,
        account=args.account,
        max_pages=args.max_pages,
        keep_ids=keep_ids,
        keep_keywords=keep_keywords,
    )
    args.manifest_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote manifest: {args.manifest_out}")
    print(
        json.dumps(
            {
                "observedCount": payload["observedCount"],
                "deleteCandidateCount": payload["deleteCandidateCount"],
                "pagesFetched": payload["source"]["pagesFetched"],
            },
            indent=2,
        )
    )
    return 0


def build_manifest(
    *,
    cdp_url: str,
    account: str,
    max_pages: int,
    keep_ids: set[str],
    keep_keywords: set[str],
) -> dict[str, Any]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0]
        page = context.new_page()
        captured: dict[str, Any] = {"url": None, "headers": None, "json": None}

        def on_request(request) -> None:
            if "/graphql/" in request.url and "/UserTweets?" in request.url and captured["url"] is None:
                captured["url"] = request.url
                captured["headers"] = request.all_headers()

        def on_response(response) -> None:
            if captured["url"] and response.url == captured["url"] and captured["json"] is None:
                try:
                    captured["json"] = response.json()
                except Exception:
                    captured["json"] = None

        page.on("request", on_request)
        page.on("response", on_response)
        page.goto(f"https://x.com/{account}", wait_until="domcontentloaded", timeout=60_000)
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        page.wait_for_timeout(3_000)

        if not captured["url"] or not captured["headers"] or not captured["json"]:
            raise SystemExit("Could not capture an authenticated UserTweets request from Brave.")

        safe_headers = {
            key: value
            for key, value in captured["headers"].items()
            if key.lower() in SAFE_HEADER_NAMES
        }
        tweets: dict[str, dict[str, Any]] = {}
        cursor: str | None = None
        errors: list[dict[str, Any]] = []
        pages_fetched = 0
        for page_index in range(max(1, max_pages)):
            pages_fetched = page_index + 1
            if page_index == 0:
                data = captured["json"]
            else:
                wrapper = page.evaluate(
                    """async ({url, headers}) => {
                        const res = await fetch(url, {headers, credentials: 'include'});
                        const text = await res.text();
                        try { return {ok: res.ok, status: res.status, json: JSON.parse(text)}; }
                        catch { return {ok: res.ok, status: res.status, text: text.slice(0, 500)}; }
                    }""",
                    {
                        "url": _request_url_with_cursor(captured["url"], cursor),
                        "headers": safe_headers,
                    },
                )
                if not wrapper.get("ok"):
                    errors.append(
                        {
                            "page": pages_fetched,
                            "status": wrapper.get("status"),
                            "text": wrapper.get("text"),
                        }
                    )
                    break
                data = wrapper.get("json") or {}

            for entry in _entries_from(data):
                for tweet in _tweets_from_entry(entry, account):
                    related = tweet["tweetId"] in keep_ids or is_hackathon_related(
                        tweet["text"], keep_keywords
                    )
                    tweet["hackathonRelated"] = related
                    tweet["keep"] = related
                    tweet["deleteRecommended"] = not related
                    tweet["reason"] = (
                        "hackathon_related_or_allowlisted" if related else "not_hackathon_related"
                    )
                    tweets[tweet["tweetId"]] = tweet

            next_cursor = _bottom_cursor(data)
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor

        page.close()
        browser.close()

    items = list(tweets.values())
    return {
        "schema": X_CLEANUP_MANIFEST_SCHEMA,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "brave_cdp_authenticated_manifest_review_required",
        "scope": "authenticated_user_tweets",
        "keepTweetIds": sorted(keep_ids),
        "keepKeywords": sorted(keep_keywords),
        "deleteCandidateCount": sum(1 for item in items if item["deleteRecommended"]),
        "observedCount": len(items),
        "items": items,
        "source": {
            "account": account,
            "url": f"https://x.com/{account}",
            "pagesFetched": pages_fetched,
            "errors": errors,
            "authMaterialSaved": False,
        },
        "safety": {
            "defaultAction": "manifest_only",
            "destructive": False,
            "requiresFreshReview": True,
        },
    }


def _request_url_with_cursor(base_url: str, cursor: str | None) -> str:
    parts = urlparse(base_url)
    query = parse_qs(parts.query)
    variables = json.loads(query["variables"][0])
    if cursor:
        variables["cursor"] = cursor
    else:
        variables.pop("cursor", None)
    query["variables"] = [json.dumps(variables, separators=(",", ":"))]
    return urlunparse(parts._replace(query=urlencode(query, doseq=True)))


def _timeline_instructions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = (((payload.get("data") or {}).get("user") or {}).get("result") or {})
    for path in (
        ("timeline_v2", "timeline", "instructions"),
        ("timeline", "timeline", "instructions"),
    ):
        current: Any = result
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if isinstance(current, list):
            return current
    return []


def _entries_from(payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for instruction in _timeline_instructions(payload):
        if "entries" in instruction:
            entries.extend(instruction.get("entries") or [])
        if instruction.get("type") == "TimelinePinEntry" and instruction.get("entry"):
            entries.append(instruction["entry"])
    seen: set[str] = set()
    unique_entries: list[dict[str, Any]] = []
    for entry in entries:
        entry_id = entry.get("entryId")
        if entry_id and entry_id in seen:
            continue
        if entry_id:
            seen.add(entry_id)
        unique_entries.append(entry)
    return unique_entries


def _bottom_cursor(payload: dict[str, Any]) -> str | None:
    for entry in _entries_from(payload):
        content = entry.get("content") or {}
        if content.get("cursorType") == "Bottom":
            return content.get("value")
    return None


def _tweets_from_entry(entry: dict[str, Any], account: str) -> list[dict[str, Any]]:
    content = entry.get("content") or {}
    tweets = []
    tweet = _tweet_from_item_content(content.get("itemContent") or {}, account)
    if tweet:
        tweets.append(tweet)
    for module_item in content.get("items") or []:
        item_content = ((module_item.get("item") or {}).get("itemContent") or {})
        tweet = _tweet_from_item_content(item_content, account)
        if tweet:
            tweets.append(tweet)
    return tweets


def _tweet_from_item_content(item_content: dict[str, Any], account: str) -> dict[str, Any] | None:
    result = ((item_content.get("tweet_results") or {}).get("result") or {})
    if result.get("__typename") == "TweetWithVisibilityResults":
        result = result.get("tweet") or {}
    legacy = result.get("legacy") or {}
    tweet_id = result.get("rest_id") or legacy.get("id_str")
    if not tweet_id:
        return None
    text = re.sub(r"\s+", " ", legacy.get("full_text") or legacy.get("text") or "").strip()
    media = (
        (legacy.get("extended_entities") or {}).get("media")
        or (legacy.get("entities") or {}).get("media")
        or []
    )
    media_urls = [
        item.get("media_url_https") or item.get("url")
        for item in media
        if item.get("media_url_https") or item.get("url")
    ]
    return {
        "tweetId": str(tweet_id),
        "url": f"https://x.com/{account}/status/{tweet_id}",
        "createdAt": legacy.get("created_at"),
        "text": text,
        "kind": "repost" if text.startswith("RT @") else "post",
        "mediaKeys": [],
        "mediaTypes": [item.get("type") for item in media if item.get("type")],
        "mediaUrls": media_urls,
    }


if __name__ == "__main__":
    raise SystemExit(main())
