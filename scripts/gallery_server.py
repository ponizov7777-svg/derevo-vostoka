#!/usr/bin/env python3
"""Local gallery server: static files + move-to-final API."""

from __future__ import annotations

import json
import mimetypes
import shutil
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "images"
FINAL_DIR = IMAGES / "чпу" / "финальные"
BUILD_SCRIPT = ROOT / "scripts" / "build_gallery.py"
DEFAULT_PORT = 8765


def rebuild_gallery() -> None:
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=True, cwd=ROOT)


def safe_image_path(rel: str) -> Path:
    rel = unquote(rel.replace("\\", "/").lstrip("/"))
    if rel.startswith("images/"):
        rel = rel[len("images/") :]
    path = (IMAGES / rel).resolve()
    if not str(path).startswith(str(IMAGES.resolve())):
        raise ValueError("Path outside images/")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        raise ValueError("Not an image file")
    return path


def unique_dest(name: str) -> Path:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    dest = FINAL_DIR / name
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    n = 1
    while True:
        candidate = FINAL_DIR / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def move_to_final(src_rel: str) -> dict:
    src = safe_image_path(src_rel)
    if not src.is_file():
        raise FileNotFoundError(f"Not found: {src_rel}")
    final_resolved = FINAL_DIR.resolve()
    if str(src.resolve()).startswith(str(final_resolved)):
        raise ValueError("Already in final folder")

    dest = unique_dest(src.name)
    shutil.move(str(src), str(dest))
    rebuild_gallery()
    rel = dest.relative_to(IMAGES).as_posix()
    return {
        "ok": True,
        "src": f"images/{src_rel.replace('images/', '')}",
        "dest": f"images/{rel}",
        "name": dest.name,
    }


class GalleryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        if args and isinstance(args[0], str) and args[0].startswith("GET /api/"):
            return
        super().log_message(fmt, *args)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/health":
            self._json(200, {"ok": True, "finalDir": "images/чпу/финальные"})
            return
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/move-to-final":
            self._handle_move()
            return
        if path == "/api/rebuild":
            try:
                rebuild_gallery()
                self._json(200, {"ok": True})
            except subprocess.CalledProcessError as exc:
                self._json(500, {"ok": False, "error": str(exc)})
            return
        self.send_error(404)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_move(self) -> None:
        try:
            data = self._read_json()
            src = data.get("src", "")
            if not src:
                self._json(400, {"ok": False, "error": "Missing src"})
                return
            result = move_to_final(src)
            self._json(200, result)
        except FileNotFoundError as exc:
            self._json(404, {"ok": False, "error": str(exc)})
        except ValueError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    rebuild_gallery()
    server = ThreadingHTTPServer(("127.0.0.1", port), GalleryHandler)
    print(f"Gallery: http://127.0.0.1:{port}/index.html")
    print(f"Final folder: {FINAL_DIR.relative_to(ROOT)}")
    print("Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
