"""Baroque outer silhouette and front filigree for the photo frame."""

from __future__ import annotations

import math

from .geometry import Part, Poly, _ellipse, rect
from .params import FrameParams


def _bez(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float], n: int = 12) -> Poly:
    pts: Poly = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def outer_silhouette(p: FrameParams) -> Poly:
    """Shared outer contour for front ornate + solid mask (mm, photo center origin)."""
    hw = p.core_w / 2.0
    hh = p.core_h / 2.0
    e = p.ornament_extra

    # Build right half top→bottom→top, then mirror.
    # Start at top center under crest attachment.
    right: Poly = []

    # Shell crest (right half) — taller, more baroque
    crest_top = -hh - e - 22.0
    right.extend(
        _bez(
            (0.0, crest_top),
            (6.0, crest_top - 8.0),
            (16.0, crest_top + 2.0),
            (12.0, crest_top + 18.0),
            n=10,
        )[1:]
    )
    right.extend(
        _bez(
            (12.0, crest_top + 18.0),
            (20.0, crest_top + 22.0),
            (22.0, -hh - e + 2.0),
            (16.0, -hh - e + 8.0),
            n=8,
        )[1:]
    )

    # Top-right scroll / corner flourish
    right.extend(
        _bez(
            (16.0, -hh - e + 8.0),
            (hw * 0.4, -hh - e - 10.0),
            (hw + e * 0.7, -hh - e * 0.45),
            (hw + e * 0.95, -hh + 6.0),
            n=16,
        )[1:]
    )

    # Right side body with mid bulge / chevron ears
    right.extend(
        _bez(
            (hw + e * 0.95, -hh + 6.0),
            (hw + e * 1.05, -hh * 0.35),
            (hw + e * 0.75, 0.0),
            (hw + e * 0.95, hh * 0.35),
            n=12,
        )[1:]
    )
    right.extend(
        _bez(
            (hw + e * 0.95, hh * 0.35),
            (hw + e * 1.1, hh * 0.7),
            (hw + e * 0.7, hh + e * 0.4),
            (hw * 0.55, hh + e * 0.85),
            n=12,
        )[1:]
    )

    # Bottom-right foot scroll
    right.extend(
        _bez(
            (hw * 0.55, hh + e * 0.85),
            (hw * 0.25, hh + e * 1.05),
            (hw * 0.1, hh + e * 0.7),
            (0.0, hh + e * 0.55),
            n=10,
        )[1:]
    )

    # Mirror to left (reverse, skip duplicated center points)
    left = [(-x, y) for x, y in reversed(right[1:-1])]
    # Full crest: rebuild left crest wing + center
    full: Poly = [(0.0, crest_top)]
    full.extend(right)
    full.extend(left)
    return full


def front_filigree_holes(p: FrameParams) -> list[Poly]:
    """Internal cutouts for the ornate front layer (not on mask)."""
    hw = p.core_w / 2.0
    hh = p.core_h / 2.0
    e = p.ornament_extra * 0.55
    holes: list[Poly] = []

    # Corner scroll voids (4 corners, mirrored)
    corner_specs = [
        (hw * 0.72, -hh * 0.78, 1, 1),
        (hw * 0.72, hh * 0.78, 1, -1),
        (-hw * 0.72, -hh * 0.78, -1, 1),
        (-hw * 0.72, hh * 0.78, -1, -1),
    ]
    for cx, cy, sx, sy in corner_specs:
        base = _scroll_hole()
        holes.append([(cx + sx * x, cy + sy * y) for x, y in base])

    # Side mid voids
    for sx in (-1.0, 1.0):
        holes.append(_ellipse(sx * (hw + e * 0.15), 0.0, 5.5, 16.0, n=20))
        holes.append(_ellipse(sx * (hw * 0.92), -hh * 0.35, 4.0, 9.0, n=16))
        holes.append(_ellipse(sx * (hw * 0.92), hh * 0.35, 4.0, 9.0, n=16))

    # Top crest voids
    holes.append(_ellipse(0.0, -hh - e * 0.35, 7.0, 5.0, n=18))
    holes.append(_ellipse(-10.0, -hh - e * 0.15, 3.5, 4.5, n=14))
    holes.append(_ellipse(10.0, -hh - e * 0.15, 3.5, 4.5, n=14))

    # Bottom flourish voids
    holes.append(_ellipse(0.0, hh + e * 0.25, 8.0, 4.5, n=16))
    holes.append(_ellipse(-12.0, hh + e * 0.35, 4.0, 5.0, n=14))
    holes.append(_ellipse(12.0, hh + e * 0.35, 4.0, 5.0, n=14))

    # Frame rail beads along window (outside front window, inside core)
    fw, fh = p.front_window_w, p.front_window_h
    for i in range(3):
        y = -fh / 2.0 - 8.0 - i * 6.0
        if abs(y) < hh - 10:
            holes.append(_ellipse(-fw / 2.0 - 10.0, y * 0.3 + (-20 + i * 18), 2.8, 5.0, n=12))
            holes.append(_ellipse(fw / 2.0 + 10.0, y * 0.3 + (-20 + i * 18), 2.8, 5.0, n=12))

    return holes


def _scroll_hole() -> Poly:
    """Small comma/scroll shaped hole in local coords."""
    return [
        (0.0, -6.0),
        (4.0, -5.0),
        (7.0, -1.0),
        (6.0, 4.0),
        (2.0, 6.0),
        (-1.0, 4.0),
        (0.5, 1.0),
        (2.5, 0.0),
        (1.0, -2.0),
        (-2.0, -2.5),
        (-3.5, -5.0),
    ]


def apply_ornament(front: Part, mask: Part, p: FrameParams) -> tuple[Part, Part]:
    """Attach shared silhouette and front-only filigree."""
    sil = outer_silhouette(p)
    front = Part(
        name="front",
        outer=sil,
        holes=[rect(0.0, 0.0, p.front_window_w, p.front_window_h), *front_filigree_holes(p)],
        engraves=[],
    )
    mask = Part(
        name="mask",
        outer=list(sil),
        holes=[rect(0.0, 0.0, p.mask_window_w, p.mask_window_h)],
        engraves=[],
    )
    return front, mask
