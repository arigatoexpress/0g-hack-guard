"""Minimal stdlib client for the 0guard native preflight API.

Run after starting the local server:
    python3 -m guard0.cli serve --port 8109
    python3 examples/native_preflight/python_client.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8109"


def native_preflight(
    payload: dict[str, Any],
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 5.0,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/native-preflight",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    payload = {
        "surface": "evm",
        "operation": "read_status",
        "chain": "eip155:8453",
        "intent": {"mode": "preview"},
    }
    try:
        result = native_preflight(payload)
    except urllib.error.URLError as exc:
        print(f"0guard native preflight unavailable: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("decision") == "allow" else 1


if __name__ == "__main__":
    raise SystemExit(main())
