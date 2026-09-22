"""Parametric dimensions for the 10×15 multi-layer laser photo frame (mm).

All part sizes derive from these values. Do not hardcode mm elsewhere.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class FrameParams:
    # Source of truth
    photo_w: float = 100.0
    photo_h: float = 150.0
    t: float = 3.0  # material thickness
    # Diode lasers usually have a small kerf; start at 0.10 and tune ±0.05 after a test cut.
    kerf: float = 0.10  # slot kerf compensation (slot_w = t - kerf)
    photo_clear: float = 1.0  # pocket clearance per side
    overlap: float = 2.5  # front window inset per side vs photo
    border: float = 28.0  # rectangular core border around pocket
    spacer_w: float = 12.0  # spacer strip width
    ornament_extra: float = 28.0  # silhouette grow beyond core (avg)
    tab_len: float = 14.0  # how deep tabs go through the back plate
    leg_tab_w: float = 12.0  # breadth of leg tab in cutting plane (stability)
    brace_tab_w: float = 12.0  # breadth of brace tab in cutting plane
    brace_hook_h: float = 14.0  # length of slot where brace/leg interlock
    brace_span: float = 48.0  # brace body width
    stand_height: float = 100.0  # easel leg height
    stand_base_w: float = 58.0
    stand_slot_from_bottom: float = 30.0  # cross center from bottom edge of back
    keyhole_stem_h: float = 10.0
    keyhole_head_r: float = 3.5
    keyhole_stem_w: float = 2.2
    finger_notch_r: float = 12.0
    stroke_cut: float = 0.1

    @property
    def slot_w(self) -> float:
        return self.t - self.kerf

    @property
    def front_window_w(self) -> float:
        return self.photo_w - 2.0 * self.overlap

    @property
    def front_window_h(self) -> float:
        return self.photo_h - 2.0 * self.overlap

    @property
    def pocket_w(self) -> float:
        return self.photo_w + 2.0 * self.photo_clear

    @property
    def pocket_h(self) -> float:
        return self.photo_h + 2.0 * self.photo_clear

    @property
    def mask_window_w(self) -> float:
        return self.pocket_w

    @property
    def mask_window_h(self) -> float:
        return self.pocket_h

    @property
    def core_w(self) -> float:
        return self.pocket_w + 2.0 * self.border

    @property
    def core_h(self) -> float:
        return self.pocket_h + 2.0 * self.border

    @property
    def outer_w(self) -> float:
        return self.core_w + 2.0 * self.ornament_extra

    @property
    def outer_h(self) -> float:
        return self.core_h + 2.0 * self.ornament_extra + 18.0  # crest allowance

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(
            {
                "slot_w": self.slot_w,
                "front_window_w": self.front_window_w,
                "front_window_h": self.front_window_h,
                "pocket_w": self.pocket_w,
                "pocket_h": self.pocket_h,
                "mask_window_w": self.mask_window_w,
                "mask_window_h": self.mask_window_h,
                "core_w": self.core_w,
                "core_h": self.core_h,
                "outer_w": self.outer_w,
                "outer_h": self.outer_h,
            }
        )
        return d


DEFAULT = FrameParams()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "images" / "рамки" / "10x15"
LASER_DIR = OUT_DIR / "лазер"
PREVIEW_DIR = OUT_DIR / "превью"
