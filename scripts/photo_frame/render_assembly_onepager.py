"""One-page visual: glue layers + stand slots."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[2] / "images" / "рамки" / "10x15" / "инструкция" / "сборка_одно_изображение.png"

W, H = 1400, 1600
C_BG = (252, 250, 245)
C_INK = (35, 28, 20)
C_FRONT = (196, 140, 70)
C_MASK = (160, 110, 55)
C_SP = (220, 185, 120)
C_BACK = (120, 85, 45)
C_LEG = (150, 105, 50)
C_BR = (170, 125, 65)
C_GLUE = (210, 50, 50)
C_SLOT = (30, 110, 180)
C_OK = (35, 120, 70)
C_PHOTO = (175, 190, 210)


def font(n: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, n)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), C_BG)
    d = ImageDraw.Draw(img)
    f32, f24, f18, f17, f16, f15, f14 = (
        font(32),
        font(24),
        font(18),
        font(17),
        font(16),
        font(15),
        font(14),
    )

    d.text((40, 28), "Сборка рамки 10x15 — клей и пазы на одном листе", fill=C_INK, font=f32)

    # A. Glue stack
    d.text((50, 90), "A. СЛОИ С КЛЕЕМ (корпус)", fill=C_GLUE, font=f24)
    x0, y = 80, 150
    layers = [("front", C_FRONT, 36), ("mask", C_MASK, 36), ("spacers U", C_SP, 28), ("back", C_BACK, 36)]
    for i, (name, col, th) in enumerate(layers):
        d.rounded_rectangle((x0, y, x0 + 320, y + th), radius=6, fill=col, outline=C_INK, width=2)
        ink = (255, 255, 255) if name != "spacers U" else C_INK
        d.text((x0 + 12, y + 6), name, fill=ink, font=f18)
        y += th
        if i < len(layers) - 1:
            for gx in range(x0 + 10, x0 + 310, 14):
                d.line([(gx, y - 2), (gx + 7, y + 2)], fill=C_GLUE, width=3)
            d.text((x0 + 340, y - 12), "КЛЕЙ", fill=C_GLUE, font=f16)
            y += 18

    d.rectangle((150, 200, 250, 280), fill=C_PHOTO, outline=C_INK)
    d.polygon([(200, 165), (185, 190), (215, 190)], fill=C_SLOT)
    d.text((270, 210), "фото сверху", fill=C_SLOT, font=f16)
    d.text((270, 235), "в карман U", fill=C_SLOT, font=f16)
    d.text((50, y + 25), "Пазов между слоями корпуса нет —", fill=C_INK, font=f17)
    d.text((50, y + 50), "только склейка больших плоскостей.", fill=C_INK, font=f17)
    d.text((50, y + 85), "front = mask = back по силуэту", fill=C_OK, font=f17)

    # B. Slots
    d.text((720, 90), "B. ПАЗЫ ПОДСТАВКИ (без клея)", fill=C_SLOT, font=f24)
    bx, by = 780, 150
    d.rounded_rectangle((bx, by, bx + 280, by + 320), radius=14, fill=C_BACK, outline=C_INK, width=2)
    d.rectangle((bx + 125, by + 200, bx + 145, by + 270), fill=C_BG, outline=C_SLOT, width=2)
    d.rectangle((bx + 95, by + 225, bx + 175, by + 245), fill=C_BG, outline=C_SLOT, width=2)
    d.text((bx + 20, by + 20), "back (сзади)", fill=(255, 255, 255), font=f16)
    d.text((bx + 155, by + 185), "V-паз", fill=C_SLOT, font=f15)
    d.text((bx + 185, by + 250), "H-паз", fill=C_SLOT, font=f15)

    lx, ly = 1120, 170
    d.polygon(
        [(lx + 30, ly + 40), (lx + 70, ly + 40), (lx + 95, ly + 280), (lx + 5, ly + 280), (lx + 30, ly + 100)],
        fill=C_LEG,
        outline=C_INK,
        width=2,
    )
    d.rectangle((lx + 40, ly, lx + 60, ly + 40), fill=C_LEG, outline=C_INK, width=2)
    d.rectangle((lx + 42, ly + 150, lx + 58, ly + 185), fill=C_BG, outline=C_SLOT, width=2)
    d.text((lx - 10, ly + 290), "ножка", fill=C_INK, font=f16)
    d.text((lx + 70, ly + 5), "шип 12", fill=C_SLOT, font=f14)
    d.text((lx + 70, ly + 155), "паз", fill=C_SLOT, font=f14)

    d.rectangle((1080, 500, 1300, 560), fill=C_BR, outline=C_INK, width=2)
    d.rectangle((1160, 460, 1220, 500), fill=C_BR, outline=C_INK, width=2)
    d.rectangle((1175, 515, 1205, 550), fill=C_BG, outline=C_SLOT, width=2)
    d.text((1090, 575), "распорка", fill=C_INK, font=f16)
    d.text((1225, 470), "шип → H", fill=C_SLOT, font=f14)
    d.text((1225, 520), "паз ↔ ножка", fill=C_SLOT, font=f14)

    d.text((920, 130), "1. шип ножки → V", fill=C_SLOT, font=f16)
    d.text((780, 490), "2. паз распорки ↔ паз ножки", fill=C_SLOT, font=f16)
    d.text((780, 520), "3. шип распорки → H", fill=C_SLOT, font=f16)

    # C. Combined side view
    d.line([(50, 700), (1350, 700)], fill=(200, 190, 180), width=2)
    d.text((50, 720), "C. ВСЁ ВМЕСТЕ (вид сбоку)", fill=C_INK, font=f24)

    sx = 120
    d.rectangle((sx, 780, sx + 50, 1180), fill=C_FRONT, outline=C_INK, width=2)
    d.rectangle((sx + 50, 780, sx + 90, 1180), fill=C_MASK, outline=C_INK, width=2)
    d.rectangle((sx + 90, 820, sx + 110, 1140), fill=C_SP, outline=C_INK, width=2)
    d.rectangle((sx + 110, 780, sx + 155, 1180), fill=C_BACK, outline=C_INK, width=2)
    d.rectangle((sx + 15, 860, sx + 45, 1100), fill=C_PHOTO, outline=C_INK)
    for gy in (828, 900, 1000, 1100):
        d.line([(sx + 48, gy), (sx + 52, gy + 8)], fill=C_GLUE, width=2)
        d.line([(sx + 88, gy), (sx + 92, gy + 8)], fill=C_GLUE, width=2)
        d.line([(sx + 108, gy), (sx + 112, gy + 8)], fill=C_GLUE, width=2)

    d.polygon([(sx + 155, 1050), (sx + 320, 1220), (sx + 155, 1180)], fill=C_LEG, outline=C_INK, width=2)
    d.polygon([(sx + 155, 1080), (sx + 260, 1120), (sx + 155, 1145)], fill=C_BR, outline=C_INK, width=2)
    d.ellipse((sx + 145, 1068, sx + 165, 1088), outline=C_SLOT, width=3)
    d.ellipse((sx + 145, 1110, sx + 165, 1130), outline=C_SLOT, width=3)
    d.text((sx + 175, 1055), "пазы", fill=C_SLOT, font=f15)

    d.text((sx, 1240), "front", fill=C_FRONT, font=f14)
    d.text((sx + 48, 1240), "mask", fill=C_MASK, font=f14)
    d.text((sx + 85, 1260), "U", fill=C_INK, font=f14)
    d.text((sx + 115, 1240), "back", fill=C_BACK, font=f14)
    d.text((sx + 220, 1240), "ножка+распорка", fill=C_INK, font=f14)

    d.rounded_rectangle((520, 780, 1320, 1220), radius=16, fill=(255, 255, 255), outline=C_INK, width=2)
    d.text((560, 810), "Легенда", fill=C_INK, font=font(26))
    d.line([(560, 860), (620, 880)], fill=C_GLUE, width=4)
    d.text((640, 860), "КЛЕЙ — front↔mask, mask↔спейсеры, спейсеры↔back", fill=C_GLUE, font=f18)
    d.rectangle((560, 920, 600, 945), outline=C_SLOT, width=3)
    d.text((640, 920), "ПАЗ/ШИП — только подставка:", fill=C_SLOT, font=f18)
    d.text((660, 960), "• шип ножки 12 мм  →  V-паз на back", fill=C_INK, font=f17)
    d.text((660, 995), "• шип распорки 12 мм  →  H-паз на back", fill=C_INK, font=f17)
    d.text((660, 1030), "• паз распорки  ↔  паз на ножке (крест-накрест)", fill=C_INK, font=f17)
    d.text((560, 1090), "Порядок: 1) ножка в V  2) распорка на ножку  3) шип в H", fill=C_INK, font=f17)
    d.text((560, 1135), "Фото 10×15 — сверху в U-карман (без клея).", fill=C_OK, font=f17)
    d.text((560, 1170), "Диод: KERF 0.10 → паз 2.90 мм.", fill=C_INK, font=f16)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
