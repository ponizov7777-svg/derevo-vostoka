#!/usr/bin/env python3
"""Build data for the souvenir generation landing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "images"
OUT = ROOT / "gallery-data.js"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
FINAL_CATEGORY = "чпу/финальные"

CATEGORY_LABELS = {
    FINAL_CATEGORY: "Финальные — для станка",
    "медали": "Медали — исходники",
    "медали/обработанные": "Медали — обработанные",
    "магниты": "Магниты ЧПУ — исходники",
    "магниты/обработанные": "Магниты ЧПУ — обработанные",
    "магниты/референсы": "Магниты ЧПУ — референсы",
    "чпу/кулоны": "Кулоны ЧПУ — исходники",
    "чпу/кулоны/референсы": "Кулоны ЧПУ — референсы",
    "чпу/кулоны/обработанные": "Кулоны ЧПУ — обработанные",
    "чпу/магниты": "Магниты ЧПУ",
    "чпу/магниты/обработанные": "Магниты ЧПУ — обработанные",
    "лазер-кулоны": "Кулоны лазер",
    "лазер-магниты": "Магниты лазер — общие",
    "лазер-магниты/В даль": "Магниты — В даль",
    "лазер-магниты/Насыпь": "Магниты — Насыпь",
    "лазер-магниты/Тринога велик": "Магниты — Тринога велик",
    "лазер-магниты/макеты": "Магниты лазер — макеты",
    "лазер-часы": "Лазерные часы",
    "мотивация": "Лазер — мотивашки",
    "мотивация/обработанные": "Лазер — обработанные",
    "мотивация/серия-восхождений": "Пидан — линейка восхождений",
    "мотивация/серия-восхождений/контуры": "Пидан — контуры SVG",
    "мотивация/векторы": "Лазер — векторы SVG",
    "мотивация/надписи": "Лазер — надписи",
    "витрины": "Витрины",
    "витрины/референсы": "Витрины — референсы",
    "витрины/плитки_200x300": "Витрины — плитки 200×300",
    "витрины/плитки_200x300/поля_лазера_300x200": "Витрины — поля лазера 300×200",
    "витрины/плитки_200кс300": "Витрины — плитки 200×300",
    "витрины/плитки_200кс300/поля_лазера_300кс200": "Витрины — поля лазера 300×200",
    "рамки/10x15/лазер": "Рамки 10×15 — лазер",
    "рамки/10x15/превью": "Рамки 10×15 — превью",
    "рамки/10x15/референсы": "Рамки 10×15 — референсы",
    "рамки/10кс15/лазер": "Рамки 10×15 — лазер",
    "рамки/10кс15/превью": "Рамки 10×15 — превью",
    "рамки/10кс15/референсы": "Рамки 10×15 — референсы",
    "подножье-пидана/лазер": "Подножье — лазер",
    "подножье-пидана/макеты": "Подножье — макеты",
    "сафари-парк/лазер": "Сафари-парк — лазер",
    "сафари-парк/чпу": "Сафари-парк — ЧПУ исходники",
    "сафари-парк/чпу/обработанные": "Сафари-парк — ЧПУ обработанные",
    "сафари-парк/чпу/референсы": "Сафари-парк — ЧПУ референсы",
    "сафари-парк/макеты": "Сафари-парк — макеты",
    "сафари-парк/референсы": "Сафари-парк — референсы",
    "3д-печать-пидан": "3Д-печать Пидан",
    "3д-печать-пидан/гугл-земля": "3Д — снимки Google Earth",
    "3д-печать-пидан/макеты": "3Д — макеты",
}

CONTEXT_META = {
    "базовый": "Базовый проект",
    "партнер_подножье": "Партнер — Подножье Пидана",
    "партнер_сафари": "Партнер — Сафари-парк",
}
TECH_META = {
    "чпу": "ЧПУ",
    "лазер": "Лазер",
    "смешанная": "Смешанная",
    "печать3д": "3Д-печать",
    "прочее": "Прочее",
}
PRODUCT_META = {
    "медали": "Медали",
    "магниты": "Магниты",
    "кулоны": "Кулоны",
    "витрины": "Витрины",
    "рамки": "Рамки",
    "часы": "Часы",
    "мотивация": "Мотивационные серии",
    "печать3д": "3Д-модели",
    "партнерская_серия": "Партнерская серия",
    "прочее": "Прочее",
}
STAGE_META = {
    "референсы": "Референсы",
    "исходники": "Исходники",
    "контуры": "Контуры/векторы",
    "обработанные": "Обработанные",
    "финальные": "Финальные",
    "макеты": "Макеты",
    "превью": "Превью",
    "инструкция": "Инструкция",
}

CONTEXT_ORDER = list(CONTEXT_META.keys())
TECH_ORDER = list(TECH_META.keys())
PRODUCT_ORDER = list(PRODUCT_META.keys())
STAGE_ORDER = list(STAGE_META.keys())

PRESETS = [
    {
        "id": "чпу_обработанные",
        "label": "ЧПУ → обработанные",
        "context": "all",
        "tech": "чпу",
        "product": "all",
        "stage": "обработанные",
        "unresolvedOnly": False,
    },
    {
        "id": "лазер_контуры",
        "label": "Лазер → контуры",
        "context": "all",
        "tech": "лазер",
        "product": "all",
        "stage": "контуры",
        "unresolvedOnly": False,
    },
    {
        "id": "партнеры_макеты",
        "label": "Партнеры → макеты",
        "context": "all",
        "tech": "all",
        "product": "партнерская_серия",
        "stage": "макеты",
        "unresolvedOnly": False,
    },
    {
        "id": "неразобранное",
        "label": "Неразобранное",
        "context": "all",
        "tech": "all",
        "product": "all",
        "stage": "all",
        "unresolvedOnly": True,
    },
]


def category_for(rel: Path) -> str:
    parent = rel.parent.as_posix()
    return "." if parent == "." else parent


def title_from_name(name: str) -> str:
    stem = Path(name).stem
    for suffix in (
        "_мягкий_туман_линии",
        "_мягкий_туман",
        "_карта_высот_обработанный",
        "_карта_высот",
        "_обработанный",
        "_soft_fog_lines",
        "_soft_fog",
        "_heightmap_processed",
        "_heightmap",
        "_processed",
    ):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem.replace("_", " ").strip()


def is_processed(path: Path, category: str, is_final: bool) -> bool:
    if is_final:
        return True
    if "обработанные" in Path(category).parts or "processed" in Path(category).parts:
        return True
    name = path.name
    return (
        name.endswith("_обработанный.png")
        or name.endswith("_processed.png")
        or "_обработанный." in name
        or "_processed." in name
        or "_мягкий_туман" in name
        or "_soft_fog" in name
    )


def detect_context(category: str) -> str:
    if category == "подножье-пидана" or category.startswith("подножье-пидана/"):
        return "партнер_подножье"
    if category == "сафари-парк" or category.startswith("сафари-парк/"):
        return "партнер_сафари"
    return "базовый"


def detect_tech(category: str, parts: tuple[str, ...]) -> str:
    if category == "3д-печать-пидан" or category.startswith("3д-печать-пидан/"):
        return "печать3д"
    if "чпу" in parts or category.startswith("медали") or category.startswith("чпу/") or category.startswith("магниты"):
        return "чпу"
    if "лазер" in parts or category.startswith("лазер-") or category.startswith("мотивация") or category.startswith("витрины") or category.startswith("рамки"):
        return "лазер"
    if "макеты" in parts:
        return "смешанная"
    return "прочее"


def detect_product(category: str) -> str:
    if category.startswith("медали"):
        return "медали"
    if category.startswith("магниты") or category.startswith("чпу/магниты") or category.startswith("лазер-магниты"):
        return "магниты"
    if category.startswith("чпу/кулоны") or category.startswith("лазер-кулоны"):
        return "кулоны"
    if category.startswith("витрины"):
        return "витрины"
    if category.startswith("рамки"):
        return "рамки"
    if category.startswith("лазер-часы"):
        return "часы"
    if category.startswith("мотивация"):
        return "мотивация"
    if category.startswith("3д-печать-пидан"):
        return "печать3д"
    if category.startswith("подножье-пидана") or category.startswith("сафари-парк"):
        return "партнерская_серия"
    return "прочее"


def detect_stage(category: str, parts: tuple[str, ...], is_final: bool, path: Path) -> str:
    if is_final:
        return "финальные"
    if "референсы" in parts:
        return "референсы"
    if "инструкция" in parts:
        return "инструкция"
    if "превью" in parts:
        return "превью"
    if "макеты" in parts:
        return "макеты"
    if "обработанные" in parts:
        return "обработанные"
    if "контуры" in parts or "векторы" in parts:
        return "контуры"
    if path.suffix.lower() == ".svg":
        return "контуры"
    return "исходники"


def make_option_list(items: list[dict], key: str, meta: dict[str, str], order: list[str]) -> list[dict]:
    counts: dict[str, int] = {}
    for item in items:
        value = item[key]
        counts[value] = counts.get(value, 0) + 1
    sort_map = {name: idx for idx, name in enumerate(order)}
    options = [
        {
            "id": opt_id,
            "label": meta.get(opt_id, opt_id),
            "count": count,
        }
        for opt_id, count in counts.items()
    ]
    options.sort(key=lambda item: (sort_map.get(item["id"], 999), item["label"]))
    return options


def category_list(items: list[dict]) -> list[dict]:
    counts: dict[str, dict] = {}
    for item in items:
        cat = item["category"]
        info = counts.setdefault(
            cat,
            {
                "id": cat,
                "label": item["categoryLabel"],
                "count": 0,
            },
        )
        info["count"] += 1
    return sorted(counts.values(), key=lambda item: item["label"])


def build_gallery_payload(now_iso: str) -> dict:
    if not IMAGES.is_dir():
        raise SystemExit(f"Not found: {IMAGES}")

    items: list[dict] = []
    for path in sorted(IMAGES.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if path.name in {".gitkeep", ".пусто"}:
            continue

        rel = path.relative_to(IMAGES)
        category = category_for(rel)
        parts = Path(category).parts
        stat = path.stat()
        is_final = category == FINAL_CATEGORY

        context = detect_context(category)
        tech = detect_tech(category, parts)
        product = detect_product(category)
        stage = detect_stage(category, parts, is_final, path)
        processed = is_processed(path, category, is_final)
        category_label = CATEGORY_LABELS.get(category, category)
        unresolved = product == "прочее" or tech == "прочее" or category_label == category

        items.append(
            {
                "id": rel.as_posix(),
                "src": f"images/{rel.as_posix()}",
                "name": path.name,
                "title": title_from_name(path.name),
                "category": category,
                "categoryLabel": category_label,
                "context": context,
                "contextLabel": CONTEXT_META.get(context, context),
                "tech": tech,
                "techLabel": TECH_META.get(tech, tech),
                "product": product,
                "productLabel": PRODUCT_META.get(product, product),
                "stage": stage,
                "stageLabel": STAGE_META.get(stage, stage),
                "unresolved": unresolved,
                "final": is_final,
                "processed": processed,
                "mtime": int(stat.st_mtime),
                "size": int(stat.st_size),
            }
        )

    contexts = make_option_list(items, "context", CONTEXT_META, CONTEXT_ORDER)
    techs = make_option_list(items, "tech", TECH_META, TECH_ORDER)
    products = make_option_list(items, "product", PRODUCT_META, PRODUCT_ORDER)
    stages = make_option_list(items, "stage", STAGE_META, STAGE_ORDER)
    categories = category_list(items)

    availability_by_context: dict[str, dict] = {}
    for context in contexts:
        context_id = context["id"]
        scoped = [item for item in items if item["context"] == context_id]
        availability_by_context[context_id] = {
            "tech": make_option_list(scoped, "tech", TECH_META, TECH_ORDER),
            "product": make_option_list(scoped, "product", PRODUCT_META, PRODUCT_ORDER),
            "stage": make_option_list(scoped, "stage", STAGE_META, STAGE_ORDER),
            "categories": category_list(scoped),
        }

    unresolved_items = [item for item in items if item["unresolved"]]
    unresolved_categories = category_list(unresolved_items)

    return {
        "generatedAt": now_iso,
        "root": "images",
        "total": len(items),
        "categories": categories,
        "facets": {
            "context": contexts,
            "tech": techs,
            "product": products,
            "stage": stages,
            "availabilityByContext": availability_by_context,
            "presets": PRESETS,
        },
        "unresolved": {
            "count": len(unresolved_items),
            "categories": unresolved_categories,
        },
        "items": items,
    }


def main() -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    gallery_payload = build_gallery_payload(now_iso)
    js = (
        "/* Auto-generated by scripts/build_gallery.py — do not edit by hand */\n"
        f"window.GALLERY_DATA = {json.dumps(gallery_payload, ensure_ascii=False, indent=2)};\n"
    )
    OUT.write_text(js, encoding="utf-8")
    print(f"Wrote {OUT.name}: {gallery_payload['total']} images")


if __name__ == "__main__":
    main()
