"""Step-by-step assembly diagrams (simple geometry) + written guide."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .params import DEFAULT, FrameParams, OUT_DIR, PREVIEW_DIR

# Colors for diagram parts
C_FRONT = (196, 140, 70)
C_MASK = (160, 110, 55)
C_SPACER = (220, 185, 120)
C_BACK = (120, 85, 45)
C_LEG = (150, 105, 50)
C_BRACE = (170, 125, 65)
C_PHOTO = (180, 195, 210)
C_GLUE = (255, 80, 80, 90)
C_BG = (252, 250, 245)
C_INK = (40, 30, 20)
C_OK = (40, 130, 70)


def _font(size: int):
    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _new(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), C_BG)
    return img, ImageDraw.Draw(img, "RGBA")


def _title(draw: ImageDraw.ImageDraw, text: str, y: int = 24) -> None:
    draw.text((40, y), text, fill=C_INK, font=_font(28))


def _note(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], color=C_INK) -> None:
    draw.text(xy, text, fill=color, font=_font(18))


def _label(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int]) -> None:
    draw.text(xy, text, fill=C_INK, font=_font(16))


def step01_parts_map(out: Path) -> None:
    """Catalog of all cut parts with names."""
    img, d = _new(1100, 900)
    _title(d, "Этап 0. Детали после резки (8 шт.)")
    # Front
    d.rounded_rectangle((60, 90, 260, 360), radius=20, fill=C_FRONT, outline=C_INK, width=2)
    d.rectangle((110, 150, 210, 300), fill=C_BG, outline=C_INK)
    d.ellipse((80, 120, 100, 145), outline=C_INK, width=2)
    _label(d, "1. front", (120, 370))
    _label(d, "ажур + окно", (105, 392))
    # Mask
    d.rounded_rectangle((300, 90, 500, 360), radius=20, fill=C_MASK, outline=C_INK, width=2)
    d.rectangle((340, 145, 460, 305), fill=C_BG, outline=C_INK)
    _label(d, "2. mask", (360, 370))
    _label(d, "силовая маска", (340, 392))
    # Spacers
    d.rectangle((560, 100, 590, 300), fill=C_SPACER, outline=C_INK, width=2)
    d.rectangle((610, 100, 640, 300), fill=C_SPACER, outline=C_INK, width=2)
    d.rectangle((560, 320, 700, 350), fill=C_SPACER, outline=C_INK, width=2)
    _label(d, "3–5. spacer L/R/B", (560, 370))
    _label(d, "U-карман под фото", (560, 392))
    # Back
    d.rounded_rectangle((760, 110, 980, 340), radius=8, fill=C_BACK, outline=C_INK, width=2)
    d.ellipse((855, 130, 885, 160), outline=(250, 250, 250), width=2)
    d.ellipse((920, 130, 955, 165), outline=(250, 250, 250), width=2)
    d.rectangle((862, 250, 878, 300), fill=C_BG)
    d.rectangle((845, 268, 895, 282), fill=C_BG)
    _label(d, "6. back", (835, 370))
    _label(d, "keyhole + крест", (815, 392))
    # Leg
    d.polygon(
        [(100, 720), (240, 720), (210, 560), (185, 500), (185, 470), (155, 470), (155, 500), (130, 560)],
        fill=C_LEG,
        outline=C_INK,
    )
    d.rectangle((165, 545, 175, 575), fill=C_BG)
    _label(d, "7. stand_leg", (130, 740))
    # Brace
    d.rectangle((340, 580, 520, 640), fill=C_BRACE, outline=C_INK, width=2)
    d.rectangle((410, 545, 450, 580), fill=C_BRACE, outline=C_INK, width=2)
    d.rectangle((420, 600, 440, 630), fill=C_BG)
    _label(d, "8. brace", (400, 660))
    _note(d, "brace_connector больше нет — убран как лишний/неясный элемент.", (60, 800), C_OK)
    _note(d, "Материал: фанера 3 мм. Клей: ПВА по дереву на большие плоскости.", (60, 830))
    img.save(out)


def step02_glue_front_mask(out: Path) -> None:
    img, d = _new(1100, 720)
    _title(d, "Этап 1. Склеить front + mask (большая площадь)")
    # side view stack
    d.rectangle((120, 200, 520, 250), fill=C_FRONT, outline=C_INK, width=2)
    d.rectangle((120, 250, 520, 300), fill=C_MASK, outline=C_INK, width=2)
    d.rectangle((220, 200, 420, 300), fill=C_BG, outline=C_INK)
    _label(d, "front", (130, 210))
    _label(d, "mask", (130, 265))
    _label(d, "окна соосны", (250, 320))
    # glue hatch
    for x in range(130, 510, 18):
        d.line([(x, 248), (x + 10, 252)], fill=(220, 60, 60), width=2)
    _note(d, "КЛЕЙ здесь (кроме окон и ажурных прорезей)", (120, 360), (180, 40, 40))
    _note(d, "1) Совместить внешние силуэты 1:1", (580, 180))
    _note(d, "2) Окно front 95x145 внутри окна mask 102x152", (580, 220))
    _note(d, "3) Прижать до высыхания (грузы / струбцины с прокладками)", (580, 260))
    _note(d, "Устойчивость: после склейки получается жёсткая", (580, 340), C_OK)
    _note(d, "лицевая панель ~6 мм с общей кромкой.", (580, 370), C_OK)
    img.save(out)


def step03_spacers(out: Path) -> None:
    img, d = _new(1100, 780)
    _title(d, "Этап 2. U-спейсеры на оборот mask (клей)")
    # back of mask
    d.rounded_rectangle((80, 100, 480, 620), radius=24, fill=C_MASK, outline=C_INK, width=2)
    d.rectangle((170, 180, 390, 480), fill=(90, 90, 90), outline=C_INK)  # window dark = through
    # U spacers
    d.rectangle((140, 180, 170, 520), fill=C_SPACER, outline=C_INK, width=2)
    d.rectangle((390, 180, 420, 520), fill=C_SPACER, outline=C_INK, width=2)
    d.rectangle((170, 480, 390, 520), fill=C_SPACER, outline=C_INK, width=2)
    _label(d, "L", (145, 330))
    _label(d, "R", (395, 330))
    _label(d, "B", (265, 490))
    _note(d, "ВЕРХ ОТКРЫТ", (230, 140), (180, 40, 40))
    d.polygon([(280, 160), (260, 190), (300, 190)], fill=(180, 40, 40))
    _note(d, "Карман внутри U: 102 x 152 мм", (520, 180))
    _note(d, "Фото 100 x 150 входит с люфтом 1 мм", (520, 220))
    _note(d, "Клей: mask ↔ все 3 спейсера", (520, 280), (180, 40, 40))
    _note(d, "(площадь контакта полосок 12 мм — достаточна)", (520, 310))
    _note(d, "Важно: внутренние кромки L/R/B", (520, 380))
    _note(d, "образуют ровный прямоугольник кармана.", (520, 410))
    _note(d, "Глубина кармана = 3 мм (один слой).", (520, 470), C_OK)
    _note(d, "Хватает для фотобумаги; стекло/акрил —", (520, 500))
    _note(d, "нужен второй слой спейсеров (пока не делаем).", (520, 530))
    img.save(out)


def step04_back(out: Path) -> None:
    img, d = _new(1100, 780)
    _title(d, "Этап 3. Приклеить back на спейсеры (силуэт = front/mask)")
    # side stack
    d.rectangle((100, 140, 420, 175), fill=C_FRONT, outline=C_INK)
    d.rectangle((100, 175, 420, 210), fill=C_MASK, outline=C_INK)
    d.rectangle((100, 210, 140, 245), fill=C_SPACER, outline=C_INK)
    d.rectangle((380, 210, 420, 245), fill=C_SPACER, outline=C_INK)
    d.rectangle((140, 230, 380, 245), fill=C_SPACER, outline=C_INK)
    d.rectangle((100, 245, 420, 290), fill=C_BACK, outline=C_INK)
    _label(d, "front+mask", (430, 160))
    _label(d, "U-спейсеры", (430, 215))
    _label(d, "back = тот же силуэт", (430, 258))
    for x in range(110, 410, 16):
        d.line([(x, 243), (x + 8, 247)], fill=(220, 60, 60), width=2)
    _note(d, "КЛЕЙ: спейсеры ↔ back", (100, 320), (180, 40, 40))
    _note(d, "Кромки front/mask/back совпадают по всему контуру.", (100, 360), C_OK)
    _note(d, "Keyhole сверху, крест-пазы снизу, вырез пальца справа сверху.", (100, 400))
    _note(d, "После склейки корпус замкнут: фото вставляется", (100, 460), C_OK)
    _note(d, "сверху в щель (U открыт вверх) и достаётся через", (100, 490), C_OK)
    _note(d, "круглый вырез пальца на заднике.", (100, 520), C_OK)
    d.rectangle((700, 180, 780, 420), fill=C_PHOTO, outline=C_INK)
    d.polygon([(740, 140), (720, 175), (760, 175)], fill=(40, 100, 180))
    _label(d, "фото", (720, 300))
    _label(d, "вставка сверху", (680, 450))
    img.save(out)


def step05_stand(out: Path) -> None:
    img, d = _new(1100, 820)
    _title(d, "Этап 4. Подставка: ножка + распорка (без клея)")
    # back plate with cross
    d.rounded_rectangle((80, 100, 360, 420), radius=8, fill=C_BACK, outline=C_INK, width=2)
    d.rectangle((210, 300, 230, 360), fill=C_BG)  # V slot
    d.rectangle((185, 322, 255, 338), fill=C_BG)  # H slot
    _label(d, "back (вид сзади)", (140, 440))
    _label(d, "V-паз = ножка", (380, 310))
    _label(d, "H-паз = распорка", (380, 340))
    # leg
    d.polygon([(620, 120), (660, 120), (660, 160), (720, 420), (560, 420), (620, 160)], fill=C_LEG, outline=C_INK, width=2)
    d.rectangle((630, 90, 650, 120), fill=C_LEG, outline=C_INK, width=2)
    _label(d, "шип 12 мм", (670, 95))
    d.rectangle((632, 250, 648, 290), fill=C_BG)
    _label(d, "паз под распорку", (670, 255))
    # brace
    d.rectangle((820, 280, 980, 340), fill=C_BRACE, outline=C_INK, width=2)
    d.rectangle((880, 240, 920, 280), fill=C_BRACE, outline=C_INK, width=2)
    d.rectangle((890, 300, 910, 335), fill=C_BG)
    _label(d, "шип в H-паз", (880, 210))
    _label(d, "паз на ножку", (920, 350))
    _note(d, "Порядок: 1) шип ножки в V-паз до упора", (80, 500))
    _note(d, "         2) распорку пазом надеть на ножку", (80, 535))
    _note(d, "         3) шип распорки защёлкнуть в H-паз", (80, 570))
    _note(d, "Клей на подставку НЕ нужен — съёмная конструкция.", (80, 620), C_OK)
    _note(d, "Устойчивость: база ножки ~58 мм, угол фиксирует распорка.", (80, 655), C_OK)
    _note(d, "Если пазы тугие/слабые — подстройте KERF после пробного реза.", (80, 700))
    img.save(out)


def step06_final(out: Path) -> None:
    img, d = _new(1100, 780)
    _title(d, "Этап 5. Готово: фото + проверка")
    # assembled side view
    d.rectangle((120, 160, 200, 480), fill=C_FRONT, outline=C_INK)
    d.rectangle((200, 160, 240, 480), fill=C_MASK, outline=C_INK)
    d.rectangle((240, 200, 260, 440), fill=C_SPACER, outline=C_INK)
    d.rectangle((260, 180, 300, 480), fill=C_BACK, outline=C_INK)
    d.polygon([(300, 360), (420, 520), (300, 480)], fill=C_LEG, outline=C_INK)
    d.polygon([(300, 400), (380, 430), (300, 450)], fill=C_BRACE, outline=C_INK)
    d.rectangle((145, 220, 195, 420), fill=C_PHOTO, outline=C_INK)
    _label(d, "вид сбоку", (150, 520))
    _note(d, "Чек-лист устойчивости и посадки:", (500, 160), C_OK)
    checks = [
        "front+mask склеены, кромки совпадают",
        "фото 10x15 входит сверху без усилия",
        "фото не выпадает вниз (есть нижний spacer)",
        "края фото перекрыты окном front (overlap 2.5)",
        "ножка сидит в V-пазе без люфта по толщине",
        "распорка держит угол, рамка не падает вперёд",
        "keyhole свободен (настенный вариант)",
    ]
    y = 210
    for c in checks:
        d.ellipse((500, y + 4, 516, y + 20), outline=C_OK, width=2)
        _note(d, c, (530, y))
        y += 40
    img.save(out)


def step_overview_stack(out: Path) -> None:
    img, d = _new(1100, 700)
    _title(d, "Схема слоёв (спереди → назад)")
    layers = [
        ("front", C_FRONT, "ажур, окно 95×145"),
        ("mask", C_MASK, "сила, окно 102×152, КЛЕЙ к front"),
        ("spacers U", C_SPACER, "карман 3 мм, КЛЕЙ к mask и back"),
        ("back", C_BACK, "замок кармана + пазы подставки"),
        ("leg+brace", C_LEG, "съёмно, без клея"),
    ]
    y = 120
    for name, color, desc in layers:
        d.rounded_rectangle((80, y, 420, y + 70), radius=10, fill=color, outline=C_INK, width=2)
        _label(d, name, (100, y + 22))
        _note(d, desc, (450, y + 22))
        y += 90
    img.save(out)


def export_assembly_guide(p: FrameParams | None = None) -> list[Path]:
    p = p or DEFAULT
    guide_dir = OUT_DIR / "инструкция"
    guide_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        guide_dir / "00_детали.png",
        guide_dir / "01_склейка_front_mask.png",
        guide_dir / "02_спейсеры_U.png",
        guide_dir / "03_задник.png",
        guide_dir / "04_подставка.png",
        guide_dir / "05_финал_проверка.png",
        guide_dir / "схема_слоёв.png",
    ]
    step01_parts_map(paths[0])
    step02_glue_front_mask(paths[1])
    step03_spacers(paths[2])
    step04_back(paths[3])
    step05_stand(paths[4])
    step06_final(paths[5])
    step_overview_stack(paths[6])

    text = guide_dir / "сборка_подробно.txt"
    text.write_text(_instruction_text(p), encoding="utf-8")
    paths.append(text)
    return paths


def _instruction_text(p: FrameParams) -> str:
    return f"""ФОТОРАМКА 10×15 — ПОДРОБНАЯ ИНСТРУКЦИЯ ПО СБОРКЕ
================================================
Материал: фанера {p.t:.0f} мм
Фото: {p.photo_w:.0f}×{p.photo_h:.0f} мм (портрет)
Паз под толщину: {p.slot_w:.2f} мм (= T − KERF {p.kerf})

СОСТАВ (8 деталей)
------------------
1. front          — лицевой ажур, окно {p.front_window_w:.0f}×{p.front_window_h:.0f}
2. mask           — силовая маска (тот же силуэт), окно {p.mask_window_w:.0f}×{p.mask_window_h:.0f}
3. spacer_left    — боковая стенка кармана
4. spacer_right   — боковая стенка кармана
5. spacer_bottom  — дно кармана
6. back           — задник ПО СИЛУЭТУ (как front/mask): keyhole, вырез пальца, V+H пазы
7. stand_leg      — ножка-подставка, шип {p.leg_tab_w:.0f} мм
8. brace          — распорка угла, шип {p.brace_tab_w:.0f} мм

Удалён brace_connector — в старой версии не было однозначной
сборки; угол теперь держат только ножка + распорка.


ЭТАП 1. Front + mask (КЛЕЙ)
---------------------------
Площадь контакта большая → основной силовой узел.
1. Очистить поверхности от нагара/пыли после лазера.
2. Тонкий слой ПВА по mask (не затекать в окно и прорези front).
3. Совместить внешние контуры 1:1, окна по центру.
4. Прижать ровно (книга/грузы), выдержать по инструкции клея.

Критерий: кромки силуэта совпадают на ощупь; окно front
меньше окна mask со всех сторон (~{p.overlap} мм).


ЭТАП 2. U-спейсеры на оборот mask (КЛЕЙ)
---------------------------------------
1. Работать с оборота склеенной панели (mask снаружи снизу).
2. Приклеить spacer_left и spacer_right: внутренние кромки
   на расстоянии {p.pocket_w:.0f} мм друг от друга (карман по ширине).
3. Приклеить spacer_bottom: внутренний край замыкает карман
   по высоте {p.pocket_h:.0f} мм. ВЕРХ без полоски — щель для фото.
4. Проверить прямоугольность кармана угольником/фото-макетом.

Критерий: лист 100×150 мм входит сверху свободно, снизу
не проваливается.


ЭТАП 3. Back на спейсеры (КЛЕЙ)
------------------------------
1. Ориентация: keyhole у верхнего края; крест-пазы ближе к низу;
   круглый вырез пальца — справа сверху.
2. Клей только на торцы/пласти спейсеров (не в карман!).
3. Совместить back с центром кармана; прижать.

Критерий: сверху остаётся щель кармана; пазы ножки свободны
от клея.


ЭТАП 4. Подставка (БЕЗ клея)
---------------------------
Механика (исправлено относительно первой версии):
  • V-паз на back: ширина {p.slot_w:.2f} (=толщина фанеры),
    длина ~{p.leg_tab_w + 0.4:.1f} под шип ножки {p.leg_tab_w:.0f} мм.
  • H-паз на back: под шип распорки {p.brace_tab_w:.0f} мм.
  • На ножке — паз под тело распорки.

Сборка:
1. Вставить шип stand_leg в V-паз до упора (ножка перпендикулярна back).
2. Надеть brace пазом на ножку.
3. Завести шип brace в H-паз — угол зафиксирован.

Критерий: рамка стоит на столе с лёгким наклоном назад,
не падает вперёд от собственного веса.


ЭТАП 5. Фото
------------
Вставить {p.photo_w:.0f}×{p.photo_h:.0f} сверху в карман.
Достать: поддеть через вырез пальца на back.


АНАЛИЗ УСТОЙЧИВОСТИ (самопроверка)
----------------------------------
OK  Front↔mask: большая площадь → жёсткая «корка» ~6 мм.
OK  Спейсеры↔mask/back: полоски {p.spacer_w:.0f} мм по U —
    достаточно для кармана; верх открыт сознательно.
OK  Шип ножки {p.leg_tab_w:.0f} мм (раньше ошибочно был ~2.85 мм —
    слишком узкий, не держал бы).
OK  Распорка замыкает треугольник ножка–back–brace.
OK  База ножки {p.stand_base_w:.0f} мм.

Риски / оговорки:
• KERF под диодный лазер стартует с {p.kerf:.2f} мм (паз {p.slot_w:.2f}).
  Диод режет узко и иногда с конусом: если шип не лезет или болтается —
  сдвиньте kerf в params.py на ±0.05 и перережьте back + ножку + распорку.
• Карман глубиной {p.t:.0f} мм — только фотобумага (стекло не предусмотрено).
• Back совпадает с силуэтом front/mask — кромки корпуса вровень по всему контуру.
• Настенный подвес: keyhole. Подставка при этом снимается.


ФАЙЛЫ
-----
Лазер:   images/рамки/10кс15/лазер/*.svg
Схемы:   images/рамки/10кс15/инструкция/*.png
Пересчёт: python -m scripts.photo_frame
"""
