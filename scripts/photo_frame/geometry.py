"""Geometric primitives for frame parts (mm, center of photo at origin, Y down)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .params import FrameParams

Point = tuple[float, float]
Poly = list[Point]


@dataclass
class Part:
    name: str
    outer: Poly
    holes: list[Poly]
    engraves: list[Poly]


def rect(cx: float, cy: float, w: float, h: float) -> Poly:
    hw, hh = w / 2.0, h / 2.0
    return [
        (cx - hw, cy - hh),
        (cx + hw, cy - hh),
        (cx + hw, cy + hh),
        (cx - hw, cy + hh),
    ]


def translate(poly: Poly, dx: float, dy: float) -> Poly:
    return [(x + dx, y + dy) for x, y in poly]


def bbox(poly: Poly) -> tuple[float, float, float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def poly_size(poly: Poly) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox(poly)
    return x1 - x0, y1 - y0


def rounded_rect(cx: float, cy: float, w: float, h: float, r: float, n: int = 6) -> Poly:
    r = min(r, w / 2.0, h / 2.0)
    hw, hh = w / 2.0, h / 2.0

    def arc(ox: float, oy: float, a0_deg: float, a1_deg: float) -> Iterable[Point]:
        for j in range(n + 1):
            t = j / n
            a = math.radians(a0_deg + (a1_deg - a0_deg) * t)
            yield (ox + r * math.cos(a), oy + r * math.sin(a))

    pts: Poly = []
    pts.extend(arc(cx + hw - r, cy - hh + r, -90, 0))
    pts.extend(arc(cx + hw - r, cy + hh - r, 0, 90))
    pts.extend(arc(cx - hw + r, cy + hh - r, 90, 180))
    pts.extend(arc(cx - hw + r, cy - hh + r, 180, 270))
    return pts


def keyhole_simple(cx: float, top_y: float, p: FrameParams) -> Poly:
    """Classic keyhole: round head + slot below. top_y = top of head."""
    r = p.keyhole_head_r
    sw = p.keyhole_stem_w / 2.0
    sh = p.keyhole_stem_h
    hx, hy = cx, top_y + r
    pts: Poly = []
    n = 28
    a0 = math.radians(35)
    a1 = math.radians(325)
    for j in range(n + 1):
        a = a0 + (a1 - a0) * j / n
        pts.append((hx + r * math.cos(a), hy + r * math.sin(a)))
    pts.append((cx + sw, hy + r * 0.3))
    pts.append((cx + sw, hy + r + sh))
    pts.append((cx - sw, hy + r + sh))
    pts.append((cx - sw, hy + r * 0.3))
    return pts


def finger_notch(cx: float, cy: float, r: float, n: int = 20) -> Poly:
    return [
        (cx + r * math.cos(2.0 * math.pi * j / n), cy + r * math.sin(2.0 * math.pi * j / n))
        for j in range(n)
    ]


def _ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 24) -> Poly:
    return [
        (cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def spacer_strips(p: FrameParams) -> list[Part]:
    """U spacers: left, right, bottom. Inner edge = pocket; top open for photo insert."""
    pw, ph = p.pocket_w, p.pocket_h
    sw = p.spacer_w
    # Sides include bottom corners; bottom strip only pocket width (no double material).
    left = rect((-pw / 2.0 - sw / 2.0), sw / 2.0, sw, ph + sw)
    right = rect((pw / 2.0 + sw / 2.0), sw / 2.0, sw, ph + sw)
    bottom = rect(0.0, (ph / 2.0 + sw / 2.0), pw, sw)
    return [
        Part(name="spacer_left", outer=left, holes=[], engraves=[]),
        Part(name="spacer_right", outer=right, holes=[], engraves=[]),
        Part(name="spacer_bottom", outer=bottom, holes=[], engraves=[]),
    ]


def back_plate(p: FrameParams, outer_silhouette: Poly | None = None) -> Part:
    """Back plate: same outer silhouette as front/mask.

    Holes: keyhole, finger notch, V+H stand slots.
    Slot rule: width ≈ T − KERF; length ≥ tab breadth.
    """
    outer = (
        list(outer_silhouette)
        if outer_silhouette is not None
        else rounded_rect(0.0, 0.0, p.core_w, p.core_h, r=4.0)
    )
    kh = keyhole_simple(0.0, -p.core_h / 2.0 + 10.0, p)
    fx = p.core_w / 2.0 - p.finger_notch_r - 6.0
    fy = -p.core_h / 2.0 + p.finger_notch_r + 6.0
    notch = finger_notch(fx, fy, p.finger_notch_r)

    cy = p.core_h / 2.0 - p.stand_slot_from_bottom
    v_slot = rect(0.0, cy, p.slot_w, p.leg_tab_w + 0.4)
    h_slot = rect(0.0, cy, p.brace_tab_w + 0.4, p.slot_w)

    glue = rect(0.0, sw_center_y(p), p.pocket_w + 2 * p.spacer_w, p.pocket_h + p.spacer_w)
    return Part(name="back", outer=outer, holes=[kh, notch, v_slot, h_slot], engraves=[glue])


def sw_center_y(p: FrameParams) -> float:
    return p.spacer_w / 2.0


def stand_leg(p: FrameParams) -> Part:
    """Trapezoid easel leg with wide top tab for the vertical back slot.

    Tab breadth in cutting plane = leg_tab_w (~12 mm) — NOT slot_w.
    When inserted 90°, plywood thickness T fills slot_w.
    """
    h = p.stand_height
    bw = p.stand_base_w
    tw = p.leg_tab_w
    tl = p.tab_len
    top_body = -h / 2.0 + 8.0

    # Simple stable silhouette: wide base, tapering shoulders, top tab
    pts: Poly = [
        (-bw / 2.0, h / 2.0),
        (bw / 2.0, h / 2.0),
        (bw / 2.0 - 4.0, h / 2.0 - 10.0),
        (14.0, 10.0),
        (tw / 2.0 + 4.0, top_body),
        (tw / 2.0, top_body),
        (tw / 2.0, top_body - tl),
        (-tw / 2.0, top_body - tl),
        (-tw / 2.0, top_body),
        (-tw / 2.0 - 4.0, top_body),
        (-14.0, 10.0),
        (-bw / 2.0 + 4.0, h / 2.0 - 10.0),
    ]
    # Mid slot where brace hooks the leg (open notch from front edge)
    # Through-slot: brace slides on; width = slot_w, height = brace engagement
    brace_hook_y = 18.0
    holes = [
        rect(0.0, brace_hook_y, p.slot_w, p.brace_hook_h),
        _ellipse(0.0, -8.0, 5.0, 10.0, n=18),
        _ellipse(0.0, 38.0, 4.5, 8.0, n=16),
    ]
    return Part(name="stand_leg", outer=pts, holes=holes, engraves=[])


def brace(p: FrameParams) -> Part:
    """Right-angle brace: horizontal tab → back; vertical slot → leg.

    Locks the easel angle. No separate connector piece.
    """
    slot = p.slot_w
    tw = p.brace_tab_w
    tl = p.tab_len
    # Body: trapezoid / wedge
    # Tab protrudes upward (into back horizontal slot when brace is horizontal-ish)
    # Layout in cutting plane: tab at +Y end, slot for leg in body
    body_w = max(p.brace_span, tw + 16.0)
    body_h = 36.0
    pts: Poly = [
        (-body_w / 2.0, body_h / 2.0),
        (-tw / 2.0, body_h / 2.0),
        (-tw / 2.0, body_h / 2.0 + tl),
        (tw / 2.0, body_h / 2.0 + tl),
        (tw / 2.0, body_h / 2.0),
        (body_w / 2.0, body_h / 2.0),
        (body_w / 2.0 - 6.0, -body_h / 2.0),
        (-body_w / 2.0 + 6.0, -body_h / 2.0),
    ]
    # Slot for leg thickness — centered so brace can slide onto leg
    hole = rect(0.0, -4.0, slot, p.brace_hook_h)
    return Part(name="brace", outer=pts, holes=[hole], engraves=[])


def skeleton_parts(p: FrameParams, outer_silhouette: Poly) -> list[Part]:
    """All structural parts; front/mask/back share the same outer silhouette."""
    front_win = rect(0.0, 0.0, p.front_window_w, p.front_window_h)
    mask_win = rect(0.0, 0.0, p.mask_window_w, p.mask_window_h)
    front = Part(name="front", outer=list(outer_silhouette), holes=[front_win], engraves=[])
    mask = Part(name="mask", outer=list(outer_silhouette), holes=[mask_win], engraves=[])
    parts = [front, mask]
    parts.extend(spacer_strips(p))
    parts.append(back_plate(p, outer_silhouette))
    parts.append(stand_leg(p))
    parts.append(brace(p))
    return parts


def shift_part_to_origin(part: Part, margin: float = 2.0) -> Part:
    """Translate part so bbox min is at (margin, margin)."""
    polys = [part.outer, *part.holes, *part.engraves]
    xs = [x for poly in polys for x, _ in poly]
    ys = [y for poly in polys for _, y in poly]
    if not xs:
        return part
    dx = margin - min(xs)
    dy = margin - min(ys)
    return Part(
        name=part.name,
        outer=translate(part.outer, dx, dy),
        holes=[translate(h, dx, dy) for h in part.holes],
        engraves=[translate(e, dx, dy) for e in part.engraves],
    )
