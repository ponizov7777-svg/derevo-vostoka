#!/usr/bin/env python3
"""ONE-SHOT, already applied (2026): English folders/filenames → Russian.

Kept in scripts/_archive/ for history. Do not run against the current tree.
Dry-run by default if invoked.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IMAGES = ROOT / "images"
ASSETS = ROOT / "assets"

# Deepest-first: rename children before parents
FOLDER_MAP = {
    "ascents-series": "серия-восхождений",
    "google-earth": "гугл-земля",
    "display-concepts": "витрины",
    "laser-magnets": "лазер-магниты",
    "laser-pendants": "лазер-кулоны",
    "podnozhye-pidana": "подножье-пидана",
    "3d-print-pidan": "3д-печать-пидан",
    "pendants": "кулоны",
    "processed": "обработанные",
    "reference": "референсы",
    "mockups": "макеты",
    "contours": "контуры",
    "motivation": "мотивация",
    "magnets": "магниты",
    "medals": "медали",
    "final": "финальные",
    "cnc": "чпу",
    "svg": "svg",
}

# Longest phrases first (applied to stem only)
PHRASE_MAP = [
    ("gory_zovut_i_ya_dolzhen_idti", "горы_зовут_и_я_должен_идти"),
    ("tropa_luchshiy_psiholog", "тропа_лучший_психолог"),
    ("nogi_gudyat_dusha_poyot", "ноги_гудят_душа_поёт"),
    ("turisticheskiy_zheton", "туристический_жетон"),
    ("pokoritel_vershiny", "покоритель_вершины"),
    ("tired_seated_person", "усталый_сидящий"),
    ("top_lug_for_hole", "ушко_под_отверстие"),
    ("balanced_boulder", "баланс_валун"),
    ("souvenir_badge", "сувенирный_значок"),
    ("same_design_phrase", "тот_же_дизайн_фраза"),
    ("full_phrase_magnet", "магнит_полная_фраза"),
    ("motivation_magnet", "магнит_мотивация"),
    ("hiker_phrase", "турист_фраза"),
    ("bike_phrase", "велик_фраза"),
    ("rockpile_phrase", "насыпь_фраза"),
    ("magnet_sample", "магнит_образец"),
    ("magnet_test", "магнит_тест"),
    ("table_souvenir", "настольный_сувенир"),
    ("print_style_reference", "стиль_печати_референс"),
    ("soft_fog_lines", "мягкий_туман_линии"),
    ("heightmap_processed", "карта_высот_обработанный"),
    ("heightmap_soft_fog", "карта_высот_мягкий_туман"),
    ("display_board_labels", "доска_витрина_подписи"),
    ("display_board", "доска_витрина"),
    ("display_concept", "концепт_витрины"),
    ("trail_to_summit", "тропа_к_вершине"),
    ("trail_medal_rack_top", "тропа_рейка_медалей_верх"),
    ("trail_medal_finish", "тропа_медали_финиш"),
    ("leather_trailhead", "кожа_старт_тропы"),
    ("trail_side_medal_rack", "тропа_рейка_медалей_сбоку"),
    ("realistic_pidan_silhouette", "реалистичный_пидан_силуэт"),
    ("stone_cairn", "каменная_тур"),
    ("stone_word", "слово_на_камне"),
    ("pine_forest_style", "стиль_сосновый_лес"),
    ("pine_style", "стиль_сосна"),
    ("font_ref", "шрифт_реф"),
    ("silhouette_close", "силуэт_крупно"),
    ("silhouette_wide", "силуэт_широкий"),
    ("summit_satellite", "вершина_спутник"),
    ("silhouette_source", "силуэт_исходник"),
    ("all_magnets_fridge", "все_магниты_холодильник"),
    ("cnc_laser_magnets_fridge_arranged", "чпу_лазер_магниты_холодильник_расстановка"),
    ("cnc_pokoril_stone_word", "чпу_покорил_слово_на_камне"),
    ("magnets_on_fridge_laser_wood", "магниты_на_холодильнике_лазер_дерево"),
    ("pokoryay_ne_gory", "покоряй_не_горы"),
    ("pokoryay_sebya", "покоряй_себя"),
    ("luchshiy_vid", "лучший_вид"),
    ("brat_vershiny", "брат_вершины"),
    ("gory_zovut", "горы_зовут"),
    ("vyshe_gor", "выше_гор"),
    ("tam_gde_doroga", "там_где_дорога"),
    ("idi_k_vershine", "иди_к_вершине"),
    ("kazhdyy_shag_tebya", "каждый_шаг_тебя"),
    ("doroga_priklyuchenie", "дорога_приключение"),
    ("dusha_po_rostu", "душа_по_росту"),
    ("voskhozhdeniya", "восхождения"),
    ("voskhozhdenie", "восхождение"),
    ("voskhozhdeniy", "восхождений"),
    ("sled_tigra", "след_тигра"),
    ("derevo_vostoka", "дерево_востока"),
    ("spil_dereva", "спил_дерева"),
    ("triangle_stones", "треугольные_камни"),
    ("mountain_relief", "рельеф_горы"),
    ("ultra_smooth", "ультра_гладкий"),
    ("plain_rim", "гладкий_обод"),
    ("wide_plain", "широкий_гладкий"),
    ("flags_tripod", "флаги_тринога"),
    ("hiker_panorama", "турист_панорама"),
    ("order_test", "тест_заказа"),
    ("laser_series", "лазер_серия"),
    ("laser_template", "лазер_шаблон"),
    ("laser_bw", "лазер_чб"),
    ("enamel_mug", "эмалированная_кружка"),
    ("wood_magnet", "деревянный_магнит"),
    ("cafe_interior", "интерьер_кафе"),
    ("tourist_forest", "турист_лес"),
    ("lukyanovka_view", "лукьяновка_вид"),
    ("summit_close", "вершина_крупно"),
    ("pendant_ref", "кулон_реф"),
    ("pendant", "кулон"),
    ("squirrel", "белка"),
    ("fox", "лиса"),
    ("hiker", "турист"),
    ("bike", "велик"),
    ("rockpile", "насыпь"),
    ("tripod", "тринога"),
    ("boulder", "валун"),
    ("balanced", "баланс"),
    ("phrase", "фраза"),
    ("magnets", "магниты"),
    ("magnet", "магнит"),
    ("medal", "медаль"),
    ("heightmap", "карта_высот"),
    ("soft_fog", "мягкий_туман"),
    ("processed", "обработанный"),
    ("source", "исходник"),
    ("reference", "референс"),
    ("template", "шаблон"),
    ("contour", "контур"),
    ("series", "серия"),
    ("variant", "вариант"),
    ("concept", "концепт"),
    ("sample", "образец"),
    ("test", "тест"),
    ("laser", "лазер"),
    ("fridge", "холодильник"),
    ("arranged", "расстановка"),
    ("wood", "дерево"),
    ("summit", "вершина"),
    ("topdown", "сверху"),
    ("close", "крупно"),
    ("view", "вид"),
    ("silhouette", "силуэт"),
    ("trail", "тропа"),
    ("finish", "финиш"),
    ("rack", "рейка"),
    ("side", "сбоку"),
    ("board", "доска"),
    ("labels", "подписи"),
    ("label", "подпись"),
    ("title", "заголовок"),
    ("kamni", "камни"),
    ("krutoy", "крутой"),
    ("vodopad", "водопад"),
    ("podnozhye", "подножье"),
    ("keychain", "брелок"),
    ("stone", "камень"),
    ("wide", "широкий"),
    ("flags", "флаги"),
    ("panorama", "панорама"),
    ("ascents", "восхождения"),
    ("pyro", "пиро"),
    ("pokoril", "покорил"),
    ("censored_no_schastliv", "цензура_не_счастлив"),
    ("zae", "зае"),
    ("teh", "тех"),
    ("bw", "чб"),
    ("cnc", "чпу"),
    ("plaque", "табличка"),
    ("full_text", "полный_текст"),
    ("path", "тропа"),
    ("clean", "чистый"),
    ("pidan", "пидан"),
]

MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def translate_stem(stem: str) -> str:
    s = stem
    # Google Earth frames: ge_01, ge_21_...
    s = re.sub(r"^ge_", "гугл_земля_", s)
    for eng, rus in PHRASE_MAP:
        s = s.replace(eng, rus)
    # collapse duplicate underscores
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def translate_filename(name: str) -> str:
    p = Path(name)
    if p.suffix.lower() not in MEDIA_EXT:
        return name
    if p.name.startswith("_") or p.name.startswith("."):
        return name
    new_stem = translate_stem(p.stem)
    if new_stem == p.stem:
        return name
    return f"{new_stem}{p.suffix.lower()}"


def plan_file_renames(base: Path) -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in MEDIA_EXT:
            continue
        new_name = translate_filename(path.name)
        if new_name != path.name:
            moves.append((path, path.with_name(new_name)))
    return moves


def plan_folder_renames(base: Path) -> list[tuple[Path, Path]]:
    dirs = [p for p in base.rglob("*") if p.is_dir()]
    dirs.sort(key=lambda p: len(p.parts), reverse=True)
    moves: list[tuple[Path, Path]] = []
    for d in dirs:
        new_name = FOLDER_MAP.get(d.name)
        if new_name and new_name != d.name:
            moves.append((d, d.with_name(new_name)))
    return moves


def plan_assets() -> list[tuple[Path, Path]]:
    mapping = {
        "podnozhye_pidana_logo.png": "подножье_пидана_логотип.png",
        "tiger_paw_reference.png": "лапа_тигра_референс.png",
    }
    moves = []
    for old, new in mapping.items():
        src = ASSETS / old
        if src.exists():
            moves.append((src, ASSETS / new))
    return moves


def apply_moves(moves: list[tuple[Path, Path]], dry_run: bool) -> int:
    done = 0
    for src, dst in moves:
        if dst.exists() and dst.resolve() != src.resolve():
            print(f"SKIP collision: {src} -> {dst}", file=sys.stderr)
            continue
        print(f"{'[dry] ' if dry_run else ''}{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        done += 1
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually rename")
    args = ap.parse_args()
    dry = not args.apply

    file_moves = plan_file_renames(IMAGES)
    asset_moves = plan_assets()
    folder_moves = plan_folder_renames(IMAGES)

    print(f"Files: {len(file_moves)}, assets: {len(asset_moves)}, folders: {len(folder_moves)}")
    n = 0
    n += apply_moves(file_moves, dry)
    n += apply_moves(asset_moves, dry)
    n += apply_moves(folder_moves, dry)
    print(f"Done: {n}")


if __name__ == "__main__":
    main()
