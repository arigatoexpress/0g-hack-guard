#!/usr/bin/env python3
"""Build social launch assets for the 0guard hackathon packet."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "hackathon-0g" / "assets"
LOGO = ASSET_DIR / "0guard-logo.png"
BANNER = ASSET_DIR / "0guard-x-banner.png"


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    banner = _build_banner()
    banner.save(BANNER, optimize=True)
    print(BANNER)
    return 0


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "",
        "/Library/Fonts/Arial.ttf",
    ]
    for name in names:
        if name and Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default(size=size)


def _build_banner() -> Image.Image:
    width, height = 1500, 500
    image = Image.new("RGBA", (width, height), "#07090d")
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            nx = x / width
            ny = y / height
            teal = max(0.0, 1.0 - ((nx - 0.18) ** 2 + (ny - 0.24) ** 2) * 7.5)
            blue = max(0.0, 1.0 - ((nx - 0.84) ** 2 + (ny - 0.18) ** 2) * 8.0)
            green = max(0.0, 1.0 - ((nx - 0.65) ** 2 + (ny - 0.86) ** 2) * 9.0)
            r = int(7 + teal * 18 + blue * 10 + green * 7)
            g = int(9 + teal * 54 + blue * 32 + green * 48)
            b = int(13 + teal * 48 + blue * 70 + green * 34)
            pixels[x, y] = (min(r, 255), min(g, 255), min(b, 255), 255)

    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(-80, width + 80, 64):
        draw.line([(x, 0), (x + 180, height)], fill=(125, 211, 252, 22), width=1)
    for y in range(34, height, 58):
        draw.line([(0, y), (width, y)], fill=(52, 211, 153, 18), width=1)

    rail_y = 340
    nodes = [(560, "Intent"), (775, "Policy"), (990, "0G proof"), (1210, "Wallet")]
    draw.line([(520, rail_y), (1250, rail_y)], fill=(125, 211, 252, 115), width=4)
    for x, label in nodes:
        draw.ellipse((x - 12, rail_y - 12, x + 12, rail_y + 12), fill=(52, 211, 153, 235))
        draw.text((x, rail_y + 25), label, font=_font(22, bold=True), fill=(230, 247, 255, 230), anchor="mm")

    for points, color in [
        ([(1080, 72), (1308, 72), (1370, 178), (1140, 178)], (125, 211, 252, 36)),
        ([(1164, 230), (1395, 230), (1325, 350), (1096, 350)], (52, 211, 153, 30)),
        ([(238, 366), (430, 336), (474, 474), (274, 496)], (248, 193, 92, 22)),
    ]:
        draw.polygon(points, fill=color)
        draw.line(points + [points[0]], fill=(235, 248, 255, 44), width=2)

    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo = ImageOps.fit(logo, (230, 230), method=Image.Resampling.LANCZOS)
        mask = Image.new("L", logo.size, 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle((0, 0, 230, 230), radius=32, fill=255)
        glow = Image.new("RGBA", (330, 330), (0, 0, 0, 0))
        glow_mask = Image.new("L", (330, 330), 0)
        glow_draw = ImageDraw.Draw(glow_mask)
        glow_draw.rounded_rectangle((50, 50, 280, 280), radius=38, fill=210)
        glow.putalpha(glow_mask.filter(ImageFilter.GaussianBlur(34)))
        glow_tint = Image.new("RGBA", glow.size, (52, 211, 153, 96))
        image.alpha_composite(Image.composite(glow_tint, glow, glow.split()[-1]), (62, 84))
        logo_layer = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        logo_layer.paste(logo, (0, 0), mask)
        image.alpha_composite(logo_layer, (112, 134))

    title_font = _font(86, bold=True)
    sub_font = _font(42, bold=True)
    body_font = _font(27)
    pill_font = _font(22, bold=True)

    draw.text((390, 116), "0guard", font=title_font, fill=(242, 251, 255, 255))
    draw.text(
        (394, 210),
        "Pre-wallet firewall for AI agents",
        font=sub_font,
        fill=(186, 230, 253, 250),
    )
    draw.text(
        (397, 271),
        "Intent + calldata + policy + exploit intel before signing.",
        font=body_font,
        fill=(202, 216, 231, 235),
    )

    pill_x = 394
    for label, color in [
        ("28/28 detectors", (52, 211, 153, 225)),
        ("0G mainnet proof", (125, 211, 252, 225)),
        ("read-only guardrails", (248, 193, 92, 220)),
    ]:
        bbox = draw.textbbox((0, 0), label, font=pill_font)
        pill_w = bbox[2] - bbox[0] + 34
        draw.rounded_rectangle(
            (pill_x, 382, pill_x + pill_w, 424),
            radius=8,
            fill=(8, 13, 22, 205),
            outline=color,
            width=2,
        )
        draw.text((pill_x + 17, 391), label, font=pill_font, fill=(238, 247, 252, 245))
        pill_x += pill_w + 14

    draw.rounded_rectangle((28, 28, width - 28, height - 28), radius=10, outline=(125, 211, 252, 52), width=2)
    return image.convert("RGB")


if __name__ == "__main__":
    raise SystemExit(main())
