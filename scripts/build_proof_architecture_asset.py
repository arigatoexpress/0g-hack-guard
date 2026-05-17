#!/usr/bin/env python3
"""Build deterministic proof architecture graphics for the public 0guard packet."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "hackathon-0g" / "assets"
ARCHITECTURE = ASSET_DIR / "0guard-proof-architecture.png"
BANNER = ASSET_DIR / "0guard-x-banner.png"

BG = "#050708"
PANEL = "#0b1013"
PANEL_2 = "#10161a"
LINE = "#29424a"
TEXT = "#eef7f2"
MUTED = "#9dafaa"
GREEN = "#46ff9a"
CYAN = "#9bd5c4"
AMBER = "#e2b25b"
RED = "#ff526b"


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    architecture = build_architecture()
    architecture.save(ARCHITECTURE, optimize=True)
    build_banner(architecture).save(BANNER, optimize=True)
    print(ARCHITECTURE)
    print(BANNER)
    return 0


def build_architecture() -> Image.Image:
    image = Image.new("RGB", (1600, 900), BG)
    draw = ImageDraw.Draw(image)
    draw_grid(draw, 1600, 900)

    title_font = font(72, bold=True)
    subtitle_font = font(30)
    label_font = font(21, bold=True)
    body_font = font(21)
    mono_font = mono(19)

    draw.text((92, 78), "0guard", fill=TEXT, font=title_font)
    draw.text(
        (96, 164),
        "Checks first. Proof trail second. Wallet last.",
        fill=CYAN,
        font=subtitle_font,
    )
    badge(draw, (1156, 82, 1468, 122), "0G mainnet proof anchored", GREEN, font(19, bold=True))
    badge(draw, (1156, 134, 1468, 174), "No signing from workbench", AMBER, font(19, bold=True))

    y = 258
    cards = [
        {
            "box": (92, y, 420, y + 290),
            "title": "1. Normalize intent",
            "items": [
                "Action, mode, value",
                "Calldata selectors",
                "Signer requirement",
                "Agent identity",
            ],
            "accent": CYAN,
        },
        {
            "box": (494, y, 846, y + 290),
            "title": "2. Apply guard code",
            "items": [
                "Policy engine",
                "Exploit signatures",
                "Source-linked OSINT",
                "Reputation adapters",
            ],
            "accent": GREEN,
        },
        {
            "box": (920, y, 1268, y + 290),
            "title": "3. Return verdict",
            "items": [
                "allow / review / deny",
                "receipt hash",
                "human explanation",
                "operator next step",
            ],
            "accent": AMBER,
        },
        {
            "box": (1340, y, 1508, y + 290),
            "title": "Wallet",
            "items": [
                "only after",
                "safe verdict",
                "or separate",
                "approval",
            ],
            "accent": RED,
        },
    ]
    for card in cards:
        panel(draw, card["box"], card["accent"])
        x0, y0, x1, _ = card["box"]
        draw.text((x0 + 24, y0 + 26), card["title"], fill=TEXT, font=label_font)
        for idx, item in enumerate(card["items"]):
            draw.text((x0 + 28, y0 + 82 + idx * 42), item, fill=MUTED, font=body_font)

    arrow(draw, (420, y + 145), (494, y + 145), CYAN)
    arrow(draw, (846, y + 145), (920, y + 145), GREEN)
    arrow(draw, (1268, y + 145), (1340, y + 145), AMBER)

    proof_y = 622
    panel(draw, (92, proof_y, 730, 820), GREEN)
    draw.text((120, proof_y + 24), "Public proof ladder", fill=TEXT, font=label_font)
    proof_lines = [
        ("Chain", "0G mainnet receipt anchor"),
        ("Storage", "deterministic root hash, upload gated"),
        ("Compute", "0GM manifest, paid inference gated"),
        ("Telegram", "preview only, no outbound send"),
    ]
    for idx, (left, right) in enumerate(proof_lines):
        yy = proof_y + 74 + idx * 30
        draw.text((122, yy), left, fill=GREEN if idx == 0 else CYAN, font=mono_font)
        draw.text((254, yy), right, fill=MUTED, font=body_font)

    panel(draw, (784, proof_y, 1508, 820), AMBER)
    draw.text((812, proof_y + 24), "Claim boundary judges can trust", fill=TEXT, font=label_font)
    boundary = [
        ("Live", "intent firewall, incident data, mainnet anchor, no-send previews."),
        ("Prepared", "Router key path, hot-wallet roles, peer drafts, Pi sentinels."),
        ("Not claimed", "paid inference, storage upload/readback, staking, fund movement."),
    ]
    for idx, (left, right) in enumerate(boundary):
        yy = proof_y + 74 + idx * 42
        draw.text((814, yy), left, fill=AMBER if idx == 2 else CYAN, font=mono_font)
        draw.text((970, yy), right, fill=MUTED, font=font(19))

    draw.text((96, 838), "Source-ready, live-proof-pending where appropriate. No private keys or paid API keys appear in repo outputs.", fill="#71837f", font=font(18))
    return image


def build_banner(architecture: Image.Image) -> Image.Image:
    banner = Image.new("RGB", (1500, 500), BG)
    draw = ImageDraw.Draw(banner)
    draw_grid(draw, 1500, 500, step=38)
    crop = architecture.crop((72, 52, 1528, 550)).resize((760, 260), Image.Resampling.LANCZOS)
    banner.paste(crop, (690, 118))
    panel(draw, (54, 64, 650, 430), CYAN)
    draw.text((92, 108), "0guard", fill=TEXT, font=font(82, bold=True))
    draw.text((96, 202), "Pre-wallet firewall for AI agents", fill=CYAN, font=font(34, bold=True))
    draw.text((98, 266), "Intent, calldata, policy, exploit intel.", fill=MUTED, font=font(25))
    draw.text((98, 302), "Checked before signing.", fill=MUTED, font=font(25))
    badge(draw, (96, 350, 274, 394), "28/28 detectors", GREEN, font(21, bold=True))
    badge(draw, (294, 350, 514, 394), "0G mainnet proof", CYAN, font(21, bold=True))
    return banner


def draw_grid(draw: ImageDraw.ImageDraw, width: int, height: int, *, step: int = 44) -> None:
    for x in range(0, width, step):
        draw.line((x, 0, x, height), fill="#0d2426", width=1)
    for y in range(0, height, step):
        draw.line((0, y, width, y), fill="#0d2426", width=1)
    draw.rectangle((26, 26, width - 26, height - 26), outline="#16373a", width=2)


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], accent: str) -> None:
    draw.rounded_rectangle(box, radius=8, fill=PANEL, outline=LINE, width=2)
    x0, y0, x1, _ = box
    draw.line((x0 + 2, y0 + 2, x1 - 2, y0 + 2), fill=accent, width=3)


def badge(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    accent: str,
    badge_font: ImageFont.ImageFont,
) -> None:
    draw.rounded_rectangle(box, radius=8, fill=PANEL_2, outline=accent, width=2)
    text_box = draw.textbbox((0, 0), text, font=badge_font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    x0, y0, x1, y1 = box
    draw.text(
        (x0 + (x1 - x0 - text_w) / 2, y0 + (y1 - y0 - text_h) / 2 - 2),
        text,
        fill=TEXT,
        font=badge_font,
    )


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
) -> None:
    sx, sy = start
    ex, ey = end
    draw.line((sx + 10, sy, ex - 18, ey), fill=color, width=4)
    draw.polygon([(ex - 18, ey - 11), (ex - 18, ey + 11), (ex + 2, ey)], fill=color)


def font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def mono(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return font(size)


if __name__ == "__main__":
    raise SystemExit(main())
