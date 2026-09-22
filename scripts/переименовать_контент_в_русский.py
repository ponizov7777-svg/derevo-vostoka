#!/usr/bin/env python3
"""Переименование контентных путей в русские имена + обновление ссылок."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "images", ROOT / "assets", ROOT / "_inbox"]
TEXT_EXT = {".md", ".mdc", ".txt", ".json", ".js", ".py", ".html", ".css", ".yml", ".yaml"}

LAT_RE = re.compile(r"[A-Za-z]")
MULTI_UNDERSCORE = re.compile(r"_+")

WORD_MAP = {
    "chatgpt": "чатгпт",
    "image": "изображение",
    "photoshop": "фотошоп",
    "marketing": "маркетинг",
    "tiger": "тигр",
    "footprint": "след",
    "surgeon": "хирург",
    "clock": "часы",
    "heart": "сердце",
    "kidney": "почка",
    "liver": "печень",
    "square": "квадрат",
    "festina": "фестина",
    "lente": "ленте",
    "dr": "доктор",
    "ge": "гугл_земля",
    "pidan": "пидан",
    "stone": "камень",
    "word": "слово",
    "medal": "медаль",
    "heightmap": "карта_высот",
    "soft": "мягкий",
    "fog": "туман",
}

CHAR_MAP = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "г",
    "h": "х",
    "i": "и",
    "j": "й",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
}


def slugify_piece(piece: str) -> str:
    value = piece.lower()
    value = value.replace(" ", "_").replace("-", "_").replace(".", "_").replace(",", "_")
    value = MULTI_UNDERSCORE.sub("_", value).strip("_")
    if not value:
        return "файл"

    parts = [p for p in value.split("_") if p]
    out: list[str] = []
    for part in parts:
        if not LAT_RE.search(part):
            out.append(part)
            continue
        if part in WORD_MAP:
            out.append(WORD_MAP[part])
            continue
        converted = "".join(CHAR_MAP.get(ch, ch) for ch in part)
        out.append(converted)
    result = "_".join(out)
    result = MULTI_UNDERSCORE.sub("_", result).strip("_")
    return result or "файл"


def normalize_name(name: str, is_file: bool) -> str:
    if not LAT_RE.search(name):
        return name
    p = Path(name)
    if is_file:
        ext = p.suffix.lower()
        stem = p.stem
        return f"{slugify_piece(stem)}{ext}"
    return slugify_piece(name)


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    n = 2
    while True:
        if path.suffix:
            candidate = path.with_name(f"{path.stem}_{n}{path.suffix}")
        else:
            candidate = path.with_name(f"{path.name}_{n}")
        if not candidate.exists():
            return candidate
        n += 1


def collect_moves(base: Path) -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []
    entries = sorted(base.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for src in entries:
        if src.name.startswith("."):
            continue
        dst_name = normalize_name(src.name, is_file=src.is_file())
        if dst_name == src.name:
            continue
        dst = src.with_name(dst_name)
        if dst.exists() and dst.resolve() != src.resolve():
            dst = unique_path(dst)
        moves.append((src, dst))
    return moves


def apply_moves(moves: list[tuple[Path, Path]]) -> dict[str, str]:
    path_map: dict[str, str] = {}
    for src, dst in moves:
        if not src.exists():
            continue
        src_rel = src.relative_to(ROOT).as_posix()
        dst_rel = dst.relative_to(ROOT).as_posix()
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        path_map[src_rel] = dst_rel
    return path_map


def replace_links(path_map: dict[str, str]) -> int:
    changed = 0
    if not path_map:
        return changed
    keys = sorted(path_map, key=len, reverse=True)
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in (".git", "__pycache__", "node_modules", ".venv", "venv")):
            continue
        if path.suffix.lower() not in TEXT_EXT:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = text
        for old in keys:
            new = path_map[old]
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
    return changed


def main() -> None:
    all_moves: list[tuple[Path, Path]] = []
    for target in TARGETS:
        if target.exists():
            all_moves.extend(collect_moves(target))
    path_map = apply_moves(all_moves)
    updated_files = replace_links(path_map)
    print(f"Переименовано путей: {len(path_map)}")
    print(f"Обновлено текстовых файлов: {updated_files}")


if __name__ == "__main__":
    main()
