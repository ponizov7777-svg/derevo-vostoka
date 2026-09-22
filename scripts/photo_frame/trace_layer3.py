"""Layer 3: same CUT as layer 2 + decorative ENGRAVE on the wood ring."""

from __future__ import annotations

import base64
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .params import LASER_DIR, PREVIEW_DIR, PROJECT_ROOT
from .trace_layer1 import (
    CUT_COLOR,
    HEIGHT_MM,
    _path_d,
    outer_contour_mm,
)
from .trace_layer2 import _window_circle

ART_SRC = (
    PROJECT_ROOT
    / "images"
    / "рамки"
    / "10x15"
    / "референсы"
    / "рамка_10x15_слой3_декор.png"
)
SVG_OUT = LASER_DIR / "слой3_декор.svg"
ENGRAVE_PNG = LASER_DIR / "слой3_декор_гравировка.png"
PREVIEW_OUT = PREVIEW_DIR / "слой3_декор.png"
PPM = 10.0  # px/mm for engrave raster


def _ring_mask(svg_w: float, svg_h: float, outer_mm: np.ndarray, cx: float, cy: float, radius: float) -> np.ndarray:
    h, w = int(round(svg_h * PPM)), int(round(svg_w * PPM))
    mask = np.zeros((h, w), np.uint8)
    cv2.fillPoly(mask, [np.round(outer_mm * PPM).astype(np.int32)], 255)
    cv2.circle(mask, (int(round(cx * PPM)), int(round(cy * PPM))), int(round(radius * PPM)), 0, -1)
    return mask


def _largest_inner_circle(gray: np.ndarray) -> tuple[float, float, float]:
    white = (gray > 245).astype(np.uint8) * 255
    contours, _ = cv2.findContours(white, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    h, w = gray.shape
    best = None
    best_score = 0.0
    for c in contours:
        area = cv2.contourArea(c)
        if area < (h * w) * 0.08:
            continue
        (cx, cy), r = cv2.minEnclosingCircle(c)
        if r < min(h, w) * 0.18:
            continue
        circ = area / (np.pi * r * r + 1e-6)
        if circ < 0.75:
            continue
        score = area * circ
        if score > best_score:
            best_score = score
            best = (float(cx), float(cy), float(r))
    if best is None:
        raise RuntimeError("Could not find the photo window in the decoration artwork")
    return best


def _align_art(art_bgr: np.ndarray, cx: float, cy: float, radius: float, svg_w: float, svg_h: float) -> np.ndarray:
    h, w = int(round(svg_h * PPM)), int(round(svg_w * PPM))
    gray = cv2.cvtColor(art_bgr, cv2.COLOR_BGR2GRAY)
    gx, gy, gr = _largest_inner_circle(gray)
    scale = (radius * PPM) / gr
    M = np.array(
        [
            [scale, 0.0, cx * PPM - scale * gx],
            [0.0, scale, cy * PPM - scale * gy],
        ],
        dtype=np.float32,
    )
    aligned = cv2.warpAffine(
        art_bgr,
        M,
        (w, h),
        flags=cv2.INTER_AREA,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    return aligned


def _ray_outer_radius(mask: np.ndarray, cx: float, cy: float, n_ang: int = 1440) -> np.ndarray:
    """Max radius of a binary mask along each angle around (cx, cy), in pixels."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise RuntimeError("Empty mask for ray radius")
    dx = xs.astype(np.float64) - cx
    dy = ys.astype(np.float64) - cy
    ang = np.arctan2(dy, dx)
    rr = np.hypot(dx, dy)
    bins = np.clip(((ang + np.pi) / (2 * np.pi) * n_ang).astype(np.int32), 0, n_ang - 1)
    radii = np.zeros(n_ang, dtype=np.float64)
    np.maximum.at(radii, bins, rr)
    good = np.where(radii > 0)[0]
    if good.size == 0:
        raise RuntimeError("No rays with content")
    xp = np.concatenate([good - n_ang, good, good + n_ang]).astype(np.float64)
    fp = np.concatenate([radii[good], radii[good], radii[good]])
    filled = np.interp(np.arange(n_ang, dtype=np.float64), xp, fp)
    pad = np.concatenate([filled[-5:], filled, filled[:5]])
    return np.convolve(pad, np.ones(11) / 11.0, mode="valid")


def _polar_match_outer(
    aligned_bgr: np.ndarray,
    outer_mm: np.ndarray,
    cx_mm: float,
    cy_mm: float,
    win_r_mm: float,
    svg_w: float,
    svg_h: float,
) -> np.ndarray:
    """Stretch the window-aligned art so its outer edge meets the CUT contour."""
    h, w = int(round(svg_h * PPM)), int(round(svg_w * PPM))
    cx = cx_mm * PPM
    cy = cy_mm * PPM
    win_r = win_r_mm * PPM

    target = np.zeros((h, w), np.uint8)
    cv2.fillPoly(target, [np.round(outer_mm * PPM).astype(np.int32)], 255)

    gray = cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2GRAY)
    art_mask = (gray < 250).astype(np.uint8) * 255

    n_ang = 1440
    r_tgt = _ray_outer_radius(target, cx, cy, n_ang)
    r_art = _ray_outer_radius(art_mask, cx, cy, n_ang)
    r_tgt = np.maximum(r_tgt, win_r + 2.0)
    r_art = np.maximum(r_art, win_r + 2.0)

    yy, xx = np.indices((h, w), dtype=np.float32)
    dx = xx - cx
    dy = yy - cy
    ang = np.arctan2(dy, dx)
    r = np.hypot(dx, dy)
    bins = np.clip(((ang + np.pi) / (2 * np.pi) * n_ang).astype(np.int32), 0, n_ang - 1)
    rt = r_tgt[bins].astype(np.float32)
    ra = r_art[bins].astype(np.float32)
    # Keep the photo hole; map the ring [win_r, r_tgt] onto [win_r, r_art].
    span_t = np.maximum(rt - win_r, 1.0)
    span_a = np.maximum(ra - win_r, 1.0)
    r_src = win_r + (r - win_r) * (span_a / span_t)
    inside_hole = r <= win_r
    r_src = np.where(inside_hole, r, r_src)

    map_x = (cx + r_src * np.cos(ang)).astype(np.float32)
    map_y = (cy + r_src * np.sin(ang)).astype(np.float32)
    warped = cv2.remap(
        aligned_bgr,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    warped[target == 0] = (255, 255, 255)
    hole = np.zeros((h, w), np.uint8)
    cv2.circle(hole, (int(round(cx)), int(round(cy))), int(round(win_r)), 255, -1)
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    need = (target > 0) & (hole == 0)
    wood = need & (gray < 200)
    unknown = need & (gray > 230)
    if np.any(unknown) and np.any(wood):
        from scipy.ndimage import distance_transform_edt

        _, inds = distance_transform_edt(~wood, return_indices=True)
        warped[unknown] = warped[inds[0][unknown], inds[1][unknown]]
    warped[target == 0] = (255, 255, 255)
    warped[hole > 0] = (255, 255, 255)
    return warped


def _fill_to_outer_without_warp(
    aligned_bgr: np.ndarray,
    outer_mm: np.ndarray,
    cx_mm: float,
    cy_mm: float,
    win_r_mm: float,
    svg_w: float,
    svg_h: float,
) -> np.ndarray:
    """Clip to the exact CUT and extend only pale wood into uncovered margins."""
    h, w = int(round(svg_h * PPM)), int(round(svg_w * PPM))
    target = np.zeros((h, w), np.uint8)
    cv2.fillPoly(target, [np.round(outer_mm * PPM).astype(np.int32)], 255)
    hole = np.zeros((h, w), np.uint8)
    cv2.circle(
        hole,
        (int(round(cx_mm * PPM)), int(round(cy_mm * PPM))),
        int(round(win_r_mm * PPM)),
        255,
        -1,
    )

    result = aligned_bgr.copy()
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    wood_area = (target > 0) & (hole == 0)
    uncovered = wood_area & (gray > 250)
    # Use only light plywood pixels as donors so engraved outlines and letters
    # cannot smear into the added edge.
    pale_wood = wood_area & (gray >= 165) & (gray <= 238)
    if np.any(uncovered) and np.any(pale_wood):
        # A flat median plywood tone is deliberate here. Nearest-pixel
        # extension creates long radial streaks in wide ribbon protrusions.
        wood_tone = np.median(result[pale_wood], axis=0).astype(np.uint8)
        result[uncovered] = wood_tone

    result[target == 0] = (255, 255, 255)
    result[hole > 0] = (255, 255, 255)
    return result


def _engrave_gray(aligned_bgr: np.ndarray, ring: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2GRAY)
    out = np.full(gray.shape, 255, np.uint8)
    out[ring > 0] = gray[ring > 0]
    return out


def export_layer3(
    art_path: Path = ART_SRC,
    svg_path: Path = SVG_OUT,
    engrave_path: Path = ENGRAVE_PNG,
    preview_path: Path = PREVIEW_OUT,
    height_mm: float = HEIGHT_MM,
    match_outer: bool = True,
) -> dict:
    pts_mm, svg_w, svg_h = outer_contour_mm(height_mm=height_mm)
    cx, cy, radius = _window_circle(pts_mm, svg_w, svg_h)
    art_rgb = np.array(Image.open(art_path).convert("RGB"))
    art = cv2.cvtColor(art_rgb, cv2.COLOR_RGB2BGR)
    aligned = _align_art(art, cx, cy, radius, svg_w, svg_h)
    if match_outer:
        aligned = _polar_match_outer(aligned, pts_mm, cx, cy, radius, svg_w, svg_h)
    else:
        aligned = _fill_to_outer_without_warp(
            aligned, pts_mm, cx, cy, radius, svg_w, svg_h
        )
    ring = _ring_mask(svg_w, svg_h, pts_mm, cx, cy, radius)
    engrave = _engrave_gray(aligned, ring)
    engrave_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(engrave).save(engrave_path)

    png_bytes = Path(engrave_path).read_bytes()
    b64 = base64.b64encode(png_bytes).decode("ascii")
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{svg_w:.3f}mm" height="{svg_h:.3f}mm"
     viewBox="0 0 {svg_w:.3f} {svg_h:.3f}">
  <title>слой3_декор</title>
  <desc>Layer 3: decorative ENGRAVE on the wood ring. CUT matches layer 2 (outer + window).</desc>
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
    svg_path.write_text(svg, encoding="utf-8")

    rgb = cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB)
    rgb[ring == 0] = (255, 255, 255)
    prev = Image.fromarray(rgb)
    draw = ImageDraw.Draw(prev)
    # Inset the overlay so the red stroke sits on the wood, not outside the art.
    inset = np.zeros(ring.shape, np.uint8)
    inset[ring > 0] = 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    inset = cv2.erode(inset, k)
    contours, _ = cv2.findContours(inset, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        pts = [tuple(int(v) for v in p[0]) for p in cnt]
        if len(pts) > 2:
            draw.line(pts + [pts[0]], fill=(220, 0, 0), width=3)
    win_box = [
        (cx - radius) * PPM + 3,
        (cy - radius) * PPM + 3,
        (cx + radius) * PPM - 3,
        (cy + radius) * PPM - 3,
    ]
    draw.ellipse(win_box, outline=(220, 0, 0), width=3)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    prev.save(preview_path)

    return {
        "svg": svg_path.as_posix(),
        "engrave": engrave_path.as_posix(),
        "preview": preview_path.as_posix(),
        "size_mm": (round(svg_w, 2), round(svg_h, 2)),
        "window_d_mm": round(2 * radius, 2),
        "engrave_px": engrave.shape[1::-1],
    }


def main() -> None:
    info = export_layer3()
    w, h = info["size_mm"]
    print(f"{info['svg']}: {w} x {h} mm, window Ø{info['window_d_mm']} mm")
    print(f"engrave: {info['engrave']} {info['engrave_px']}")
    print(f"preview: {info['preview']}")


if __name__ == "__main__":
    main()
