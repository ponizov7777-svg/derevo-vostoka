#!/usr/bin/env python3
"""Build laser keychain PNGs for tiger paw souvenirs."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "images" / "мотивация"
CANVAS = 3072


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in (
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def ellipse_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    angle_deg: float,
    n: int = 48,
) -> list[tuple[float, float]]:
    angle = np.deg2rad(angle_deg)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    pts: list[tuple[float, float]] = []
    for t in np.linspace(0, 2 * np.pi, n, endpoint=False):
        x = rx * np.cos(t)
        y = ry * np.sin(t)
        rx_rot = x * cos_a - y * sin_a + cx
        ry_rot = x * sin_a + y * cos_a + cy
        pts.append((float(rx_rot), float(ry_rot)))
    return pts


def draw_badge_shell(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], lug_cx: int) -> None:
    x0, y0, x1, y1 = box
    r = 180
    draw.rounded_rectangle(box, radius=r, fill=0)

    lug_w, lug_h = 260, 240
    lug_top = y0 - lug_h + 50
    draw.rounded_rectangle(
        (lug_cx - lug_w // 2, lug_top, lug_cx + lug_w // 2, y0 + 40),
        radius=80,
        fill=0,
    )


def draw_badge_inner(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    inset: int,
    lug_cx: int,
    hole_r: int,
    lug_top: int,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(
        (x0 + inset, y0 + inset, x1 - inset, y1 - inset),
        radius=max(180 - inset, 20),
        fill=255,
    )
    draw.ellipse(
        (lug_cx - hole_r, lug_top + 118, lug_cx + hole_r, lug_top + 118 + hole_r * 2),
        fill=255,
    )


def draw_paw(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    scale: float,
) -> None:
    """Smooth paw pads traced from the reference photo proportions."""
    pads = [
        # main pad — wide, three lobes approximated by a large ellipse + two small side lobes
        ellipse_points(cx + 0.02 * scale, cy + 0.34 * scale, 0.34 * scale, 0.24 * scale, -4, 56),
        ellipse_points(cx - 0.18 * scale, cy + 0.42 * scale, 0.10 * scale, 0.08 * scale, -18, 32),
        ellipse_points(cx + 0.22 * scale, cy + 0.42 * scale, 0.10 * scale, 0.08 * scale, 18, 32),
        # toes
        ellipse_points(cx - 0.28 * scale, cy - 0.08 * scale, 0.11 * scale, 0.15 * scale, -28, 40),
        ellipse_points(cx - 0.08 * scale, cy - 0.20 * scale, 0.12 * scale, 0.17 * scale, -8, 40),
        ellipse_points(cx + 0.12 * scale, cy - 0.21 * scale, 0.12 * scale, 0.17 * scale, 10, 40),
        ellipse_points(cx + 0.30 * scale, cy - 0.10 * scale, 0.11 * scale, 0.15 * scale, 28, 40),
    ]
    for poly in pads:
        draw.polygon(poly, fill=0)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    cx: int,
    y: int,
    font: ImageFont.FreeTypeFont,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((cx - tw // 2, y), text, fill=0, font=font)


def finalize(img: Image.Image) -> Image.Image:
    arr = np.array(img)
    return Image.fromarray(np.where(arr < 128, 0, 255).astype(np.uint8), mode="L")


def build_text_keychain() -> Image.Image:
    img = Image.new("L", (CANVAS, CANVAS), 255)
    draw = ImageDraw.Draw(img)

    margin = 260
    badge = (margin, 380, CANVAS - margin, CANVAS - margin)
    cx = CANVAS // 2
    hole_r = 48
    lug_top = badge[1] - 190

    draw_badge_shell(draw, badge, cx)
    draw_badge_inner(draw, badge, inset=34, lug_cx=cx, hole_r=hole_r, lug_top=lug_top)

    inset = 78
    inner = (badge[0] + inset, badge[1] + inset, badge[2] - inset, badge[3] - inset)
    draw.rounded_rectangle(inner, radius=120, outline=0, width=16)

    font = load_font(118)
    draw_centered_text(draw, "СЛЕД ТИГРА", cx, badge[1] + 130, font)
    draw_centered_text(draw, "ДИКАЯ ТРОПА", cx, badge[3] - 230, font)

    paw_cy = (badge[1] + badge[3]) // 2 + 80
    draw_paw(draw, cx, paw_cy, scale=720)

    return finalize(img)


def build_silhouette_keychain() -> Image.Image:
    img = Image.new("L", (CANVAS, CANVAS), 255)
    draw = ImageDraw.Draw(img)

    margin = 320
    badge = (margin, 380, CANVAS - margin, CANVAS - margin)
    cx = CANVAS // 2
    hole_r = 48
    lug_top = badge[1] - 190

    draw_badge_shell(draw, badge, cx)
    draw_badge_inner(draw, badge, inset=34, lug_cx=cx, hole_r=hole_r, lug_top=lug_top)

    paw_cy = (badge[1] + badge[3]) // 2 + 40
    draw_paw(draw, cx, paw_cy, scale=880)

    return finalize(img)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "sled_tigra_laser.png": build_text_keychain(),
        "sled_tigra_silhouette_laser.png": build_silhouette_keychain(),
    }
    for name, img in outputs.items():
        path = OUT_DIR / name
        img.save(path)
        print(f"Saved: {path}")


if __name__ == "__main__":
    main()
