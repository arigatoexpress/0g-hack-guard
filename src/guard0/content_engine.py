"""
Content Engine for 0G Hack Guard
================================
Auto-generates X/Twitter posts from crypto hack threat intelligence.
Integrates with crypto_hack_guard signatures so when a new signature is
added, it can auto-generate awareness content.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# ── Severity thresholds ──────────────────────────────────────────────────────

SEVERITY_CRITICAL = 100_000_000
SEVERITY_MAJOR = 10_000_000

# ── Templates ────────────────────────────────────────────────────────────────

ALERT_TEMPLATES: dict[str, tuple[str, ...]] = {
    "critical": (
        "🚨 CRITICAL: {protocol} hacked for ${loss} on {chain}. {attack_vector_short}. Exit now. {hashtags}",
        "🚨 {protocol} exploit: ${loss} drained via {attack_vector_short}. {chain} users revoke approvals immediately. {hashtags}",
    ),
    "major": (
        "⚠️ {protocol} hacked for ${loss} on {chain}. {attack_vector_short}. Review your positions. {hashtags}",
        "⚠️ Major exploit: {protocol} lost ${loss} to {attack_vector_short}. Stay safe, {chain} fam. {hashtags}",
    ),
    "mid": (
        "🔍 {protocol} incident: ${loss} lost on {chain} via {attack_vector_short}. {hashtags}",
        "📉 {protocol} exploit: ${loss} — {attack_vector_short}. {hashtags}",
    ),
}

THREAD_TEMPLATES: dict[str, tuple[str, ...]] = {
    "critical": (
        "1/ 🚨 BREAKING: {protocol} just got hit for ${loss}. CRITICAL incident on {chain}. Here's what we know 👇 {hashtags}",
        "2/ Attack Vector: {attack_vector}",
        "3/ What happened: {description}",
        "4/ Impact: ${loss} in losses. User funds at risk. Contagion possible across {chain} ecosystem.",
        "5/ Action items: Revoke approvals. Withdraw if possible. Do NOT interact with {protocol} contracts until team confirms recovery.",
        "6/ Signatures matched: {signatures}",
        "7/ Attribution: {attribution}",
        "8/ Stay updated via @0g_hack_guard. Share this thread to warn others. 🛡️",
    ),
    "major": (
        "1/ ⚠️ {protocol} exploit alert: ${loss} lost on {chain}. Thread breakdown 👇 {hashtags}",
        "2/ How it happened: {attack_vector}",
        "3/ Technical details: {description}",
        "4/ Impact: ${loss} drained. Affected users should revoke approvals and monitor wallets.",
        "5/ Signatures detected: {signatures}",
        "6/ Lessons: {lesson}",
        "7/ Follow @0g_hack_guard for real-time alerts. Stay safe out there. 🛡️",
    ),
    "mid": (
        "1/ 📉 {protocol} incident: ${loss} lost on {chain}. Quick breakdown 👇 {hashtags}",
        "2/ Attack: {attack_vector}",
        "3/ What users should do: Revoke approvals, avoid interacting with affected contracts.",
        "4/ Detection signatures: {signatures}",
        "5/ Stay vigilant. Follow @0g_hack_guard for alerts. 🛡️",
    ),
}

SUMMARY_TEMPLATES: dict[str, tuple[str, ...]] = {
    "critical": (
        "📚 What we learned from {protocol} (${loss}): {lesson} Cross-chain infra & admin keys are the new battleground. Verify upgrades & bridge configs. {hashtags}",
    ),
    "major": (
        "📚 Lessons from {protocol} (${loss}): {lesson} Flash loans & oracle manipulation remain high-risk. Use protocols with multi-sig + timelock. {hashtags}",
    ),
    "mid": (
        "📚 {protocol} reminder (${loss}): {lesson} Even smaller incidents teach us to verify before signing. {hashtags}",
    ),
}

# ── Short-form mappings ──────────────────────────────────────────────────────

ATTACK_VECTOR_SHORT: dict[str, str] = {
    "social engineering": "social engineering",
    "bridge message forgery": "bridge forgery",
    "uups proxy upgrade": "proxy takeover",
    "flash loan oracle manipulation": "flash loan attack",
    "admin key compromise": "admin key leak",
    "oracle misconfiguration": "oracle misconfig",
    "access control exploit": "access control flaw",
    "hot wallet compromise": "hot wallet drain",
    "signature replay": "sig replay",
    "reserve manipulation": "reserve manipulation",
    "domain hijacking": "domain hijack",
    "smart contract bug": "contract bug",
    "mmr proof replay": "MMR replay",
    "donate negative amounts": "donation bug",
    "burnaddress accounting bug": "accounting bug",
    "fake state proof": "state proof forgery",
    "undisclosed": "unknown vector",
}

CHAIN_TAGS: dict[str, str] = {
    "ethereum": "ETH",
    "solana": "SOL",
    "near": "NEAR",
    "sui": "SUI",
    "base": "Base",
    "berachain": "BERA",
    "blast": "Blast",
    "arbitrum": "ARB",
    "multi-chain": "MultiChain",
    "tron": "TRON",
    "bsc": "BSC",
}

ATTACK_TAGS: dict[str, str] = {
    "social engineering": "SocialEngineering",
    "bridge message forgery": "BridgeSecurity",
    "uups proxy upgrade": "ProxySecurity",
    "flash loan oracle manipulation": "FlashLoan",
    "admin key compromise": "KeyManagement",
    "oracle misconfiguration": "OracleRisk",
    "access control exploit": "AccessControl",
    "hot wallet compromise": "WalletSecurity",
    "signature replay": "SignatureReplay",
    "reserve manipulation": "ReserveManipulation",
    "domain hijacking": "Web3Security",
    "smart contract bug": "SmartContract",
    "mmr proof replay": "BridgeExploit",
    "donate negative amounts": "LogicBug",
    "burnaddress accounting bug": "AccountingBug",
    "fake state proof": "BridgeExploit",
    "undisclosed": "DeFiHack",
}

# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_severity(loss_usd: float) -> str:
    if loss_usd >= SEVERITY_CRITICAL:
        return "critical"
    elif loss_usd >= SEVERITY_MAJOR:
        return "major"
    return "mid"


def _format_loss(loss_usd: float) -> str:
    if loss_usd >= 1_000_000_000:
        return f"{loss_usd / 1_000_000_000:.1f}B".replace(".0B", "B")
    elif loss_usd >= 1_000_000:
        return f"{loss_usd / 1_000_000:.1f}M".replace(".0M", "M")
    elif loss_usd >= 1_000:
        return f"{loss_usd / 1_000:.1f}K".replace(".0K", "K")
    return f"{loss_usd:.0f}"


def _generate_hashtags(protocol: str, chain: str, attack_vector: str) -> str:
    tags = ["#DeFi", "#CryptoSecurity", "#0GHackGuard"]

    proto_tag = (
        protocol.replace(" ", "").replace("-", "").replace(".", "").replace("/", "")
    )
    if proto_tag:
        tags.append(f"#{proto_tag}")

    chain_key = chain.lower()
    if chain_key in CHAIN_TAGS:
        tags.append(f"#{CHAIN_TAGS[chain_key]}")

    attack_lower = attack_vector.lower()
    for keyword, hashtag in ATTACK_TAGS.items():
        if keyword in attack_lower:
            tags.append(f"#{hashtag}")
            break
    else:
        tags.append("#DeFiHack")

    return " ".join(tags)


def _truncate_to_limit(text: str, limit: int = 280) -> str:
    if len(text) <= limit:
        return text
    truncate_at = limit - 3
    last_space = text.rfind(" ", 0, truncate_at)
    if last_space > 0:
        return text[:last_space] + "..."
    return text[:truncate_at] + "..."


def _match_signatures(attack_vector: str) -> list[str]:
    """Map attack vectors to crypto_hack_guard signature names."""
    sigs: list[str] = []
    av_lower = attack_vector.lower()

    mapping: dict[str, list[str]] = {
        "social engineering": ["durable_nonce_admin_transfer", "soceng"],
        "bridge": ["single_dvn_bridge", "lzReceive", "bridge"],
        "uups proxy upgrade": ["sequence_grant_upgrade", "upgradeTo", "grantRole"],
        "flash loan": ["sequence_flash_swap_withdraw", "flash_loan_init"],
        "admin key": ["transferOwnership", "grantRole", "acceptOwnership"],
        "oracle": ["setAggregator", "updatePrice", "oracle"],
        "access control": ["critical_selector", "access"],
        "hot wallet": ["high_value", "drain_language"],
        "signature replay": ["critical_selector:approve(address,uint256)", "signature"],
        "mmr proof": ["lzReceive", "bridge"],
        "donate negative": ["drain_language", "logic_bug"],
    }

    for keyword, signatures in mapping.items():
        if keyword in av_lower:
            sigs.extend(signatures)

    return list(dict.fromkeys(sigs))


# ── Dataclass ────────────────────────────────────────────────────────────────


@dataclass
class ContentOutput:
    protocol: str
    loss_usd: float
    severity: str
    alert_tweet: str
    thread_breakdown: list[str]
    summary_post: str
    hashtags: str
    signatures_matched: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "loss_usd": self.loss_usd,
            "severity": self.severity,
            "alert_tweet": self.alert_tweet,
            "thread_breakdown": self.thread_breakdown,
            "summary_post": self.summary_post,
            "hashtags": self.hashtags,
            "signatures_matched": self.signatures_matched,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ── Core functions ───────────────────────────────────────────────────────────


def generate_content(
    incident: dict[str, Any],
    *,
    alert_index: int = 0,
    summary_index: int = 0,
    custom_description: str | None = None,
    custom_lesson: str | None = None,
    custom_attribution: str | None = None,
) -> ContentOutput:
    """
    Generate tweet-ready content from a hack incident dict.

    Expected incident keys:
        protocol, loss_usd, attack_vector, chain, date
    Optional keys:
        description, attribution, lesson
    """
    protocol = incident.get("protocol", "Unknown")
    loss_usd = float(incident.get("loss_usd", 0))
    attack_vector = incident.get("attack_vector", "undisclosed")
    chain = incident.get("chain", "Unknown")
    date = incident.get("date", "")

    severity = _get_severity(loss_usd)
    loss_formatted = _format_loss(loss_usd)
    hashtags = _generate_hashtags(protocol, chain, attack_vector)
    signatures = _match_signatures(attack_vector)

    av_short = attack_vector
    for keyword, short in ATTACK_VECTOR_SHORT.items():
        if keyword in attack_vector.lower():
            av_short = short
            break

    # Alert tweet
    templates = ALERT_TEMPLATES[severity]
    alert_tmpl = templates[alert_index % len(templates)]
    alert = alert_tmpl.format(
        protocol=protocol,
        loss=loss_formatted,
        chain=chain,
        attack_vector=attack_vector,
        attack_vector_short=av_short,
        hashtags=hashtags,
    )
    alert = _truncate_to_limit(alert, 280)

    # Thread breakdown
    description = custom_description or incident.get(
        "description", f"{protocol} was exploited via {attack_vector}."
    )
    attribution = custom_attribution or incident.get("attribution", "Under investigation.")
    lesson = custom_lesson or incident.get(
        "lesson", "Verify all contract interactions and use multisig with timelocks."
    )

    thread: list[str] = []
    for tmpl in THREAD_TEMPLATES[severity]:
        tweet = tmpl.format(
            protocol=protocol,
            loss=loss_formatted,
            chain=chain,
            attack_vector=attack_vector,
            attack_vector_short=av_short,
            description=description,
            attribution=attribution,
            lesson=lesson,
            signatures=", ".join(signatures) if signatures else "none",
            hashtags=hashtags,
        )
        thread.append(_truncate_to_limit(tweet, 280))

    # Summary post
    summary_templates = SUMMARY_TEMPLATES[severity]
    summary_tmpl = summary_templates[summary_index % len(summary_templates)]
    summary = summary_tmpl.format(
        protocol=protocol,
        loss=loss_formatted,
        chain=chain,
        attack_vector=attack_vector,
        attack_vector_short=av_short,
        description=description,
        attribution=attribution,
        lesson=lesson,
        signatures=", ".join(signatures) if signatures else "none",
        hashtags=hashtags,
    )
    summary = _truncate_to_limit(summary, 280)

    return ContentOutput(
        protocol=protocol,
        loss_usd=loss_usd,
        severity=severity,
        alert_tweet=alert,
        thread_breakdown=thread,
        summary_post=summary,
        hashtags=hashtags,
        signatures_matched=signatures,
        metadata={
            "date": date,
            "chain": chain,
            "attack_vector": attack_vector,
            "description": description,
            "attribution": attribution,
            "lesson": lesson,
        },
    )


def generate_batch(incidents: list[dict[str, Any]]) -> list[ContentOutput]:
    """Generate content for a batch of incidents."""
    return [generate_content(inc) for inc in incidents]


def batch_to_json(incidents: list[dict[str, Any]], indent: int | None = 2) -> str:
    """Generate JSON output for X bot consumption from a batch of incidents."""
    outputs = generate_batch(incidents)
    return json.dumps([o.to_dict() for o in outputs], indent=indent, ensure_ascii=False)


# ── Signature integration ────────────────────────────────────────────────────


def _derive_attack_vector_from_signatures(
    signatures: list[str],
    blockers: list[str],
    warnings: list[str],
) -> str:
    """Infer attack vector from matched crypto_hack_guard signatures."""
    all_text = " ".join(signatures + blockers + warnings).lower()

    if "durable_nonce" in all_text or "soceng" in all_text:
        return "social engineering"
    elif "single_dvn" in all_text or "lzreceive" in all_text or "bridge" in all_text:
        return "bridge message forgery"
    elif "grant_upgrade" in all_text or "upgradeto" in all_text:
        return "UUPS proxy upgrade"
    elif "flash" in all_text:
        return "flash loan oracle manipulation"
    elif "transferownership" in all_text or "grantrole" in all_text:
        return "admin key compromise"
    elif "aggregator" in all_text or "oracle" in all_text or "updateprice" in all_text:
        return "oracle misconfiguration"
    elif "unlimited_approval" in all_text or "critical_selector" in all_text:
        return "signature replay"
    elif "drain_language" in all_text:
        return "hot wallet compromise"
    elif "high_value" in all_text:
        return "access control exploit"

    return "undisclosed"


def from_signature_result(
    protocol: str,
    chain: str,
    date: str,
    loss_usd: float,
    signature_result: dict[str, Any],
    *,
    attack_vector: str | None = None,
) -> ContentOutput:
    """
    Auto-generate content when a new crypto_hack_guard signature is matched.
    Derives attack vector and severity from the signature result.
    """
    sigs = signature_result.get("signatures_matched", [])
    blockers = signature_result.get("blockers", [])
    warnings = signature_result.get("warnings", [])

    if attack_vector is None:
        attack_vector = _derive_attack_vector_from_signatures(sigs, blockers, warnings)

    incident = {
        "protocol": protocol,
        "chain": chain,
        "date": date,
        "loss_usd": loss_usd,
        "attack_vector": attack_vector,
        "description": (
            f"Signatures triggered: {', '.join(sigs)}. "
            f"Blockers: {len(blockers)}. Warnings: {len(warnings)}."
        ),
        "attribution": "Auto-detected by 0G Hack Guard signature engine.",
        "lesson": (
            "Never sign transactions without reviewing calldata and destination "
            "addresses. Use 0G Hack Guard pre-flight checks."
        ),
    }

    return generate_content(incident)
