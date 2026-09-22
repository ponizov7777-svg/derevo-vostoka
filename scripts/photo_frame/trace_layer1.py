"""Trace layer-1 outer CUT contour from a filled silhouette PNG."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .params import LASER_DIR, PREVIEW_DIR, PROJECT_ROOT

CUT_COLOR = "#ff0000"
SILHOUETTE = (
    PROJECT_ROOT
    / "images"
    / "рамки"
    / "10x15"
    / "референсы"
    / "рамка_10x15_слой1_силуэт.png"
)
SVG_OUT = LASER_DIR / "слой1_контур.svg"
PREVIEW_OUT = PREVIEW_DIR / "слой1_контур.png"
# Outer bounding-box height of the whole souvenir (crest + oval + ribbon).
HEIGHT_MM = 210.0
MARGIN_MM = 2.0


def _filled_mask(path: Path) -> np.ndarray:
    arr = np.array(Image.open(path).convert("L"))
    binary = (arr < 128).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    h, w = binary.shape
    flood = binary.copy()
    ff_mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, ff_mask, (0, 0), 128)
    holes = (flood == 0).astype(np.uint8) * 255
    filled = cv2.bitwise_or(binary, holes)
    blur = cv2.GaussianBlur(filled, (11, 11), 0)
    return (blur > 127).astype(np.uint8) * 255


def _outer_poly(mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise RuntimeError("No outer contour")
    outer = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(outer, True)
    approx = cv2.approxPolyDP(outer, 0.00035 * peri, True)
    return approx[:, 0, :].astype(np.float64)


def _to_mm(pts: np.ndarray, height_mm: float) -> tuple[np.ndarray, float, float]:
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    h_px = y1 - y0
    scale = height_mm / h_px
    mm = np.empty_like(pts)
    mm[:, 0] = (pts[:, 0] - x0) * scale + MARGIN_MM
    mm[:, 1] = (pts[:, 1] - y0) * scale + MARGIN_MM
    width_mm = (x1 - x0) * scale
    return mm, width_mm + 2 * MARGIN_MM, height_mm + 2 * MARGIN_MM


def _path_d(pts: np.ndarray) -> str:
    parts = [f"M {pts[0, 0]:.3f},{pts[0, 1]:.3f}"]
    parts.extend(f"L {x:.3f},{y:.3f}" for x, y in pts[1:])
    parts.append("Z")
    return " ".join(parts)


def outer_contour_mm(
    src: Path = SILHOUETTE,
    height_mm: float = HEIGHT_MM,
) -> tuple[np.ndarray, float, float]:
    mask = _filled_mask(src)
    pts_px = _outer_poly(mask)
    return _to_mm(pts_px, height_mm)


def export_layer1(
    src: Path = SILHOUETTE,
    svg_path: Path = SVG_OUT,
    preview_path: Path = PREVIEW_OUT,
    height_mm: float = HEIGHT_MM,
) -> dict:
    pts_mm, svg_w, svg_h = outer_contour_mm(src, height_mm)
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w:.3f}mm" height="{svg_h:.3f}mm"
     viewBox="0 0 {svg_w:.3f} {svg_h:.3f}">
  <title>слой1_контур</title>
  <desc>Layer 1: single outer CUT contour of the whole piece. No window, no engrave.</desc>
  <g id="CUT" fill="none" stroke="{CUT_COLOR}" stroke-width="0.1"
     vector-effect="non-scaling-stroke">
    <path id="outer" d="{_path_d(pts_mm)}"/>
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
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(preview_path)

    return {
        "svg": svg_path.as_posix(),
        "preview": preview_path.as_posix(),
        "size_mm": (round(svg_w, 2), round(svg_h, 2)),
        "points": int(len(pts_mm)),
    }


def main() -> None:
    info = export_layer1()
    w, h = info["size_mm"]
    print(f"{info['svg']}: {w} x {h} mm, {info['points']} pts")
    print(f"preview: {info['preview']}")


if __name__ == "__main__":
    main()
