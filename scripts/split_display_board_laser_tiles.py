#!/usr/bin/env python3
"""Split fixed display-board PNG into laser field tiles (300x200 mm layout)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "витрины" / "доска_витрина_01_лазер_серый_лес_камни.png"
OUT_DIR = ROOT / "images" / "витрины" / "плитки_200x300"
FIELD_DIR = OUT_DIR / "поля_лазера_300x200"

BOARD_W_MM = 500.0
BOARD_H_MM = 1000.0
FIELD_W_MM = 300.0
FIELD_H_MM = 200.0
COL_WIDTHS = [300.0, 200.0]
ROW_HEIGHTS = [200.0] * 5
PPM = 10.0  # px per mm → field 3000×2000


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIELD_DIR.mkdir(parents=True, exist_ok=True)

    im = Image.open(SRC).convert("L")
    w, h = im.size
    sx, sy = w / BOARD_W_MM, h / BOARD_H_MM

    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 48)
    except OSError:
        font = ImageFont.load_default()

    manifest: list[dict] = []
    canvas = Image.new("L", (w, h), 255)
    y_mm = 0.0
    n = 1

    for r, rh in enumerate(ROW_HEIGHTS):
        x_mm = 0.0
        for c, cw in enumerate(COL_WIDTHS):
            x0 = int(round(x_mm * sx))
            y0 = int(round(y_mm * sy))
            x1 = int(round((x_mm + cw) * sx))
            y1 = int(round((y_mm + rh) * sy))
            x0, y0 = max(0, x0), max(0, y0)
            x1, y1 = min(w, x1), min(h, y1)

            crop = im.crop((x0, y0, x1, y1))
            tw, th = int(round(cw * PPM)), int(round(rh * PPM))
            tile = crop.resize((tw, th), Image.Resampling.LANCZOS)

            tile_name = f"плитка_{n:02d}_ряд{r + 1}_кол{c + 1}_{int(cw)}x{int(rh)}мм.png"
            tile.save(OUT_DIR / tile_name)

            fw, fh = int(round(FIELD_W_MM * PPM)), int(round(FIELD_H_MM * PPM))
            field = Image.new("L", (fw, fh), 255)
            field.paste(tile, (0, 0))
            draw = ImageDraw.Draw(field)

            mark = 8
            for mx, my in ((0, 0), (tw - 1, 0), (0, th - 1), (tw - 1, th - 1)):
                draw.line([(mx - mark, my), (mx + mark, my)], fill=0, width=2)
                draw.line([(mx, my - mark), (mx, my + mark)], fill=0, width=2)
            for mx, my in ((0, 0), (fw - 1, 0), (0, fh - 1), (fw - 1, fh - 1)):
                draw.line([(mx - 6, my), (mx + 6, my)], fill=0, width=1)
                draw.line([(mx, my - 6), (mx, my + 6)], fill=0, width=1)
            draw.text((fw - 90, 10), f"#{n}", fill=0, font=font)

            field_name = f"поле_{n:02d}_ряд{r + 1}_кол{c + 1}_лазер300x200.png"
            field.save(FIELD_DIR / field_name)

            canvas.paste(crop, (x0, y0))

            note = (
                "полная ширина поля"
                if cw >= FIELD_W_MM
                else "гравировать левые 200мм поля 300мм; справа пусто"
            )
            manifest.append(
                {
                    "n": n,
                    "row": r + 1,
                    "col": c + 1,
                    "origin_mm": [x_mm, y_mm],
                    "size_mm": [cw, rh],
                    "laser_field_mm": [FIELD_W_MM, FIELD_H_MM],
                    "source_px": [x0, y0, x1, y1],
                    "tile_file": tile_name,
                    "field_file": f"поля_лазера_300x200/{field_name}",
                    "note": note,
                }
            )
            print(f"#{n}: {cw:.0f}x{rh:.0f} mm -> {tile_name}")
            n += 1
            x_mm += cw
        y_mm += rh

    reasm_path = OUT_DIR / "_сборка_проверка.png"
    canvas.save(reasm_path)
    diff = int(np.abs(np.array(im).astype(int) - np.array(canvas).astype(int)).sum())

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "Плитки для гравировки доски 500x1000 мм",
        "Схема: доска_витрина_01_лазер_серый_лес_камни_сетка_200x300",
        "Ориентация поля лазера: 300 мм (ширина) x 200 мм (высота)",
        f"Исходник: {SRC.name}",
        f"Экспорт: {PPM:.0f} px/мм (поле 3000x2000 px)",
        "",
        "плитка_*: чистый фрагмент макета по размеру куска",
        "поля_лазера_300x200/: полный кадр поля 300x200 мм",
        "  (для кол.2 контент слева 200мм, справа белый запас)",
        "Кресты: углы контента и углы поля — для совмещения",
        "",
        "Порядок: 1→2, сдвиг вниз 3→4, … до 9→10",
        "",
    ]
    for m in manifest:
        lines.append(
            f"#{m['n']:02d} ряд{m['row']} кол{m['col']}: "
            f"origin ({m['origin_mm'][0]:.0f},{m['origin_mm'][1]:.0f}) мм, "
            f"кусок {m['size_mm'][0]:.0f}x{m['size_mm'][1]:.0f} мм | "
            f"{m['tile_file']} | {m['note']}"
        )
    lines += ["", f"Проверка сборки: _сборка_проверка.png (pixel_diff={diff})"]
    (OUT_DIR / "README_плитки.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"reassembly_abs_diff={diff}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
