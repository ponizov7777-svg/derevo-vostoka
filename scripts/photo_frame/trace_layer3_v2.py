"""Export the second, independently generated layer-3 decoration."""

from __future__ import annotations

from .params import LASER_DIR, PREVIEW_DIR, PROJECT_ROOT
from .trace_layer3 import export_layer3


ART_SRC = (
    PROJECT_ROOT
    / "images"
    / "рамки"
    / "10x15"
    / "референсы"
    / "рамка_10x15_слой3_декор_v2.png"
)


def main() -> None:
    info = export_layer3(
        art_path=ART_SRC,
        svg_path=LASER_DIR / "слой3_декор_v2.svg",
        engrave_path=LASER_DIR / "слой3_декор_v2_гравировка.png",
        preview_path=PREVIEW_DIR / "слой3_декор_v2.png",
    )
    w, h = info["size_mm"]
    print(f"{info['svg']}: {w} x {h} mm, window Ø{info['window_d_mm']} mm")
    print(f"engrave: {info['engrave']} {info['engrave_px']}")
    print(f"preview: {info['preview']}")


if __name__ == "__main__":
    main()
