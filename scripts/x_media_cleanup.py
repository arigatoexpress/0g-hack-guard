#!/usr/bin/env python3
"""Prepare or execute an X post/media cleanup manifest.

The default posture is review-first:

1. Generate a manifest of recent posts or media-bearing posts.
2. Review the manifest and adjust keep/delete flags.
3. Run a dry-run delete pass.
4. Only then run live deletion with the exact confirmation string.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from guard0.x_cleanup_policy import (
    DEFAULT_HACKATHON_KEYWORDS,
    DEFAULT_KEEP_TWEET_IDS,
    X_CLEANUP_MANIFEST_SCHEMA,
    is_hackathon_related,
)

LIVE_DELETE_CONFIRMATION = "DELETE_X_MEDIA_FROM_0GUARD"
SCHEMA = X_CLEANUP_MANIFEST_SCHEMA


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _extract_tweet_id(value: str) -> str:
    match = re.search(r"/status/(\d+)", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"\d+", value.strip()):
        return value.strip()
    raise SystemExit(f"Could not extract tweet id from: {value}")


def _load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise SystemExit(f"Unexpected manifest schema in {path}: {payload.get('schema')}")
    return payload


def _write_or_print(payload: dict[str, Any], path: Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path:
        path.write_text(text, encoding="utf-8")
        print(f"Wrote manifest: {path}")
        return
    print(text, end="")


def _candidate_ids(manifest: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for item in manifest.get("items", []):
        if item.get("keep") is True:
            continue
        if item.get("deleteRecommended") is not True:
            continue
        tweet_id = str(item.get("tweetId") or "")
        if tweet_id:
            ids.append(tweet_id)
    return ids


def _template_manifest(keep_ids: set[str], keep_keywords: set[str]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "generatedAt": _now(),
        "mode": "template_review_required",
        "keepTweetIds": sorted(keep_ids),
        "keepKeywords": sorted(keep_keywords),
        "deleteCandidateCount": 0,
        "items": [],
        "instructions": [
            "Run without --template and with X OAuth env vars to populate recent posts.",
            "Use --all-posts to include text-only posts; otherwise only media-bearing posts are listed.",
            "Review every item before live deletion.",
            "Keep the HackQuest proof post and any HackQuest/0guard-related posts unless Ari explicitly changes the allowlist.",
            f"Live deletion requires --live-delete-confirm {LIVE_DELETE_CONFIRMATION}.",
        ],
        "safety": {
            "defaultAction": "dry_run_or_manifest_only",
            "destructive": False,
            "requiresFreshReview": True,
        },
    }


def _is_hackathon_related(text: str, keep_keywords: set[str]) -> bool:
    return is_hackathon_related(text, keep_keywords)


def _build_manifest(
    keep_ids: set[str],
    keep_keywords: set[str],
    *,
    max_results: int,
    pages: int,
    include_text_posts: bool,
) -> dict[str, Any]:
    from guard0.x_bot import XBot, XBotConfigError

    try:
        bot = XBot.from_env()
    except XBotConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    tweets = bot.list_timeline_tweets(
        max_results=max_results,
        pages=pages,
        include_text_posts=include_text_posts,
    )
    items = []
    for tweet in tweets:
        hackathon_related = _is_hackathon_related(tweet.text, keep_keywords)
        keep = tweet.tweet_id in keep_ids or hackathon_related
        items.append(
            {
                "tweetId": tweet.tweet_id,
                "url": f"https://x.com/i/web/status/{tweet.tweet_id}",
                "createdAt": tweet.created_at,
                "text": tweet.text,
                "mediaKeys": tweet.media_keys,
                "mediaTypes": tweet.media_types,
                "mediaUrls": tweet.media_urls,
                "hackathonRelated": hackathon_related,
                "keep": keep,
                "deleteRecommended": not keep,
                "reason": (
                    "allowlisted_hackquest_proof_post"
                    if tweet.tweet_id in keep_ids
                    else "hackathon_keyword_match"
                    if hackathon_related
                    else "not_hackathon_related"
                ),
            }
        )

    return {
        "schema": SCHEMA,
        "generatedAt": _now(),
        "mode": "review_required_all_posts" if include_text_posts else "review_required_media_only",
        "keepTweetIds": sorted(keep_ids),
        "keepKeywords": sorted(keep_keywords),
        "deleteCandidateCount": sum(1 for item in items if item["deleteRecommended"]),
        "scope": "all_posts" if include_text_posts else "media_posts_only",
        "items": items,
        "safety": {
            "defaultAction": "manifest_only",
            "destructive": False,
            "requiresFreshReview": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run-first X post/media cleanup for 0guard")
    parser.add_argument("--manifest-out", type=Path, help="Write generated manifest to this path")
    parser.add_argument("--template", action="store_true", help="Write an empty review template")
    parser.add_argument("--max-results", type=int, default=100, help="Timeline page size, capped at 100")
    parser.add_argument("--pages", type=int, default=5, help="Maximum timeline pages to scan")
    parser.add_argument("--keep-tweet-id", action="append", default=[], help="Tweet id to preserve")
    parser.add_argument("--keep-url", action="append", default=[], help="Tweet/status URL to preserve")
    parser.add_argument("--keep-keyword", action="append", default=[], help="Text keyword that marks a post as hackathon-related")
    parser.add_argument("--all-posts", action="store_true", help="List all recent posts, not only media-bearing posts")
    parser.add_argument("--no-default-keep", action="store_true", help="Do not auto-keep the HackQuest post")
    parser.add_argument("--delete-from-manifest", type=Path, help="Delete candidates from a reviewed manifest")
    parser.add_argument("--dry-run", action="store_true", help="Validate delete candidates but do not delete")
    parser.add_argument(
        "--live-delete-confirm",
        default="",
        help=f"Required exact value for live deletion: {LIVE_DELETE_CONFIRMATION}",
    )
    args = parser.parse_args(argv)

    keep_ids = set() if args.no_default_keep else set(DEFAULT_KEEP_TWEET_IDS)
    keep_ids.update(str(item).strip() for item in args.keep_tweet_id if str(item).strip())
    keep_ids.update(_extract_tweet_id(item) for item in args.keep_url)
    keep_keywords = set(DEFAULT_HACKATHON_KEYWORDS)
    keep_keywords.update(str(item).strip().lower() for item in args.keep_keyword if str(item).strip())

    if args.delete_from_manifest:
        manifest = _load_manifest(args.delete_from_manifest)
        ids = _candidate_ids(manifest)
        print(f"Prepared {len(ids)} X post deletion candidate(s).")
        for tweet_id in ids:
            print(f"- https://x.com/i/web/status/{tweet_id}")
        if args.dry_run:
            print("Dry-run complete. No X posts deleted.")
            return 0
        if args.live_delete_confirm != LIVE_DELETE_CONFIRMATION:
            print(
                f"Live X deletion requires --live-delete-confirm {LIVE_DELETE_CONFIRMATION}. "
                "Run with --dry-run first.",
                file=sys.stderr,
            )
            return 2
        if not ids:
            print("No deletion candidates found in manifest.")
            return 0

        from guard0.x_bot import XBot, XBotConfigError

        try:
            bot = XBot.from_env()
        except XBotConfigError as exc:
            print(f"Configuration error: {exc}", file=sys.stderr)
            return 1
        results = bot.delete_tweets(ids)
        for result in results:
            status = "deleted" if result.deleted else "not_deleted"
            print(f"{status}: https://x.com/i/web/status/{result.tweet_id}")
        return 0 if all(result.deleted for result in results) else 1

    payload = (
        _template_manifest(keep_ids, keep_keywords)
        if args.template
        else _build_manifest(
            keep_ids,
            keep_keywords,
            max_results=args.max_results,
            pages=args.pages,
            include_text_posts=args.all_posts,
        )
    )
    _write_or_print(payload, args.manifest_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
