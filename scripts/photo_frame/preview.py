"""Render PNG previews: flat parts sheet, assembled stack, exploded view."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .export_svg import build_all_parts
from .geometry import Part, Poly, bbox
from .params import DEFAULT, FrameParams, PREVIEW_DIR


PPM = 4.0  # pixels per mm for previews
COLORS = {
    "front": (180, 120, 60, 230),
    "mask": (140, 95, 50, 220),
    "spacer_left": (210, 180, 120, 220),
    "spacer_right": (210, 180, 120, 220),
    "spacer_bottom": (210, 180, 120, 220),
    "back": (120, 85, 45, 230),
    "stand_leg": (160, 110, 55, 230),
    "brace": (150, 105, 50, 230),
    "brace_connector": (130, 95, 45, 230),
}


def _draw_poly(
    draw: ImageDraw.ImageDraw,
    poly: Poly,
    ox: float,
    oy: float,
    fill: tuple[int, ...] | None,
    outline: tuple[int, ...] = (40, 25, 10, 255),
    width: int = 1,
) -> None:
    if len(poly) < 3:
        return
    pts = [(ox + x * PPM, oy + y * PPM) for x, y in poly]
    draw.polygon(pts, fill=fill, outline=outline)
    if width > 1:
        draw.line(pts + [pts[0]], fill=outline, width=width)


def _draw_part(
    draw: ImageDraw.ImageDraw,
    part: Part,
    ox: float,
    oy: float,
    fill: tuple[int, ...],
) -> None:
    # Even-odd style: draw outer, then holes in light/transparent
    _draw_poly(draw, part.outer, ox, oy, fill)
    hole_fill = (248, 244, 235, 255)
    for h in part.holes:
        _draw_poly(draw, h, ox, oy, hole_fill, outline=(60, 40, 20, 255))


def preview_parts_sheet(p: FrameParams | None = None, path: Path | None = None) -> Path:
    p = p or DEFAULT
    parts = build_all_parts(p)
    # layout similar to nest
    gap = 8.0
    x = gap
    y = gap
    row_h = 0.0
    sheet_w = 420.0
    placements: list[tuple[Part, float, float]] = []
    for part in parts:
        x0, y0, x1, y1 = bbox(part.outer + [pt for h in part.holes for pt in h])
        pw, ph = x1 - x0, y1 - y0
        if x + pw + gap > sheet_w and x > gap:
            x = gap
            y += row_h + gap
            row_h = 0.0
        placements.append((part, x - x0, y - y0))
        x += pw + gap
        row_h = max(row_h, ph)
    sheet_h = y + row_h + gap
    img = Image.new("RGBA", (int(sheet_w * PPM), int(sheet_h * PPM)), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    for part, dx, dy in placements:
        _draw_part(draw, part, dx, dy, COLORS.get(part.name, (160, 120, 80, 220)))
    path = path or (PREVIEW_DIR / "детали_раскладка.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path)
    return path


def preview_assembled(p: FrameParams | None = None, path: Path | None = None) -> Path:
    """Front view of stacked front+mask (aligned)."""
    p = p or DEFAULT
    parts = {pt.name: pt for pt in build_all_parts(p)}
    front, mask = parts["front"], parts["mask"]
    all_pts = front.outer + mask.outer
    x0, y0, x1, y1 = bbox(all_pts)
    pad = 15.0
    w = x1 - x0 + 2 * pad
    h = y1 - y0 + 2 * pad
    img = Image.new("RGBA", (int(w * PPM), int(h * PPM)), (245, 240, 230, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    ox, oy = pad - x0, pad - y0
    _draw_part(draw, mask, ox, oy, COLORS["mask"])
    _draw_part(draw, front, ox, oy, COLORS["front"])
    # photo placeholder
    pw, ph = p.photo_w, p.photo_h
    photo = [
        (-pw / 2, -ph / 2),
        (pw / 2, -ph / 2),
        (pw / 2, ph / 2),
        (-pw / 2, ph / 2),
    ]
    _draw_poly(draw, photo, ox, oy, (200, 210, 220, 180), outline=(80, 90, 100, 255))
    path = path or (PREVIEW_DIR / "сборка_вид_спереди.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path)
    return path


def preview_exploded(p: FrameParams | None = None, path: Path | None = None) -> Path:
    """Simple exploded stack along Z simulated as diagonal offsets."""
    p = p or DEFAULT
    parts = {pt.name: pt for pt in build_all_parts(p)}
    order = [
        ("front", 0),
        ("mask", 1),
        ("spacer_left", 2),
        ("spacer_right", 2),
        ("spacer_bottom", 2),
        ("back", 3),
        ("stand_leg", 4),
        ("brace", 5),
    ]
    # gather bbox
    xs: list[float] = []
    ys: list[float] = []
    for name, layer in order:
        part = parts[name]
        dx = layer * 18.0
        dy = -layer * 22.0
        for x, y in part.outer:
            xs.append(x + dx)
            ys.append(y + dy)
    pad = 20.0
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    w = x1 - x0 + 2 * pad
    h = y1 - y0 + 2 * pad
    img = Image.new("RGBA", (int(w * PPM), int(h * PPM)), (250, 248, 242, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    # draw back-to-front for visibility
    for name, layer in reversed(order):
        part = parts[name]
        dx = pad - x0 + layer * 18.0
        dy = pad - y0 - layer * 22.0
        # For spacers/stand use absolute shift in draw coords via translating polys
        shifted = Part(
            name=part.name,
            outer=[(x + layer * 18.0, y - layer * 22.0) for x, y in part.outer],
            holes=[[(x + layer * 18.0, y - layer * 22.0) for x, y in h] for h in part.holes],
            engraves=[],
        )
        _draw_part(draw, shifted, pad - x0, pad - y0, COLORS.get(name, (160, 120, 80, 200)))
    path = path or (PREVIEW_DIR / "сборка_explode.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path)
    return path


def export_previews(p: FrameParams | None = None) -> list[Path]:
    p = p or DEFAULT
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    return [
        preview_parts_sheet(p),
        preview_assembled(p),
        preview_exploded(p),
    ]
