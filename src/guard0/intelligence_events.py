"""Polling snapshot for live-ish 0guard intelligence surfaces.

This is deliberately a snapshot, not a websocket or mempool listener. It lets
the product show what is real today: source reachability, normalized OSINT
signals, and read-only chain heads when the caller opts into network reads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from guard0.crosschain import cross_chain_readiness
from guard0.osint import osint_readiness, osint_signals, source_registry_public

INTELLIGENCE_EVENTS_SCHEMA = "0guard.intelligence_events_snapshot.v1"


def intelligence_events_snapshot(*, live: bool = False, limit: int = 10) -> dict[str, Any]:
    """Return a real-data snapshot from currently safe read-only streams."""
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    registry = source_registry_public()
    readiness = osint_readiness(live=live)
    signals = osint_signals(live=live, limit=limit)
    chain_heads = cross_chain_readiness(
        live=live,
        include_non_default=True,
        timeout_seconds=2.5,
    )
    event_rows = _event_rows(
        source_status=signals["sourceStatus"],
        signals=signals["signals"],
        chain_probes=chain_heads["probes"],
        limit=limit,
    )
    return {
        "schema": INTELLIGENCE_EVENTS_SCHEMA,
        "generatedAt": _now(),
        "live": live,
        "mode": "polling_snapshot_read_only",
        "streamingTransport": "none_yet",
        "liveReadsPerformed": {
            "sourceReachability": readiness["attemptedLiveChecks"],
            "osintFetches": sum(
                1
                for source in signals["sourceStatus"]
                if source.get("status") in {"ok", "degraded"}
            ),
            "rpcProbes": chain_heads["attemptedRpcProbes"],
            "httpProbes": chain_heads["attemptedHttpProbes"],
        },
        "sourceRegistry": {
            "sourceCount": registry["sourceCount"],
            "enabledByDefaultCount": registry["enabledByDefaultCount"],
            "rightsPolicy": registry["rightsPolicy"],
        },
        "readiness": {
            "readinessRatio": readiness["readinessRatio"],
            "reachableLiveChecks": readiness["reachableLiveChecks"],
            "okRpcProbes": chain_heads["okRpcProbes"],
            "rpcReadinessRatio": chain_heads["rpcReadinessRatio"],
            "okHttpProbes": chain_heads["okHttpProbes"],
            "httpReadinessRatio": chain_heads["httpReadinessRatio"],
        },
        "eventCount": len(event_rows),
        "events": event_rows,
        "honestLimits": [
            "This is polling/readback, not mempool monitoring or push streaming.",
            "Reputation adapters still normalize reviewed payloads; fetch workers remain explicit future work.",
            "Fixture detector coverage is separate from live trace coverage.",
        ],
        "nextDataStreams": [
            "PhishDestroy derived active-domain worker with TTL and rawPayloadStored:false.",
            "OFAC/Chainalysis sanctions precheck as a binary compliance signal.",
            "Forta alert/label digest in shadow mode before wallet-specific denies.",
            "EVM approval/permit event watcher using RPC logs or explorer API terms.",
        ],
        "safety": _safety(),
    }


def _event_rows(
    *,
    source_status: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    chain_probes: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for signal in signals:
        rows.append(
            {
                "type": "osint_signal",
                "sourceId": signal.get("sourceId"),
                "observedAt": signal.get("observedAt"),
                "title": signal.get("title"),
                "signalType": signal.get("signalType"),
                "recordHash": signal.get("recordHash"),
                "sourceLink": signal.get("sourceLink") or signal.get("link"),
                "rawPayloadReturned": False,
            }
        )
    for probe in chain_probes:
        if probe.get("status") not in {"ok", "chain_id_mismatch"}:
            continue
        rows.append(
            {
                "type": "chain_head",
                "sourceId": probe.get("id"),
                "observedAt": _now(),
                "title": f"{probe.get('name')} latest block",
                "chainId": probe.get("chainId"),
                "latestBlockNumber": probe.get("latestBlockNumber"),
                "observedChainId": probe.get("observedChainId"),
                "latencyMs": probe.get("latencyMs"),
                "rawPayloadReturned": False,
            }
        )
    if not rows:
        for status in source_status[:limit]:
            rows.append(
                {
                    "type": "source_status",
                    "sourceId": status.get("sourceId"),
                    "observedAt": _now(),
                    "title": status.get("status"),
                    "adapter": status.get("adapter"),
                    "error": status.get("error"),
                    "rawPayloadReturned": False,
                }
            )
    rows.sort(key=lambda item: str(item.get("observedAt") or ""), reverse=True)
    return rows[:limit]


def _safety() -> dict[str, bool]:
    return {
        "readOnly": True,
        "rawPayloadsReturned": False,
        "privateKeyRequired": False,
        "transactionSigningEnabled": False,
        "broadcastingEnabled": False,
        "bridgingEnabled": False,
        "swappingEnabled": False,
        "moneyMovementEnabled": False,
        "telegramSendsEnabled": False,
        "socialPostingEnabled": False,
    }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
