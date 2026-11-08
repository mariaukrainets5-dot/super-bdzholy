#!/usr/bin/env python3
"""Wraps index.html (Artifact format, no document tags) into docs/index.html for GitHub Pages,
copies the game art and voice next to it and makes the home-screen icon and manifest."""
import json
import shutil
from pathlib import Path

from PIL import Image

root = Path(__file__).parent
docs = root / "docs"
docs.mkdir(exist_ok=True)
page = (root / "index.html").read_text(encoding="utf-8")
cut = page.index('<canvas id="cv">')
head, body = page[:cut], page[cut:]
extra = """<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="description" content="Детская игра: пчёлы охраняют мёд Королевы от жуков, медведя, усыпителя и Короля Жуков.">
<meta name="theme-color" content="#1c1530">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Супер Бджолы">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<style>:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }</style>
"""
(docs / "index.html").write_text(
    '<!doctype html>\n<html lang="ru">\n<head>\n' + head + extra + "</head>\n<body>\n" + body + "</body>\n</html>\n",
    encoding="utf-8",
)
if (docs / "art").exists():
    shutil.rmtree(docs / "art")
shutil.copytree(root / "art", docs / "art", ignore=shutil.ignore_patterns("*.json"))

# Icon: the hero bee on a warm honey circle.
bee = Image.open(root / "art" / "bee-me.webp").convert("RGBA")
for size in (180, 192, 512):
    icon = Image.new("RGBA", (size, size), (255, 178, 30, 255))
    b = bee.copy()
    b.thumbnail((int(size * .86), int(size * .86)), Image.LANCZOS)
    icon.alpha_composite(b, ((size - b.width) // 2, (size - b.height) // 2))
    icon.convert("RGB").save(docs / f"icon-{size}.png")
(docs / "manifest.webmanifest").write_text(json.dumps({
    "name": "Супер Бджолы", "short_name": "Бджолы", "start_url": "./", "display": "fullscreen",
    "orientation": "landscape", "background_color": "#1c1530", "theme_color": "#1c1530",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]}, ensure_ascii=False, indent=1), encoding="utf-8")
(docs / ".nojekyll").write_text("")
print("docs/ ready")
