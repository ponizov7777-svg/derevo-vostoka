#!/usr/bin/env python3
"""Convert laser PNG art into SVG cut contours (keychains or magnet silhouettes).

Examples:
  # Keychain with top hole + engrave
  python scripts/png_to_laser_svg.py images/мотивация/foo.png

  # Magnet outer silhouette only (next to each PNG)
  python scripts/png_to_laser_svg.py --no-hole --cut-only --beside images/лазер-магниты
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

PHYSICAL_HEIGHT_MM = 70.0
MARGIN_PX = 8


def contour_to_path(pts: np.ndarray, vx: float, vy: float) -> str:
    coords = [f"{x - vx:.2f},{y - vy:.2f}" for x, y in pts]
    return "M " + " L ".join(coords) + " Z"


def detect_outer_contour(black: np.ndarray) -> np.ndarray:
    h, w = black.shape
    contours, _ = cv2.findContours(black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    candidates = [
        c
        for c in contours
        if cv2.boundingRect(c)[2] > w * 0.35 and cv2.boundingRect(c)[3] > h * 0.55
    ]
    if not candidates:
        raise RuntimeError("Outer contour was not detected")
    outer = max(candidates, key=cv2.contourArea)
    return cv2.approxPolyDP(outer, 1.0, True)


def detect_silhouette_contour(arr: np.ndarray, bg_threshold: int = 245) -> np.ndarray:
    """Outer cut path for sticker/magnet art on a near-white background.

    Flood-fills from image corners to isolate the background, then takes the
    largest external contour of everything that is not background. This follows
    the thin black outline + white border silhouette, not internal fills.
    """
    h, w = arr.shape
    # Near-white pixels are flood-fill eligible; artwork blocks the fill.
    bg_mask = np.zeros((h + 2, w + 2), np.uint8)
    flood_src = (arr >= bg_threshold).astype(np.uint8) * 255
    # Seed from corners (and mid-edges) so irregular canvases still fill.
    seeds = [
        (0, 0),
        (w - 1, 0),
        (0, h - 1),
        (w - 1, h - 1),
        (w // 2, 0),
        (w // 2, h - 1),
        (0, h // 2),
        (w - 1, h // 2),
    ]
    for x, y in seeds:
        if flood_src[y, x] < 128:
            continue
        cv2.floodFill(flood_src, bg_mask, (x, y), 128, loDiff=0, upDiff=0, flags=4)

    background = flood_src == 128
    content = (~background).astype(np.uint8) * 255
    # Close tiny antialias gaps in the outer stroke.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(content, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise RuntimeError("Silhouette contour was not detected")
    candidates = [
        c
        for c in contours
        if cv2.contourArea(c) > (h * w) * 0.05
        and cv2.boundingRect(c)[2] > w * 0.25
        and cv2.boundingRect(c)[3] > h * 0.25
    ]
    if not candidates:
        candidates = list(contours)
    outer = max(candidates, key=cv2.contourArea)
    return cv2.approxPolyDP(outer, 1.2, True)


def detect_hole(arr: np.ndarray) -> tuple[float, float, float]:
    h, w = arr.shape
    min_dim = min(h, w)
    min_size = max(25.0, min_dim * 0.018)
    max_size = min_dim * 0.12
    min_area = max(500.0, min_size * min_size * 0.35)
    white = (arr >= 128).astype(np.uint8) * 255
    num, _labels, stats, centers = cv2.connectedComponentsWithStats(white, 8)
    hole_candidates = []
    for i in range(1, num):
        x, y, cw, ch, area = stats[i]
        if y >= h * 0.22:
            continue
        if not (min_size < cw < max_size and min_size < ch < max_size):
            continue
        ratio = cw / ch
        if 0.75 < ratio < 1.25 and area > min_area:
            # Prefer holes near horizontal center of the top lug.
            cx = centers[i][0]
            center_score = abs(cx - w / 2) / w
            hole_candidates.append((i, area, center_score))
    if not hole_candidates:
        raise RuntimeError("Top hole was not detected")
    hole_candidates.sort(key=lambda item: (item[2], -item[1]))
    hole_label = hole_candidates[0][0]
    hx, hy = centers[hole_label]
    _, _, hw, hh, _ = stats[hole_label]
    hr = (hw + hh) / 4.0
    return float(hx), float(hy), float(hr)


def build_engrave_path(black: np.ndarray, vx: float, vy: float) -> str:
    contours, _ = cv2.findContours(black, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    parts: list[str] = []
    for contour in contours:
        if cv2.contourArea(contour) < 2:
            continue
        contour = cv2.approxPolyDP(contour, 0.65, True)
        pts = contour[:, 0, :]
        if len(pts) < 3:
            continue
        parts.append(contour_to_path(pts, vx, vy))
    if not parts:
        raise RuntimeError("No engraving contours found")
    return " ".join(parts)


def convert_one(
    src: Path,
    dst: Path,
    physical_height_mm: float = PHYSICAL_HEIGHT_MM,
    *,
    cut_only: bool = False,
    no_hole: bool = False,
) -> dict:
    arr = np.array(Image.open(src).convert("L"))
    black = (arr < 128).astype(np.uint8) * 255

    if no_hole:
        outer = detect_silhouette_contour(arr)
    else:
        outer = detect_outer_contour(black)
    ox, oy, ow, oh = cv2.boundingRect(outer)

    hx = hy = hr = 0.0
    if not no_hole:
        hx, hy, hr = detect_hole(arr)

    vx, vy = ox - MARGIN_PX, oy - MARGIN_PX
    vw, vh = ow + MARGIN_PX * 2, oh + MARGIN_PX * 2
    physical_w = physical_height_mm * vw / vh
    scale = physical_height_mm / vh

    outer_d = contour_to_path(outer[:, 0, :], vx, vy)
    stroke_w = 0.10 / scale

    title = src.stem.replace("_", " ")
    engrave_layer = ""
    if no_hole:
        description = "Red CUT layer: outer silhouette (magnet, no hole)."
    else:
        description = "Red CUT layer: outer profile and hole."
    if not cut_only:
        engrave_d = build_engrave_path(black, vx, vy)
        description += " Black ENGRAVE layer: engraving."
        engrave_layer = f"""  <g id="ENGRAVE" inkscape:groupmode="layer" inkscape:label="ENGRAVE"
     fill="#000000" stroke="none" fill-rule="evenodd">
    <path d="{engrave_d}"/>
  </g>
"""

    hole_svg = ""
    if not no_hole:
        hole_svg = (
            f'\n    <circle id="hole-cut" cx="{hx - vx:.3f}" '
            f'cy="{hy - vy:.3f}" r="{hr:.3f}"/>'
        )

    svg = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="{physical_w:.3f}mm" height="{physical_height_mm:.3f}mm"
     viewBox="0 0 {vw} {vh}" style="background:#ffffff">
  <title>{title}</title>
  <desc>{description}</desc>
{engrave_layer}\
  <g id="CUT" inkscape:groupmode="layer" inkscape:label="CUT"
     fill="none" stroke="#ff0000" stroke-width="{stroke_w:.3f}"
     vector-effect="non-scaling-stroke">
    <path id="outer-cut" d="{outer_d}"/>{hole_svg}
  </g>
</svg>
"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(svg, encoding="utf-8")

    info = {
        "src": src.name,
        "dst": dst.as_posix(),
        "size_mm": (physical_w, physical_height_mm),
        "outer_points": len(outer[:, 0, :]),
        "no_hole": no_hole,
    }
    if not no_hole:
        info["hole_mm"] = 2 * hr * scale
        info["top_material_mm"] = (hy - hr - oy) * scale
    return info


def collect_pngs(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for src in inputs:
        if src.is_file() and src.suffix.lower() == ".png":
            files.append(src)
        elif src.is_dir():
            files.extend(sorted(p for p in src.rglob("*.png") if p.is_file()))
        else:
            raise SystemExit(f"Not found: {src}")
    # Stable unique order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in files:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="PNG files or directories to convert",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for SVG output (default: next to each PNG, or images/мотивация/векторы)",
    )
    parser.add_argument(
        "--beside",
        action="store_true",
        help="Write each SVG next to its PNG (same folder, same stem)",
    )
    parser.add_argument(
        "--height-mm",
        type=float,
        default=PHYSICAL_HEIGHT_MM,
        help="Physical height of each piece in millimeters",
    )
    parser.add_argument(
        "--cut-only",
        action="store_true",
        help="Export only the CUT layer (no ENGRAVE fill)",
    )
    parser.add_argument(
        "--no-hole",
        action="store_true",
        help="Outer silhouette only — for magnets without a hanging hole",
    )
    args = parser.parse_args()

    files = collect_pngs(args.inputs)
    if not files:
        raise SystemExit("No PNG files found")

    default_out = Path("images/мотивация/векторы")
    ok = fail = 0
    for src in files:
        if args.beside or (args.output_dir is None and args.no_hole):
            dst = src.with_suffix(".svg")
        elif args.output_dir is not None:
            dst = args.output_dir / f"{src.stem}.svg"
        else:
            dst = default_out / f"{src.stem}.svg"
        try:
            info = convert_one(
                src,
                dst,
                physical_height_mm=args.height_mm,
                cut_only=args.cut_only,
                no_hole=args.no_hole,
            )
        except Exception as exc:  # noqa: BLE001 — batch report
            fail += 1
            print(f"FAIL {src}: {exc}")
            continue
        ok += 1
        w, h = info["size_mm"]
        extra = (
            f"silhouette, outer pts {info['outer_points']}"
            if info.get("no_hole")
            else (
                f"hole {info['hole_mm']:.2f} mm, "
                f"top ring {info['top_material_mm']:.2f} mm, "
                f"outer pts {info['outer_points']}"
            )
        )
        print(f"{info['src']} -> {dst}: {w:.2f}x{h:.2f} mm, {extra}")

    print(f"Done: {ok} ok, {fail} failed, {len(files)} total")
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
