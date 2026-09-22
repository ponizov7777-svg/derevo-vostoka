"""SVG export for laser CUT/ENGRAVE layers (mm units)."""

from __future__ import annotations

import json
from pathlib import Path

from .geometry import Part, Poly, bbox, shift_part_to_origin, skeleton_parts
from .ornament import apply_ornament, outer_silhouette
from .params import DEFAULT, FrameParams, LASER_DIR, OUT_DIR, PREVIEW_DIR


CUT_COLOR = "#ff0000"
ENGRAVE_COLOR = "#000000"


def poly_to_path(poly: Poly) -> str:
    if not poly:
        return ""
    parts = [f"M {poly[0][0]:.3f},{poly[0][1]:.3f}"]
    for x, y in poly[1:]:
        parts.append(f"L {x:.3f},{y:.3f}")
    parts.append("Z")
    return " ".join(parts)


def part_svg(part: Part, stroke: float = 0.1) -> str:
    p = shift_part_to_origin(part, margin=2.0)
    all_pts = p.outer + [pt for h in p.holes for pt in h] + [pt for e in p.engraves for pt in e]
    if not all_pts:
        w = h = 10.0
    else:
        x0, y0, x1, y1 = bbox(all_pts)
        w, h = x1 - x0 + 4.0, y1 - y0 + 4.0
    cut_paths = [poly_to_path(p.outer)] + [poly_to_path(h) for h in p.holes]
    eng_paths = [poly_to_path(e) for e in p.engraves]
    cut_g = "\n".join(
        f'    <path d="{d}" fill="none" stroke="{CUT_COLOR}" '
        f'stroke-width="{stroke}" vector-effect="non-scaling-stroke"/>'
        for d in cut_paths
        if d
    )
    eng_g = ""
    if eng_paths:
        eng_g = "\n".join(
            f'    <path d="{d}" fill="none" stroke="{ENGRAVE_COLOR}" '
            f'stroke-width="{stroke}" vector-effect="non-scaling-stroke"/>'
            for d in eng_paths
            if d
        )
        eng_g = f'  <g id="ENGRAVE">\n{eng_g}\n  </g>\n'
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}mm" height="{h:.3f}mm"
     viewBox="0 0 {w:.3f} {h:.3f}">
  <title>{part.name}</title>
  <g id="CUT">
{cut_g}
  </g>
{eng_g}</svg>
"""


def nest_parts(parts: list[Part], sheet_w: float = 400.0, gap: float = 4.0) -> tuple[str, list[dict]]:
    """Simple left-to-right, wrap nesting for a cutting sheet."""
    placed: list[tuple[Part, float, float]] = []
    meta: list[dict] = []
    x = gap
    y = gap
    row_h = 0.0
    max_x = sheet_w
    max_y = gap

    for part in parts:
        sp = shift_part_to_origin(part, margin=0.0)
        x0, y0, x1, y1 = bbox(sp.outer + [pt for h in sp.holes for pt in h])
        pw, ph = x1 - x0, y1 - y0
        if x + pw + gap > max_x and x > gap:
            x = gap
            y += row_h + gap
            row_h = 0.0
        dx, dy = x - x0, y - y0
        placed.append((sp, dx, dy))
        meta.append({"name": part.name, "x": x, "y": y, "w": pw, "h": ph})
        x += pw + gap
        row_h = max(row_h, ph)
        max_y = max(max_y, y + ph)

    sheet_h = max_y + gap
    paths: list[str] = []
    for sp, dx, dy in placed:
        for poly in [sp.outer, *sp.holes]:
            shifted = [(px + dx, py + dy) for px, py in poly]
            d = poly_to_path(shifted)
            paths.append(
                f'    <path d="{d}" fill="none" stroke="{CUT_COLOR}" '
                f'stroke-width="0.1" vector-effect="non-scaling-stroke"/>'
            )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_w:.3f}mm" height="{sheet_h:.3f}mm"
     viewBox="0 0 {sheet_w:.3f} {sheet_h:.3f}">
  <title>photo_frame_10x15_nested</title>
  <g id="CUT">
{chr(10).join(paths)}
  </g>
</svg>
"""
    return svg, meta


def build_all_parts(p: FrameParams | None = None) -> list[Part]:
    p = p or DEFAULT
    sil = outer_silhouette(p)
    parts = skeleton_parts(p, sil)
    # Replace front/mask with ornamented versions; back reuses the exact same outer
    front, mask = apply_ornament(parts[0], parts[1], p)
    result: list[Part] = [front, mask]
    for pt in parts[2:]:
        if pt.name == "back":
            result.append(
                Part(
                    name="back",
                    outer=list(front.outer),
                    holes=pt.holes,
                    engraves=pt.engraves,
                )
            )
        else:
            result.append(pt)
    return result


def export_all(p: FrameParams | None = None) -> dict:
    p = p or DEFAULT
    LASER_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    parts = build_all_parts(p)
    written: list[str] = []
    for part in parts:
        path = LASER_DIR / f"{part.name}.svg"
        path.write_text(part_svg(part, stroke=p.stroke_cut), encoding="utf-8")
        written.append(path.as_posix())

    nested_svg, nest_meta = nest_parts(parts)
    nested_path = LASER_DIR / "лист_раскладка.svg"
    nested_path.write_text(nested_svg, encoding="utf-8")
    written.append(nested_path.as_posix())

    params_path = OUT_DIR / "params.json"
    params_path.write_text(json.dumps(p.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "params": p.to_dict(),
        "parts": [{"name": pt.name, "file": f"лазер/{pt.name}.svg"} for pt in parts],
        "nested": "лазер/лист_раскладка.svg",
        "nest_layout": nest_meta,
    }
    man_path = OUT_DIR / "manifest.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
