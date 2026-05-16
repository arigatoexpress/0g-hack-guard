#!/usr/bin/env python3
"""Build a no-text verdict-chain explainer plate.

This intentionally avoids generated labels or fake UI. The visual language is
simple: mixed blocks enter a checkpoint, green blocks join the protected chain,
and red blocks are diverted into quarantine before they can join.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "hackathon-0g" / "assets"
OUT_MP4 = ASSET_DIR / os.getenv(
    "VERDICT_EXPLAINER_NAME",
    "0guard-verdict-chain-explainer-polished-20260516.mp4",
)

WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 20.0
FRAMES = int(FPS * DURATION)

MAIN_Y = 292
QUARANTINE_Y = 508
SCANNER_X = 618
LEFT_X = -140


@dataclass(frozen=True)
class Block:
    kind: str
    start: float
    scan: float
    finish: float
    final_x: int


BLOCKS = (
    Block("green", 0.5, 2.8, 4.2, 820),
    Block("red", 3.0, 5.3, 7.1, 490),
    Block("green", 5.2, 7.5, 9.0, 910),
    Block("red", 7.4, 9.8, 11.7, 638),
    Block("green", 9.4, 11.8, 13.2, 1000),
    Block("red", 11.2, 13.7, 15.5, 786),
    Block("green", 13.4, 15.8, 17.0, 1090),
)


def main() -> int:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUT_MP4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, cwd=ROOT)
    assert proc.stdin is not None
    for frame in range(FRAMES):
        image = render_frame(frame / FPS)
        proc.stdin.write(image.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed while encoding verdict explainer")
    print(OUT_MP4)
    return 0


def render_frame(t: float) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (4, 8, 10))
    base = ImageDraw.Draw(canvas, "RGBA")
    _draw_background(base, t)

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    _draw_floor_lights(glow_draw, t)
    _draw_rails(glow_draw, t)
    _draw_motion_trails(glow_draw, t)
    _draw_final_chains(glow_draw, t)
    _draw_blocks(glow_draw, t)
    _draw_scanner(glow_draw, t)
    _draw_scan_particles(glow_draw, t)
    _draw_quarantine_cells(glow_draw, t)
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow)

    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_floor_lights(draw, t, crisp=True)
    _draw_rails(draw, t, crisp=True)
    _draw_motion_trails(draw, t, crisp=True)
    _draw_final_chains(draw, t, crisp=True)
    _draw_blocks(draw, t, crisp=True)
    _draw_scanner(draw, t, crisp=True)
    _draw_scan_particles(draw, t, crisp=True)
    _draw_quarantine_cells(draw, t, crisp=True)
    _draw_foreground_vignette(draw)
    return canvas.convert("RGB")


def _draw_background(draw: ImageDraw.ImageDraw, t: float) -> None:
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        if y % 2 == 0:
            draw.line(
                (0, y, WIDTH, y),
                fill=(
                    int(3 + 5 * ratio),
                    int(8 + 12 * ratio),
                    int(11 + 15 * ratio),
                    255,
                ),
                width=1,
            )
    for y in range(0, HEIGHT, 32):
        alpha = int(12 + 8 * math.sin(t * 0.45 + y * 0.05))
        draw.line((0, y, WIDTH, y), fill=(34, 80, 80, alpha), width=1)
    for x in range(120, WIDTH, 180):
        draw.line((x, 58, x - 105, 675), fill=(30, 92, 92, 18), width=2)
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0, 18))


def _draw_floor_lights(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    alpha = 72 if crisp else 42
    for y, color, x0, x1 in (
        (MAIN_Y + 132, (14, 218, 205), 72, 1210),
        (QUARANTINE_Y + 116, (255, 38, 70), 310, 930),
    ):
        draw.polygon(
            (
                x0,
                y,
                x1,
                y,
                x1 - 88,
                y + 42,
                x0 + 58,
                y + 42,
            ),
            fill=(*color, alpha // 2),
        )
        pulse = 0.5 + 0.5 * math.sin(t * 2.0 + y)
        draw.line((x0, y, x1, y), fill=(*color, int(alpha + 40 * pulse)), width=2 if crisp else 10)


def _draw_rails(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    cyan = (16, 238, 222, 190 if crisp else 145)
    red = (255, 42, 70, 145 if crisp else 105)
    width = 8 if crisp else 22
    draw.line((72, MAIN_Y + 68, 1210, MAIN_Y + 68), fill=cyan, width=width)
    draw.line((72, MAIN_Y + 104, 1210, MAIN_Y + 104), fill=(7, 72, 72, 155), width=4 if crisp else 14)
    draw.line((315, QUARANTINE_Y + 68, 925, QUARANTINE_Y + 68), fill=red, width=width)
    draw.line((315, QUARANTINE_Y + 104, 925, QUARANTINE_Y + 104), fill=(104, 14, 28, 155), width=4 if crisp else 14)
    pulse = (math.sin(t * 3.0) + 1) / 2
    draw.line((SCANNER_X - 58, 126, SCANNER_X - 58, 616), fill=(24, 230, 220, int(55 + 65 * pulse)), width=2 if crisp else 7)
    draw.line((SCANNER_X + 58, 126, SCANNER_X + 58, 616), fill=(24, 230, 220, int(40 + 45 * pulse)), width=2 if crisp else 7)


def _draw_final_chains(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    for block in BLOCKS:
        if block.kind != "green":
            continue
        if t < block.finish:
            continue
        _draw_cube(draw, block.final_x, MAIN_Y, 66, (26, 238, 126), 220 if crisp else 130)
    if t > 17.0:
        hold = min(1.0, (t - 17.0) / 1.35)
        for x in range(760, 1190, 68):
            _draw_cube(draw, x, MAIN_Y, 50, (18, 218, 104), int((176 if crisp else 98) * hold))


def _draw_blocks(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    for block in BLOCKS:
        if t < block.start:
            continue
        size = 74 if block.kind == "green" else 68
        color = (30, 236, 122) if block.kind == "green" else (245, 36, 66)
        if t <= block.scan:
            p = _ease((t - block.start) / (block.scan - block.start))
            x = _lerp(LEFT_X, SCANNER_X, p)
            y = MAIN_Y
            incoming_color = (70, 235, 220) if block.kind == "green" else (250, 70, 80)
            _draw_cube(draw, x, y, size, incoming_color, 190 if crisp else 105)
            continue
        if t <= block.finish:
            p = _ease((t - block.scan) / (block.finish - block.scan))
            if block.kind == "green":
                x = _lerp(SCANNER_X, block.final_x, p)
                y = MAIN_Y - 22 * math.sin(p * math.pi)
            else:
                x = _lerp(SCANNER_X, block.final_x, p)
                y = _lerp(MAIN_Y, QUARANTINE_Y, p) - 54 * math.sin(p * math.pi)
            _draw_cube(draw, x, y, size, color, 220 if crisp else 130)
            _draw_decision_path(draw, x, y, block.kind, p, crisp)
            _draw_verdict_burst(draw, SCANNER_X, MAIN_Y, color, t - block.scan, crisp)
            continue
        if block.kind == "red":
            _draw_cube(draw, block.final_x, QUARANTINE_Y, size, color, 190 if crisp else 112)


def _draw_motion_trails(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    for block in BLOCKS:
        if t < block.start or t > block.finish:
            continue
        color = (30, 236, 122) if block.kind == "green" else (245, 36, 66)
        points = []
        for offset in (0.0, 0.16, 0.32, 0.48):
            sample = max(block.start, t - offset)
            if sample <= block.scan:
                p = _ease((sample - block.start) / (block.scan - block.start))
                points.append((_lerp(LEFT_X, SCANNER_X, p), MAIN_Y + 39))
            else:
                p = _ease((sample - block.scan) / (block.finish - block.scan))
                if block.kind == "green":
                    points.append((_lerp(SCANNER_X, block.final_x, p), MAIN_Y + 39 - 22 * math.sin(p * math.pi)))
                else:
                    points.append((_lerp(SCANNER_X, block.final_x, p), _lerp(MAIN_Y, QUARANTINE_Y, p) + 39 - 54 * math.sin(p * math.pi)))
        for index, (x, y) in enumerate(points[1:], start=1):
            alpha = (70 if crisp else 38) // index
            draw.ellipse((x - 24, y - 8, x + 24, y + 8), fill=(*color, alpha))


def _draw_scanner(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    active = any(abs(t - block.scan) < 0.85 for block in BLOCKS)
    alpha = 225 if crisp else 128
    if active:
        alpha += 35 if crisp else 25
    shield = [
        (SCANNER_X, 126),
        (SCANNER_X + 94, 174),
        (SCANNER_X + 72, 420),
        (SCANNER_X, 506),
        (SCANNER_X - 72, 420),
        (SCANNER_X - 94, 174),
    ]
    inner = [
        (SCANNER_X, 156),
        (SCANNER_X + 64, 190),
        (SCANNER_X + 50, 393),
        (SCANNER_X, 452),
        (SCANNER_X - 50, 393),
        (SCANNER_X - 64, 190),
    ]
    fill_alpha = 46 if crisp else 24
    draw.polygon(shield, outline=(36, 238, 230, alpha), fill=(18, 160, 170, fill_alpha))
    draw.polygon(inner, outline=(130, 255, 244, int(alpha * 0.66)), fill=(40, 255, 236, 14 if crisp else 8))
    draw.line((SCANNER_X - 82, 218, SCANNER_X + 82, 218), fill=(65, 255, 236, 115), width=3 if crisp else 10)
    draw.line((SCANNER_X - 66, 388, SCANNER_X + 66, 388), fill=(65, 255, 236, 72), width=2 if crisp else 7)
    scan_y = 176 + ((t * 156) % 252)
    draw.polygon(
        (
            SCANNER_X - 70,
            scan_y - 8,
            SCANNER_X + 70,
            scan_y - 8,
            SCANNER_X + 58,
            scan_y + 8,
            SCANNER_X - 58,
            scan_y + 8,
        ),
        fill=(120, 255, 239, 120 if crisp else 72),
    )
    phase = t * 2.2
    for radius in (44, 68, 92, 118):
        wave_alpha = int((82 if crisp else 46) * (0.5 + 0.5 * math.sin(phase + radius * 0.13)))
        draw.ellipse((SCANNER_X - radius, 315 - radius, SCANNER_X + radius, 315 + radius), outline=(62, 250, 230, wave_alpha), width=2 if crisp else 8)
    for angle in range(0, 360, 45):
        length = 74 + 8 * math.sin(t * 2 + angle)
        sx = SCANNER_X + math.cos(math.radians(angle + t * 14)) * 36
        sy = 315 + math.sin(math.radians(angle + t * 14)) * 36
        ex = SCANNER_X + math.cos(math.radians(angle + t * 14)) * length
        ey = 315 + math.sin(math.radians(angle + t * 14)) * length
        draw.line((sx, sy, ex, ey), fill=(70, 255, 236, 42 if crisp else 25), width=1 if crisp else 4)


def _draw_scan_particles(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    for index in range(28):
        phase = (index * 0.73 + t * 1.75) % 1.0
        x = SCANNER_X - 120 + phase * 240
        y = 178 + ((index * 37 + int(t * 45)) % 270)
        size = 2 if crisp else 6
        alpha = 120 if crisp else 60
        draw.ellipse((x - size, y - size, x + size, y + size), fill=(118, 255, 236, alpha))


def _draw_quarantine_cells(draw: ImageDraw.ImageDraw, t: float, crisp: bool = False) -> None:
    for block in BLOCKS:
        if block.kind != "red" or t < block.finish:
            continue
        x = block.final_x
        y = QUARANTINE_Y
        alpha = 178 if crisp else 95
        draw.rounded_rectangle((x - 48, y - 18, x + 98, y + 96), radius=10, outline=(255, 52, 72, alpha), width=3 if crisp else 10)
        draw.line((x - 40, y + 9, x + 88, y + 9), fill=(255, 52, 72, alpha), width=2 if crisp else 7)
        draw.line((x - 40, y + 72, x + 88, y + 72), fill=(255, 52, 72, alpha // 2), width=1 if crisp else 5)


def _draw_verdict_burst(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    color: tuple[int, int, int],
    age: float,
    crisp: bool,
) -> None:
    if age < 0 or age > 1.1:
        return
    p = age / 1.1
    radius = 48 + 104 * p
    alpha = int((185 if crisp else 95) * (1 - p))
    draw.ellipse((x - radius, y - radius + 46, x + radius, y + radius + 46), outline=(*color, alpha), width=5 if crisp else 14)


def _draw_decision_path(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    kind: str,
    progress: float,
    crisp: bool,
) -> None:
    if progress < 0.08:
        return
    color = (30, 236, 122) if kind == "green" else (245, 36, 66)
    alpha = 108 if crisp else 62
    if kind == "green":
        draw.arc((SCANNER_X - 20, MAIN_Y - 26, x + 42, y + 94), start=300, end=35, fill=(*color, alpha), width=3 if crisp else 10)
    else:
        draw.arc((min(SCANNER_X, x) - 38, MAIN_Y + 28, max(SCANNER_X, x) + 92, QUARANTINE_Y + 112), start=20, end=165, fill=(*color, alpha), width=3 if crisp else 10)


def _draw_cube(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    size: int,
    color: tuple[int, int, int],
    alpha: int,
) -> None:
    x = int(x)
    y = int(y)
    depth = int(size * 0.28)
    r, g, b = color
    front = (r, g, b, alpha)
    top = (min(255, r + 45), min(255, g + 45), min(255, b + 45), int(alpha * 0.9))
    side = (max(0, r - 42), max(0, g - 42), max(0, b - 42), int(alpha * 0.88))
    draw.rounded_rectangle((x - 4, y + size - 4, x + size + depth + 6, y + size + 10), radius=8, fill=(0, 0, 0, int(alpha * 0.25)))
    draw.polygon((x, y, x + size, y, x + size + depth, y - depth, x + depth, y - depth), fill=top)
    draw.polygon((x + size, y, x + size + depth, y - depth, x + size + depth, y + size - depth, x + size, y + size), fill=side)
    draw.rounded_rectangle((x, y, x + size, y + size), radius=max(4, size // 9), fill=front)
    draw.rounded_rectangle((x + 8, y + 8, x + size - 8, y + size - 8), radius=max(3, size // 12), outline=(255, 255, 255, int(alpha * 0.18)), width=2)
    draw.line((x, y, x + size, y, x + size + depth, y - depth), fill=(220, 255, 255, int(alpha * 0.4)), width=2)
    draw.line((x, y + size, x + size, y + size, x + size + depth, y + size - depth), fill=(0, 0, 0, int(alpha * 0.3)), width=2)


def _draw_foreground_vignette(draw: ImageDraw.ImageDraw) -> None:
    for inset in range(0, 72, 12):
        alpha = int((72 - inset) * 0.32)
        draw.rectangle((inset, inset, WIDTH - inset, HEIGHT - inset), outline=(0, 0, 0, alpha), width=10)


def _ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def _lerp(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


if __name__ == "__main__":
    raise SystemExit(main())
