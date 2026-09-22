#!/usr/bin/env python3
"""Build a clean vector SVG logo for «подножье ПИДАНА»."""

from __future__ import annotations

import math
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "images" / "подножье-пидана" / "лазер"
OUT_SVG = OUT_DIR / "подножье_логотип_вектор.svg"
OUT_PNG = OUT_DIR / "подножье_логотип_вектор.png"
OUT_SVG_BLACK = OUT_DIR / "подножье_логотип_вектор_чёрный.svg"

FILL = "#3A2A1A"
SCRIPT_FONT = Path(r"C:\Windows\Fonts\Hello Dina Script Style .otf")
BOLD_FONT = Path(r"C:\Windows\Fonts\DrukCyr-Heavy.ttf")


def glyph_path(
    font: TTFont, text: str, font_size: float
) -> tuple[str, float, float, float, float, float]:
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = font_size / font["head"].unitsPerEm
    pen = SVGPathPen(glyph_set)
    bp = BoundsPen(glyph_set)
    x_adv = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            raise KeyError(f"Missing glyph for {ch!r}")
        glyph = glyph_set[gname]
        matrix = (scale, 0, 0, -scale, x_adv, 0)
        glyph.draw(TransformPen(pen, matrix))
        glyph.draw(TransformPen(bp, matrix))
        x_adv += glyph.width * scale
    x0, y0, x1, y1 = bp.bounds
    return pen.getCommands(), x_adv, x0, y0, x1, y1


def zigzag_ribbon(points: list[tuple[float, float]], half_w: float) -> str:
    """Closed evenodd hole along a polyline (constant half-width band)."""
    if len(points) < 2:
        return ""
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(points):
        if i == 0:
            dx, dy = points[1][0] - x, points[1][1] - y
        elif i == len(points) - 1:
            dx, dy = x - points[i - 1][0], y - points[i - 1][1]
        else:
            dx1, dy1 = x - points[i - 1][0], y - points[i - 1][1]
            dx2, dy2 = points[i + 1][0] - x, points[i + 1][1] - y
            dx, dy = dx1 + dx2, dy1 + dy2
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        left.append((x + nx * half_w, y + ny * half_w))
        right.append((x - nx * half_w, y - ny * half_w))
    seq = left + list(reversed(right))
    parts = [f"M {seq[0][0]:.2f},{seq[0][1]:.2f}"]
    parts.extend(f"L {x:.2f},{y:.2f}" for x, y in seq[1:])
    parts.append("Z")
    return " ".join(parts)


def icon_path(ox: float, oy: float, h: float) -> str:
    """Twin-peak cabin mark with door, window, and chevron cutouts."""
    s = h / 100.0

    def P(x: float, y: float) -> tuple[float, float]:
        return ox + x * s, oy + y * s

    def M(x: float, y: float) -> str:
        px, py = P(x, y)
        return f"M {px:.2f},{py:.2f}"

    def L(x: float, y: float) -> str:
        px, py = P(x, y)
        return f"L {px:.2f},{py:.2f}"

    # Outer silhouette — double gable / twin peaks over cabin body
    outer = " ".join(
        [
            M(4, 100),
            L(4, 58),
            L(22, 14),  # left peak
            L(34, 38),
            L(50, 2),  # right peak
            L(78, 58),
            L(78, 100),
            "Z",
        ]
    )
    door = " ".join([M(38, 100), L(38, 52), L(48, 52), L(48, 100), "Z"])
    window = " ".join([M(26, 70), L(26, 58), L(33, 58), L(33, 70), "Z"])

    holes = [door, window]
    half_w = 1.55 * s
    amp = 4.0
    for y in (64, 76, 88):
        # left wall zigzag (3 peaks)
        pts_l = [P(x, y + (amp if i % 2 else -amp) * (0 if i in (0, 4) else 1)) for i, x in enumerate((7, 13, 19, 25, 31))]
        # endpoints on centerline
        pts_l[0] = P(7, y)
        pts_l[-1] = P(31, y)
        pts_l[1] = P(13, y - amp)
        pts_l[2] = P(19, y + amp * 0.15)
        pts_l[3] = P(25, y - amp)
        holes.append(zigzag_ribbon(pts_l, half_w))

        pts_r = [P(7, y)] * 5  # placeholder
        pts_r = [
            P(50, y),
            P(56, y - amp),
            P(62, y + amp * 0.15),
            P(68, y - amp),
            P(75, y),
        ]
        holes.append(zigzag_ribbon(pts_r, half_w))

    return outer + " " + " ".join(holes)


def icon_draw_pil(
    draw: ImageDraw.ImageDraw, ox: float, oy: float, h: float, fill: str, scale: float
) -> None:
    s = (h / 100.0) * scale
    ox_s, oy_s = ox * scale, oy * scale

    def pt(x: float, y: float) -> tuple[float, float]:
        return ox_s + x * s, oy_s + y * s

    outer = [pt(4, 100), pt(4, 58), pt(22, 14), pt(34, 38), pt(50, 2), pt(78, 58), pt(78, 100)]
    draw.polygon(outer, fill=fill)
    draw.rectangle([pt(38, 52), pt(48, 100)], fill="#FFFFFF")
    draw.rectangle([pt(26, 58), pt(33, 70)], fill="#FFFFFF")

    amp = 4.0
    for y in (64, 76, 88):
        for pts in (
            [pt(7, y), pt(13, y - amp), pt(19, y + amp * 0.15), pt(25, y - amp), pt(31, y)],
            [pt(50, y), pt(56, y - amp), pt(62, y + amp * 0.15), pt(68, y - amp), pt(75, y)],
        ):
            draw.line(pts, fill="#FFFFFF", width=max(2, int(3.1 * s)))


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Fallback if Style font missing
    script_path = SCRIPT_FONT if SCRIPT_FONT.exists() else Path(r"C:\Windows\Fonts\Hello Dina Script.otf")
    script_tt = TTFont(script_path)
    bold_tt = TTFont(BOLD_FONT)

    pidana_size = 58.0
    pod_size = 36.0
    gap = 12.0
    margin = 6.0

    pidana_d, _, px0, py0, px1, py1 = glyph_path(bold_tt, "ПИДАНА", pidana_size)
    pod_d, _, sx0, sy0, sx1, sy1 = glyph_path(script_tt, "подножье", pod_size)

    icon_x = margin
    text_block_top_offset = 0.0

    # Place text first, then size icon to text block
    text_x0 = 0.0  # temporary; recalculated
    pidana_baseline = 0.0
    pod_baseline = (0 + py0) - 7.0 - sy1  # relative; recompute below

    # Provisional icon height = text stack
    script_h = abs(sy0) + max(sy1, 0)
    pidana_h = abs(py0) + max(py1, 0)
    icon_h = script_h + 7.0 + pidana_h
    icon_w = icon_h * 0.82

    text_x = icon_x + icon_w + gap
    pidana_baseline = margin + icon_h - max(py1, 0)
    pidana_tx = text_x - px0
    pidana_ty = pidana_baseline
    pod_baseline = (pidana_baseline + py0) - 7.0 - sy1
    pod_tx = text_x - sx0
    pod_ty = pod_baseline

    script_top = pod_ty + sy0
    icon_y = script_top
    pidana_bottom = pidana_baseline + py1
    icon_h = pidana_bottom - icon_y
    icon_w = icon_h * 0.82
    text_x = icon_x + icon_w + gap
    pidana_tx = text_x - px0
    pod_tx = text_x - sx0

    right = max(pidana_tx + px1, pod_tx + sx1) + margin
    top = min(icon_y, script_top) - 2
    bottom = max(icon_y + icon_h, pidana_bottom) + margin
    shift_y = -top
    vb_w = right
    vb_h = bottom + shift_y

    phys_w = 80.0
    phys_h = phys_w * vb_h / vb_w

    mark = icon_path(icon_x, icon_y + shift_y, icon_h)
    pod_tf = f"translate({pod_tx:.3f} {pod_ty + shift_y:.3f})"
    pid_tf = f"translate({pidana_tx:.3f} {pidana_ty + shift_y:.3f})"

    def write_svg(path: Path, fill: str) -> None:
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{phys_w:.3f}mm" height="{phys_h:.3f}mm"
     viewBox="0 0 {vb_w:.2f} {vb_h:.2f}">
  <title>подножье ПИДАНА</title>
  <desc>Clean vector logo — geometric mark and outlined Cyrillic wordmark.</desc>
  <g id="logo" fill="{fill}" fill-rule="evenodd">
    <path id="mark" d="{mark}"/>
    <path id="podnozhye" d="{pod_d}" transform="{pod_tf}"/>
    <path id="pidana" d="{pidana_d}" transform="{pid_tf}"/>
  </g>
</svg>
"""
        path.write_text(svg, encoding="utf-8")

    write_svg(OUT_SVG, FILL)
    write_svg(OUT_SVG_BLACK, "#000000")
    print(f"SVG {OUT_SVG.name}: {phys_w:.1f}x{phys_h:.1f} mm")
    print(f"SVG {OUT_SVG_BLACK.name} (black)")

    # Preview on brand sage
    scale = 14.0
    W, H = int(vb_w * scale), int(vb_h * scale)
    im = Image.new("RGB", (W, H), "#C5C9A8")
    draw = ImageDraw.Draw(im)
    icon_draw_pil(draw, icon_x, icon_y + shift_y, icon_h, FILL, scale)
    script_font = ImageFont.truetype(str(script_path), int(pod_size * scale))
    bold_font = ImageFont.truetype(str(BOLD_FONT), int(pidana_size * scale))
    draw.text(
        (pod_tx * scale, (pod_ty + shift_y) * scale),
        "подножье",
        font=script_font,
        fill=FILL,
        anchor="ls",
    )
    draw.text(
        (pidana_tx * scale, (pidana_ty + shift_y) * scale),
        "ПИДАНА",
        font=bold_font,
        fill=FILL,
        anchor="ls",
    )
    im.save(OUT_PNG)
    print(f"PNG {OUT_PNG.name} {im.size}")


if __name__ == "__main__":
    build()
