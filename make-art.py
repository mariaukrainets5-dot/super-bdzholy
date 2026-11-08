#!/usr/bin/env python3
"""Higgsfield originals in art-src/ -> game files in art/.
Sprites: flat green or magenta background is keyed out by distance to the corner colour,
cropped to the visible part, sized for the game. Backgrounds: resized webp.
Voice: art-src/voice/*.wav -> art/voice/*.mp3 with silence trimmed."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

root = Path(__file__).parent
src, out = root / "art-src", root / "art"
out.mkdir(exist_ok=True)
FF = "/opt/homebrew/opt/ffmpeg-full/bin/"

# name: longest side in pixels in the game file (about 2x of on-screen size for sharpness)
SPRITES = {"bee-me": 200, "bee-dad": 220, "bee-sis": 190, "queen": 360, "beetle": 150, "fast": 130,
           "big": 220, "armored": 170, "spitter": 160, "king": 380, "bear": 420, "man": 300,
           "device": 220, "vault": 360, "sunflower": 220}
BGS = ["bg-meadow", "bg-dusk", "bg-storm", "bg-night", "bg-kingdom", "bg-hive"]


def key(rgb):
    rgb = rgb.astype(float)
    c = np.concatenate([rgb[:10, :10].reshape(-1, 3), rgb[:10, -10:].reshape(-1, 3), rgb[-10:, :10].reshape(-1, 3), rgb[-10:, -10:].reshape(-1, 3)])
    bg = np.median(c, 0)
    d = np.sqrt(((rgb - bg) ** 2).sum(-1))
    alpha = np.clip((d - 60) / 55, 0, 1)
    green = bg[1] > bg[0] and bg[1] > bg[2]
    if green:  # despill green fringe
        g, m = rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2])
        rgb[..., 1] = np.where((g > m) & (alpha < 1), m + (g - m) * .2, g)
    else:  # magenta: red and blue both high, green low
        rb = np.minimum(rgb[..., 0], rgb[..., 2])
        spill = np.clip(rb - rgb[..., 1], 0, None)
        k = (alpha < 1)
        rgb[..., 0] = np.where(k, rgb[..., 0] - spill * .5, rgb[..., 0])
        rgb[..., 2] = np.where(k, rgb[..., 2] - spill * .5, rgb[..., 2])
    a = Image.fromarray((alpha * 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.7))
    img = Image.fromarray(np.clip(rgb, 0, 255).astype("uint8")).convert("RGBA")
    img.putalpha(a)
    return img


def sprites(only):
    info = {}
    for name, size in SPRITES.items():
        p = src / f"{name}.png"
        if not p.exists() or (only and name not in only):
            continue
        img = key(np.asarray(Image.open(p).convert("RGB")))
        box = img.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
        img = img.crop(box)
        img.thumbnail((size, size), Image.LANCZOS)
        img.save(out / f"{name}.webp", quality=86, alpha_quality=90, method=6)
        info[name] = [img.width, img.height]
        print(name, img.size, (out / f"{name}.webp").stat().st_size // 1024, "KB")
    old = json.loads((out / "sizes.json").read_text()) if (out / "sizes.json").exists() else {}
    old.update(info)
    (out / "sizes.json").write_text(json.dumps(old))


def backgrounds(only):
    for name in BGS:
        p = src / f"{name}.png"
        if not p.exists() or (only and name not in only):
            continue
        img = Image.open(p).convert("RGB").resize((1440, 900), Image.LANCZOS)
        img.save(out / f"{name}.webp", quality=74, method=6)
        print(name, (out / f"{name}.webp").stat().st_size // 1024, "KB")


def voices():
    vo = out / "voice"
    vo.mkdir(exist_ok=True)
    for f in sorted((src / "voice").glob("*.wav")):
        subprocess.run([FF + "ffmpeg", "-v", "error", "-y", "-i", str(f), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ac", "1", "-b:a", "64k", str(vo / (f.stem + ".mp3"))], check=True)
    print("voice", len(list(vo.glob("*.mp3"))))


if __name__ == "__main__":
    only = set(sys.argv[1:])
    sprites(only)
    backgrounds(only)
    if (src / "voice").exists() and (not only or "voice" in only):
        voices()
