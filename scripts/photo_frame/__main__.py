"""Build laser SVGs, verify fit, write previews.

Usage:
  python -m scripts.photo_frame
  python -m scripts.photo_frame --verify-only
"""

from __future__ import annotations

import argparse
import sys

from .export_svg import export_all
from .params import DEFAULT, OUT_DIR, LASER_DIR
from .preview import export_previews
from .assembly_guide import export_assembly_guide
from .verify_fit import FitError, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)

    try:
        for line in verify(DEFAULT):
            print(line)
    except FitError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.verify_only:
        return 0

    # Drop obsolete part file from earlier revision
    obsolete = LASER_DIR / "brace_connector.svg"
    if obsolete.exists():
        obsolete.unlink()

    manifest = export_all(DEFAULT)
    print(f"Exported {len(manifest['parts'])} parts + nested sheet -> {OUT_DIR}")
    paths = export_previews(DEFAULT)
    for path in paths:
        print(f"Preview: {path}")
    for path in export_assembly_guide(DEFAULT):
        print(f"Guide: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
