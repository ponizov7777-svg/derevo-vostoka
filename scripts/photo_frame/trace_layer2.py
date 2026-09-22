"""Layer 2: same outer CUT as layer 1 + inner photo window."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .params import LASER_DIR, PREVIEW_DIR
from .trace_layer1 import (
    CUT_COLOR,
    HEIGHT_MM,
    MARGIN_MM,
    _path_d,
    outer_contour_mm,
)

SVG_OUT = LASER_DIR / "слой2_окно.svg"
PREVIEW_OUT = PREVIEW_DIR / "слой2_окно.png"
# Minimum wood between window and outer edge (oval body).
RIM_MM = 12.0
# Crest / ribbon stay solid: search inscribed circle only in the oval body.
BODY_Y0_MM = 80.0
BODY_Y1_MM = 178.0


def _window_circle(outer_mm: np.ndarray, svg_w: float, svg_h: float) -> tuple[float, float, float]:
    ppm = 8.0
    h = int(round(svg_h * ppm))
    w = int(round(svg_w * ppm))
    canvas = np.zeros((h, w), np.uint8)
    cv2.fillPoly(canvas, [np.round(outer_mm * ppm).astype(np.int32)], 255)
    dist = cv2.distanceTransform(canvas, cv2.DIST_L2, 5)
    y0 = max(0, int(BODY_Y0_MM * ppm))
    y1 = min(h, int(BODY_Y1_MM * ppm))
    roi = dist.copy()
    roi[:y0] = 0
    roi[y1:] = 0
    cy, cx = np.unravel_index(int(roi.argmax()), roi.shape)
    r_inscribed = float(roi[cy, cx]) / ppm
    radius = r_inscribed - RIM_MM
    if radius < 20:
        raise RuntimeError(f"Photo window too small: r={radius:.1f} mm")
    return cx / ppm, cy / ppm, radius


def export_layer2(
    svg_path: Path = SVG_OUT,
    preview_path: Path = PREVIEW_OUT,
    height_mm: float = HEIGHT_MM,
    src=None,
    window: tuple[float, float, float] | None = None,
) -> dict:
    pts_mm, svg_w, svg_h = outer_contour_mm(src=src, height_mm=height_mm) if src is not None else outer_contour_mm(height_mm=height_mm)
    if window is None:
        cx, cy, radius = _window_circle(pts_mm, svg_w, svg_h)
    else:
        cx, cy, radius = window
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w:.3f}mm" height="{svg_h:.3f}mm"
     viewBox="0 0 {svg_w:.3f} {svg_h:.3f}">
  <title>слой2_окно</title>
  <desc>Layer 2: same outer CUT as layer 1 plus inner circular photo window.
Outer matches слой1_контур.svg. Window diameter {2 * radius:.1f} mm, rim {RIM_MM:.0f} mm.</desc>
  <g id="CUT" fill="none" stroke="{CUT_COLOR}" stroke-width="0.1"
     vector-effect="non-scaling-stroke">
    <path id="outer" d="{_path_d(pts_mm)}"/>
    <circle id="window" cx="{cx:.3f}" cy="{cy:.3f}" r="{radius:.3f}"/>
  </g>
</svg>
"""
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(svg, encoding="utf-8")

    ppm = 4.0
    img = Image.new("RGB", (int(svg_w * ppm), int(svg_h * ppm)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    xy = [(float(x * ppm), float(y * ppm)) for x, y in pts_mm]
    draw.line(xy + [xy[0]], fill=(220, 0, 0), width=3)
    box = [
        (cx - radius) * ppm,
        (cy - radius) * ppm,
        (cx + radius) * ppm,
        (cy + radius) * ppm,
    ]
    draw.ellipse(box, outline=(220, 0, 0), width=3)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(preview_path)

    return {
        "svg": svg_path.as_posix(),
        "preview": preview_path.as_posix(),
        "size_mm": (round(svg_w, 2), round(svg_h, 2)),
        "window_d_mm": round(2 * radius, 2),
        "window_center_mm": (round(cx, 2), round(cy, 2)),
        "rim_mm": RIM_MM,
        "margin_mm": MARGIN_MM,
    }


def main() -> None:
    info = export_layer2()
    w, h = info["size_mm"]
    print(
        f"{info['svg']}: {w} x {h} mm, window Ø{info['window_d_mm']} mm "
        f"at {info['window_center_mm']}, rim {info['rim_mm']} mm"
    )
    print(f"preview: {info['preview']}")


if __name__ == "__main__":
    main()
