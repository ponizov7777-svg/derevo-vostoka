"""Create a pure black-and-white laser raster and SVG for layer 3 v3."""

from __future__ import annotations

import base64

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .params import LASER_DIR, PREVIEW_DIR
from .trace_layer1 import CUT_COLOR, HEIGHT_MM, _path_d, outer_contour_mm
from .trace_layer2 import _window_circle
from .trace_layer3 import PPM, _ring_mask


SOURCE = LASER_DIR / "слой3_декор_v3_гравировка.png"
BW_PNG = LASER_DIR / "слой3_декор_v3_чб.png"
SVG_OUT = LASER_DIR / "слой3_декор_v3_чб.svg"
PREVIEW_OUT = PREVIEW_DIR / "слой3_декор_v3_чб.png"


def _to_laser_bw(gray: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """Remove plywood tone, then dither remaining engraving to 1 bit."""
    black_point = 25.0
    wood_white = 205.0
    normalized = np.clip(
        (gray.astype(np.float32) - black_point)
        * (255.0 / (wood_white - black_point)),
        0,
        255,
    ).astype(np.uint8)
    normalized[gray >= wood_white] = 255
    normalized[ring == 0] = 255

    bw = np.array(
        Image.fromarray(normalized)
        .convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        .convert("L")
    )
    bw[ring == 0] = 255
    return bw


def main() -> None:
    pts_mm, svg_w, svg_h = outer_contour_mm(height_mm=HEIGHT_MM)
    cx, cy, radius = _window_circle(pts_mm, svg_w, svg_h)
    ring = _ring_mask(svg_w, svg_h, pts_mm, cx, cy, radius)

    gray = np.array(Image.open(SOURCE).convert("L"))
    bw = _to_laser_bw(gray, ring)
    Image.fromarray(bw).save(BW_PNG)

    b64 = base64.b64encode(BW_PNG.read_bytes()).decode("ascii")
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{svg_w:.3f}mm" height="{svg_h:.3f}mm"
     viewBox="0 0 {svg_w:.3f} {svg_h:.3f}">
  <title>слой3_декор_v3_чб</title>
  <desc>Pure black-and-white raster engraving with exact layer-3 CUT.</desc>
  <g id="ENGRAVE">
    <image x="0" y="0" width="{svg_w:.3f}" height="{svg_h:.3f}"
           preserveAspectRatio="none"
           xlink:href="data:image/png;base64,{b64}"/>
  </g>
  <g id="CUT" fill="none" stroke="{CUT_COLOR}" stroke-width="0.1"
     vector-effect="non-scaling-stroke">
    <path id="outer" d="{_path_d(pts_mm)}"/>
    <circle id="window" cx="{cx:.3f}" cy="{cy:.3f}" r="{radius:.3f}"/>
  </g>
</svg>
"""
    SVG_OUT.write_text(svg, encoding="utf-8")

    preview = Image.fromarray(cv2.cvtColor(bw, cv2.COLOR_GRAY2RGB))
    draw = ImageDraw.Draw(preview)
    inset = cv2.erode(
        ring,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
    )
    contours, _ = cv2.findContours(
        inset, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for contour in contours:
        points = [tuple(int(v) for v in point[0]) for point in contour]
        if len(points) > 2:
            draw.line(points + [points[0]], fill=(220, 0, 0), width=3)
    draw.ellipse(
        [
            (cx - radius) * PPM + 3,
            (cy - radius) * PPM + 3,
            (cx + radius) * PPM - 3,
            (cy + radius) * PPM - 3,
        ],
        outline=(220, 0, 0),
        width=3,
    )
    preview.save(PREVIEW_OUT)

    values = np.unique(bw)
    print(f"{BW_PNG.as_posix()}: values={values.tolist()}")
    print(f"{SVG_OUT.as_posix()}: {svg_w:.2f} x {svg_h:.2f} mm")
    print(f"preview: {PREVIEW_OUT.as_posix()}")


if __name__ == "__main__":
    main()
