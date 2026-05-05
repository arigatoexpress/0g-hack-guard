#!/usr/bin/env python3
"""
CLI for posting hack alerts to Telegram.

Usage:
    export TELEGRAM_BOT_TOKEN=...
    export TELEGRAM_CHAT_ID=...
    python scripts/telegram_post.py --text "Critical alert"
    python scripts/telegram_post.py --file content/hack_guard_thread.json --thread
    python scripts/telegram_post.py --health
"""
from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "src")

from guard0.telegram_bot import (
    send_message,
    send_thread,
    get_me,
)


def cmd_post(args: argparse.Namespace) -> int:
    if args.health:
        info = get_me()
        print(json.dumps(info, indent=2))
        return 0

    if args.text:
        result = send_message(args.text)
        print(json.dumps(result, indent=2))
        return 0

    if args.file:
        with open(args.file) as f:
            data = json.load(f)

        if args.thread:
            tweets = data if isinstance(data, list) else data.get("tweets", data.get("thread", []))
            messages = [t if isinstance(t, str) else t.get("text", t.get("content", "")) for t in tweets]
            if args.dry_run:
                print(f"[DRY RUN] Would post {len(messages)} messages to Telegram:")
                for i, msg in enumerate(messages, 1):
                    print(f"\n--- Message {i} ---\n{msg}\n")
                return 0
            results = send_thread(messages)
            print(f"Posted {len(results)} messages")
            return 0
        else:
            text = data if isinstance(data, str) else json.dumps(data, indent=2)
            result = send_message(text)
            print(json.dumps(result, indent=2))
            return 0

    print("Use --text, --file, or --health")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="telegram-post", description="Post threat intel to Telegram")
    parser.add_argument("--text", help="Single message text (supports HTML)")
    parser.add_argument("--file", help="JSON file with tweet/thread content")
    parser.add_argument("--thread", action="store_true", help="Post as threaded messages")
    parser.add_argument("--dry-run", action="store_true", help="Print without sending")
    parser.add_argument("--health", action="store_true", help="Check bot connection")
    args = parser.parse_args(argv)
    return cmd_post(args)


if __name__ == "__main__":
    sys.exit(main())
