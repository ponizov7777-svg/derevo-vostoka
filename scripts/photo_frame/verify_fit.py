"""Dimensional fit verification for the multi-layer photo frame."""

from __future__ import annotations

import math
import sys

from .export_svg import build_all_parts
from .geometry import Part, Poly, poly_size
from .params import DEFAULT, FrameParams


class FitError(Exception):
    pass


def _approx_eq(a: float, b: float, tol: float = 0.05) -> bool:
    return abs(a - b) <= tol


def _find(parts: list[Part], name: str) -> Part:
    for p in parts:
        if p.name == name:
            return p
    raise FitError(f"Missing part: {name}")


def verify(p: FrameParams | None = None) -> list[str]:
    p = p or DEFAULT
    parts = build_all_parts(p)
    msgs: list[str] = []

    assert _approx_eq(p.slot_w, p.t - p.kerf)

    front = _find(parts, "front")
    mask = _find(parts, "mask")
    back = _find(parts, "back")
    leg = _find(parts, "stand_leg")
    brace = _find(parts, "brace")

    # No obsolete connector
    if any(pt.name == "brace_connector" for pt in parts):
        raise FitError("brace_connector should be removed — use brace+leg only")

    fw, fh = poly_size(front.holes[0])
    mw, mh = poly_size(mask.holes[0])
    if not (_approx_eq(fw, p.front_window_w) and _approx_eq(fh, p.front_window_h)):
        raise FitError(f"Front window size {fw}x{fh} != {p.front_window_w}x{p.front_window_h}")
    if not (_approx_eq(mw, p.mask_window_w) and _approx_eq(mh, p.mask_window_h)):
        raise FitError(f"Mask window size {mw}x{mh} != {p.mask_window_w}x{p.mask_window_h}")
    if not (fw < p.photo_w < mw and fh < p.photo_h < mh):
        raise FitError(
            f"Photo fit failed: front {fw}x{fh} < photo {p.photo_w}x{p.photo_h} < pocket {mw}x{mh}"
        )
    msgs.append(
        f"OK photo stack: window {fw:.1f}x{fh:.1f} < photo {p.photo_w:.0f}x{p.photo_h:.0f} "
        f"< pocket {mw:.1f}x{mh:.1f}"
    )

    # Front/mask/back share outer silhouette
    if len(front.outer) != len(mask.outer) or len(front.outer) != len(back.outer):
        raise FitError("Front/mask/back outer point counts differ")
    max_d = 0.0
    for a, b, c in zip(front.outer, mask.outer, back.outer):
        max_d = max(
            max_d,
            math.hypot(a[0] - b[0], a[1] - b[1]),
            math.hypot(a[0] - c[0], a[1] - c[1]),
        )
    if max_d > 0.01:
        raise FitError(f"Front/mask/back outer silhouette mismatch max_d={max_d}")
    msgs.append(f"OK shared silhouette front=mask=back ({len(front.outer)} pts)")

    for name in ("spacer_left", "spacer_right", "spacer_bottom"):
        sp = _find(parts, name)
        w, h = poly_size(sp.outer)
        if min(w, h) < p.spacer_w - 0.2:
            raise FitError(f"{name} thinner than spacer_w: {w}x{h}")
    left = _find(parts, "spacer_left")
    _, lh = poly_size(left.outer)
    if lh < p.pocket_h - 0.5:
        raise FitError(f"Left spacer height {lh} < pocket_h {p.pocket_h}")
    msgs.append("OK U-spacers (top open for photo insert)")

    # Back slots: last two holes are v_slot, h_slot
    v_slot, h_slot = back.holes[-2], back.holes[-1]
    vw, vh = poly_size(v_slot)
    hw, hh = poly_size(h_slot)
    if not _approx_eq(min(vw, vh), p.slot_w, tol=0.05):
        raise FitError(f"Vertical slot thin dim {min(vw, vh)} != slot_w {p.slot_w}")
    if not _approx_eq(max(vw, vh), p.leg_tab_w + 0.4, tol=0.05):
        raise FitError(f"Vertical slot length {max(vw, vh)} != leg_tab_w+0.4")
    if not _approx_eq(min(hw, hh), p.slot_w, tol=0.05):
        raise FitError(f"Horizontal slot thin dim {min(hw, hh)} != slot_w {p.slot_w}")
    if not _approx_eq(max(hw, hh), p.brace_tab_w + 0.4, tol=0.05):
        raise FitError(f"Horizontal slot length {max(hw, hh)} != brace_tab_w+0.4")
    msgs.append(
        f"OK back slots: V {p.slot_w:.2f}x{p.leg_tab_w + 0.4:.1f}, "
        f"H {p.brace_tab_w + 0.4:.1f}x{p.slot_w:.2f}"
    )

    # Leg tab tip breadth = leg_tab_w
    top_y = min(y for _, y in leg.outer)
    tip = [(x, y) for x, y in leg.outer if y <= top_y + 1.0]
    tip_w = max(x for x, _ in tip) - min(x for x, _ in tip)
    if not _approx_eq(tip_w, p.leg_tab_w, tol=0.3):
        raise FitError(f"Leg tab tip width {tip_w:.2f} != leg_tab_w {p.leg_tab_w}")
    msgs.append(f"OK leg tab breadth {tip_w:.1f} mm (stable, not slot-thin)")

    # Brace slot matches material; brace tab breadth
    bw, bh = poly_size(brace.holes[0])
    if not _approx_eq(min(bw, bh), p.slot_w, tol=0.05):
        raise FitError(f"Brace leg-slot {bw}x{bh} != slot_w {p.slot_w}")
    brace_top = min(y for _, y in brace.outer)
    # tab is at max y end
    brace_bot_tab = max(y for _, y in brace.outer)
    tab_pts = [(x, y) for x, y in brace.outer if y >= brace_bot_tab - 0.5]
    # Actually tab is at +Y (body_h/2 + tl) — highest Y
    high = max(y for _, y in brace.outer)
    tab_pts = [(x, y) for x, y in brace.outer if abs(y - high) < 0.5]
    tab_w = max(x for x, _ in tab_pts) - min(x for x, _ in tab_pts)
    if not _approx_eq(tab_w, p.brace_tab_w, tol=0.3):
        raise FitError(f"Brace tab width {tab_w:.2f} != brace_tab_w {p.brace_tab_w}")
    msgs.append("OK brace: tab + leg slot match T/tab widths")

    bw, bh = poly_size(back.outer)
    fw_o, fh_o = poly_size(front.outer)
    if abs(bw - fw_o) > 0.5 or abs(bh - fh_o) > 0.5:
        raise FitError(f"Back outer {bw}x{bh} != front outer {fw_o}x{fh_o}")
    msgs.append(f"OK back matches front outer ({bw:.1f}x{bh:.1f})")

    if len(front.holes) < 2:
        raise FitError("Front missing filigree holes")
    msgs.append(f"OK front filigree holes: {len(front.holes) - 1}")

    # Stability notes as soft checks
    if p.stand_base_w < 50:
        raise FitError("Stand base too narrow for stability (<50 mm)")
    if p.leg_tab_w < 10:
        raise FitError("Leg tab too narrow for strength (<10 mm)")
    msgs.append("OK stand proportions (base>=50, tab>=10)")

    msgs.append("ALL FIT CHECKS PASSED")
    return msgs


def main() -> None:
    try:
        for line in verify(DEFAULT):
            print(line)
    except FitError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
