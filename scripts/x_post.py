#!/usr/bin/env python3
"""CLI for posting tweets and threads from JSON / Markdown content.

Usage
-----
Post a single tweet from a JSON file::

    python scripts/x_post.py --file content/single_tweet.json

Post a thread from a JSON file::

    python scripts/x_post.py --file content/thread.json --thread

Post a thread from a Markdown file (each paragraph = one tweet)::

    python scripts/x_post.py --file content/thread.md --thread

Post inline::

    python scripts/x_post.py --text "Hello from 0G Hack Guard"

Post inline thread (pipe-separated)::

    python scripts/x_post.py --thread --text "Tweet 1||Tweet 2||Tweet 3"

Dry-run (validate but do not post)::

    python scripts/x_post.py --file content/thread.json --thread --dry-run

With media::

    python scripts/x_post.py --file content/tweet.json --media docs/assets/diagram.png
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from zg_hack_guard.x_bot import XBot, XBotConfigError

logger = logging.getLogger("x_post")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_content(path: Path, is_thread: bool) -> list[str]:
    """Load tweet text(s) from a JSON or Markdown file."""
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return [str(item) for item in data]
        if isinstance(data, dict):
            if "tweets" in data:
                return [str(t) for t in data["tweets"]]
            if "text" in data:
                return [str(data["text"])]
        raise SystemExit(f"Unexpected JSON structure in {path}")

    if suffix in (".md", ".markdown", ".txt"):
        text = path.read_text()
        # Split on double newlines for Markdown; each paragraph is a tweet.
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            raise SystemExit(f"No content found in {path}")
        return paragraphs if is_thread else [paragraphs[0]]

    raise SystemExit(f"Unsupported file format: {suffix}")


def parse_inline(text: str, is_thread: bool) -> list[str]:
    """Parse inline text. For threads, '||' separates tweets."""
    if is_thread:
        return [t.strip() for t in text.split("||") if t.strip()]
    return [text.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="X (Twitter) posting CLI for 0G Hack Guard")
    parser.add_argument("--file", "-f", type=Path, help="Path to JSON / Markdown / txt file")
    parser.add_argument("--text", "-t", help="Inline tweet text")
    parser.add_argument("--thread", action="store_true", help="Post as a thread")
    parser.add_argument("--media", "-m", nargs="+", help="Media file paths to attach")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not post")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    if not args.file and not args.text:
        parser.print_help()
        return 2

    if args.file and args.text:
        logger.error("Use either --file or --text, not both.")
        return 2

    # Load content
    if args.file:
        tweets = load_content(args.file, args.thread)
    else:
        tweets = parse_inline(args.text, args.thread)

    if args.thread and len(tweets) < 2:
        logger.warning("--thread requested but only one tweet found.")

    # Validate media paths
    media_paths = args.media or []
    for mp in media_paths:
        if not Path(mp).exists():
            logger.error("Media file not found: %s", mp)
            return 1

    logger.info("Prepared %d tweet(s). Dry-run=%s", len(tweets), args.dry_run)
    for i, t in enumerate(tweets, 1):
        logger.debug("Tweet %d (%d chars): %s", i, len(t), t[:80].replace("\n", " "))

    if args.dry_run:
        logger.info("Dry-run complete. No posts sent.")
        return 0

    # Initialize bot from environment
    try:
        bot = XBot.from_env()
    except XBotConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    # Post
    try:
        if len(tweets) == 1 and not args.thread:
            result = bot.post_tweet(tweets[0], media_paths=media_paths or None)
            logger.info("Posted tweet: https://x.com/i/web/status/%s", result.tweet_id)
        else:
            result = bot.post_thread(tweets, media_paths=media_paths or None)
            root = result.tweets[0].tweet_id
            logger.info("Posted thread root: https://x.com/i/web/status/%s", root)
            for i, t in enumerate(result.tweets, 1):
                logger.info("  [%d] https://x.com/i/web/status/%s", i, t.tweet_id)
    except Exception as exc:
        logger.error("Posting failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
