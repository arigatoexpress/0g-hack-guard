"""
Crypto Hack Signature & Behavioral Detection Module
====================================================
Real-world detection signatures derived from April 2026 — the worst month on
record for DeFi/DEX hacks ($635M+ across 28 incidents).

Sources: DeFi Llama, Rekt News, SlowMist, CertiK, Chainalysis, BlockSec Phalcon
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ── Known Malicious Addresses (April 2026 IOCs) ──────────────────────────────

KNOWN_MALICIOUS_ADDRESSES: frozenset[str] = frozenset({
    # Drift Protocol (Solana)
    "HkGz4KmoZ7Zmk7HN6ndJ31UJ1qZ2qgwQxgVqQwovpZES",
    "H7PiGqqUaanBovwKgEtreJbKmQe6dbq6VTrw6guy7ZgL",
    # Wasabi Protocol (EVM)
    "0x02228b0afcdbEdf8180D96Fc181Da3AF5DD1d1ab",
    # Kelp DAO / LayerZero
    "0x85d456b298ef3",  # RSETH_OFTAdapter (compromised adapter path)
    # Rhea Finance (NEAR)
    "rhea000453.multica.near",
    "rhea000462.multica.near",
    "rhea000505.multica.near",
    # Volo Protocol (Sui)
    "0xd763599972ea5a8cfe53d182371ee010dc52ace7e39ccff7d8803ba7100fa46a",
    "0xe76970bbf9b038974f6086009799772db5190f249ce7d065a581b1ac0adaef75",
    # Giddy Finance extraction
    "0x237e67d9cAcAD42b4aCE31d61f444d14BEA78E39",
    # Rhea refund addr
    "0xBb5Fa936469CaDb8907f3aEF80F5B53f55Bc11f6",
})

# ── Suspicious Function Selectors (4-byte + common signatures) ───────────────

SUSPICIOUS_SELECTORS: tuple[str, ...] = (
    # Ownership / admin transfers
    "0x8da5cb5b",   # owner()
    "0xf2fde38b",   # transferOwnership(address)
    "0x3659cfe6",   # upgradeTo(address) — UUPS proxy upgrade
    "0x4f1ef286",   # upgradeToAndCall(address,bytes)
    "0x79ba5097",   # acceptOwnership()
    # Access control
    "0x2f2ff15d",   # grantRole(bytes32,address)
    "0xd547741f",   # revokeRole(bytes32,address)
    "0x91d14854",   # hasRole(bytes32,address)
    # Destructive
    "0x83197ef0",   # destroy() / selfdestruct pattern
    "0x9cb8a26a",   # suicide(address) alias
    # Dangerous approvals
    "0x095ea7b3",   # approve(address,uint256)
    "0xa22cb465",   # setApprovalForAll(address,bool)
    # Bridge / cross-chain
    "0x3f7658ff",   # lzReceive(bytes,bytes)
    "0x004e8f00",   # receivePayload (LayerZero variants)
    # Oracle manipulation helpers
    "0x41441d3b",   # updatePrice(uint256)
    "0xc6610657",   # setAggregator(address)
)

# ── Behavioral Regex Signatures ──────────────────────────────────────────────

# Unlimited / max uint256 approval
MAX_UINT_PATTERN = re.compile(r"0{64,}$|f{64,}$|ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", re.I)

# Flash-loan initiation selectors (Aave, Balancer, Uniswap V3, etc.)
FLASH_LOAN_SELECTORS: tuple[str, ...] = (
    "0xab9c4b5d",   # Aave: flashLoan(address,address[],uint256[],uint256,address,bytes,uint16)
    "0x42b0b77c",   # Aave: flashLoanSimple(address,address,uint256,bytes,uint16)
    "0x5a046a78",   # Balancer: flashLoan(address,address[],uint256[],bytes)
    "0x490e6cbc",   # Uniswap V3: flash(address,uint256,uint256,bytes)
)

# Patterns in calldata or prompt text that indicate drain / sweep behavior
DRAIN_PATTERN_RE = re.compile(
    r"\b(drain|sweep|rescue|emergency.?withdraw|migrate.?funds|withdraw.?all|clear.?balance)\b",
    re.IGNORECASE,
)

# Social-engineering / phishing language in prompts
SOCIAL_ENG_PATTERNS: tuple[str, ...] = (
    r"ignore\s+(previous|prior|all\s+previous)\s+instructions",
    r"bypass\s+(security|guard|safety|policy)",
    r"disable\s+(guard|safety|protection|check)",
    r"sign\s+this\s+(transaction|tx|message)\s+(blindly|without\s+reviewing|asap|urgent)",
    r"(durable\s+nonce|pre-?sign|pre\s+sign)",
    r"(internal\s+tool|internal\s+chat|new\s+trading\s+partner|integration\s+meeting)",
    r"upgrade\s+(contract|implementation|proxy)\s+(now|immediately|asap)",
)

# Bridge misconfiguration signatures
SINGLE_DVN_PATTERN = re.compile(r"requiredDVNCount\s*[=:]\s*1", re.IGNORECASE)

# ── High-Risk Action Combinations ────────────────────────────────────────────

HIGH_RISK_ACTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("approve", "transferFrom"),
    ("approve", "swap"),
    ("grantRole", "upgradeTo"),
    ("transferOwnership", "upgradeTo"),
    ("setAggregator", "updatePrice"),
    ("flashLoan", "swap"),
    ("lzReceive", "bridge"),
)


@dataclass(frozen=True)
class HackCheckResult:
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    signatures_matched: tuple[str, ...] = ()
    iocs_hit: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "signatures_matched": list(self.signatures_matched),
            "iocs_hit": list(self.iocs_hit),
        }


def _looks_like_address(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    if v.startswith("0x") and len(v) == 42:
        return all(c in "0123456789abcdefABCDEF" for c in v[2:])
    # Solana base58
    if len(v) in (43, 44):
        return True
    # NEAR
    if v.endswith(".near"):
        return True
    return False


def _extract_addresses(payload: dict[str, Any]) -> list[str]:
    """Recursively pull potential addresses from the intent payload."""
    addrs: list[str] = []
    for val in payload.values():
        if isinstance(val, str) and _looks_like_address(val):
            addrs.append(val.lower() if val.startswith("0x") else val)
        elif isinstance(val, dict):
            addrs.extend(_extract_addresses(val))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str) and _looks_like_address(item):
                    addrs.append(item.lower() if item.startswith("0x") else item)
    return addrs


def _check_iocs(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    iocs: list[str] = []
    for addr in _extract_addresses(payload):
        if addr in {a.lower() if a.startswith("0x") else a for a in KNOWN_MALICIOUS_ADDRESSES}:
            blockers.append(f"Interaction with known malicious address: {addr}")
            iocs.append(addr)
    return blockers, iocs


def _check_calldata(payload: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Returns (blockers, warnings, signatures_matched) from calldata analysis."""
    blockers: list[str] = []
    warnings: list[str] = []
    sigs: list[str] = []

    calldata: str = str(payload.get("calldata") or payload.get("data") or "")
    if not calldata.startswith("0x") or len(calldata) < 10:
        return blockers, warnings, sigs

    selector = calldata[:10].lower()

    # Suspicious selectors
    if selector in {s.lower() for s in SUSPICIOUS_SELECTORS}:
        name = {
            "0x8da5cb5b": "owner()",
            "0xf2fde38b": "transferOwnership(address)",
            "0x3659cfe6": "upgradeTo(address)",
            "0x4f1ef286": "upgradeToAndCall(address,bytes)",
            "0x79ba5097": "acceptOwnership()",
            "0x2f2ff15d": "grantRole(bytes32,address)",
            "0xd547741f": "revokeRole(bytes32,address)",
            "0x91d14854": "hasRole(bytes32,address)",
            "0x83197ef0": "destroy()",
            "0x9cb8a26a": "suicide(address)",
            "0x095ea7b3": "approve(address,uint256)",
            "0xa22cb465": "setApprovalForAll(address,bool)",
            "0x3f7658ff": "lzReceive(bytes,bytes)",
            "0x41441d3b": "updatePrice(uint256)",
            "0xc6610657": "setAggregator(address)",
        }.get(selector, selector)
        blockers.append(f"Critical selector detected: {name} ({selector})")
        sigs.append(f"critical_selector:{name}")

    # Flash-loan initiation
    if selector in {s.lower() for s in FLASH_LOAN_SELECTORS}:
        warnings.append("Flash-loan initiation detected; verify downstream actions.")
        sigs.append("flash_loan_init")

    # Unlimited approval
    if selector == "0x095ea7b3" and MAX_UINT_PATTERN.search(calldata):
        blockers.append("Unlimited ERC-20 approval (max uint256) detected.")
        sigs.append("unlimited_approval")

    return blockers, warnings, sigs


def _check_textual_signatures(payload: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    sigs: list[str] = []

    text = str(payload.get("prompt_text") or "")
    action = str(payload.get("action") or "")

    # Social-engineering / prompt-injection patterns
    for pattern in SOCIAL_ENG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            blockers.append(f"Social-engineering signature matched: {pattern[:40]}...")
            sigs.append(f"soceng:{pattern[:30]}")

    # Drift-style durable nonce hint
    if "durable nonce" in text.lower() and ("transfer" in text.lower() or "admin" in text.lower()):
        blockers.append("Durable-nonce admin-transfer pattern detected (Drift-style social-engineering signature).")
        sigs.append("durable_nonce_admin_transfer")

    # Drain / sweep language
    if DRAIN_PATTERN_RE.search(text):
        blockers.append("Drain/sweep language detected in intent prompt.")
        sigs.append("drain_language")

    # Bridge single-DVN misconfiguration in text or params
    if SINGLE_DVN_PATTERN.search(text):
        warnings.append("Single-DVN bridge configuration flagged (Kelp-style vulnerability).")
        sigs.append("single_dvn_bridge")

    # Action-pair risk
    # We look at action + method combinations
    method = str(payload.get("method") or "")
    for a, m in HIGH_RISK_ACTION_PAIRS:
        if a in action.lower() and m in (method.lower() or action.lower()):
            warnings.append(f"High-risk action pair: {a} + {m}")
            sigs.append(f"risk_pair:{a}_{m}")

    # Value anomalies
    value_eth = payload.get("value_eth")
    if isinstance(value_eth, (int, float)) and value_eth > 100:
        warnings.append(f"Very high value intent: {value_eth} ETH")
        sigs.append("high_value")

    return blockers, warnings, sigs


def _check_behavioral_sequence(payload: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Check for multi-step behavioral signatures in nested intent arrays."""
    blockers: list[str] = []
    warnings: list[str] = []
    sigs: list[str] = []

    steps = payload.get("steps") or payload.get("operations") or []
    if not isinstance(steps, list) or len(steps) < 2:
        return blockers, warnings, sigs

    actions = [str(s.get("action", "")).lower() for s in steps]
    calldatas = [str(s.get("calldata", s.get("data", ""))).lower() for s in steps]

    # Approve → TransferFrom sequence (classic allowance drain)
    for i in range(len(actions) - 1):
        if "approve" in actions[i] and "transfer" in actions[i + 1]:
            blockers.append(f"Step {i+1}-{i+2}: approve → transfer sequence detected.")
            sigs.append("sequence_approve_transfer")

    # Flash loan + swap + withdraw (Rhea-style)
    if any("flash" in a for a in actions) and any("swap" in a for a in actions) and any("withdraw" in a for a in actions):
        warnings.append("Flash-loan → swap → withdraw sequence detected (possible price manipulation).")
        sigs.append("sequence_flash_swap_withdraw")

    # Multiple grantRole / upgradeTo in same tx batch (Wasabi-style)
    grant_count = sum(1 for c in calldatas if "0x2f2ff15d" in c)
    upgrade_count = sum(1 for c in calldatas if "0x3659cfe6" in c or "0x4f1ef286" in c)
    if grant_count >= 1 and upgrade_count >= 1:
        blockers.append("Combined grantRole + upgradeTo in operation batch (UUPS takeover signature).")
        sigs.append("sequence_grant_upgrade")

    return blockers, warnings, sigs


def check_crypto_hack_signatures(payload: dict[str, Any]) -> HackCheckResult:
    """
    Run the full signature & behavioral detection suite against a normalized intent.
    """
    all_blockers: list[str] = []
    all_warnings: list[str] = []
    all_sigs: list[str] = []
    all_iocs: list[str] = []

    # 1. IOC / address blocklist
    b, i = _check_iocs(payload)
    all_blockers.extend(b)
    all_iocs.extend(i)

    # 2. Calldata analysis
    b, w, s = _check_calldata(payload)
    all_blockers.extend(b)
    all_warnings.extend(w)
    all_sigs.extend(s)

    # 3. Textual / prompt signatures
    b, w, s = _check_textual_signatures(payload)
    all_blockers.extend(b)
    all_warnings.extend(w)
    all_sigs.extend(s)

    # 4. Multi-step behavioral sequences
    b, w, s = _check_behavioral_sequence(payload)
    all_blockers.extend(b)
    all_warnings.extend(w)
    all_sigs.extend(s)

    return HackCheckResult(
        blockers=tuple(all_blockers),
        warnings=tuple(all_warnings),
        signatures_matched=tuple(all_sigs),
        iocs_hit=tuple(all_iocs),
    )
