#!/usr/bin/env python3
"""Embed the current sprites into loaf-showcase.html.

    python3 tools/build_showcase.py

Reads `loaf-showcase.src.html` and splices the real PNGs out of
`Sources/Loaf/Resources/sprites/` into it as data URIs, the same src-plus-
generated pattern `coat-study.src.html` uses. Run it after `blender/build_all.sh`
and the showcase is current; without it the page silently keeps whatever sprites
were embedded the day it was written, which is exactly the drift CLAUDE.md §3
bans between Blender and the app.

The state names and their file mappings below MUST match `LoafState.sprite`.
Blender names by camera angle, the app names by intent, and the showcase speaks
the app's vocabulary.
"""

import base64
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPRITES = ROOT / "Sources/Loaf/Resources/sprites"

# Rendered at every weight, because the tour shows her body changing. One frame each.
WEIGHTED = {"idle": "side_idle"}

# Normal weight only: (basename, frame count). A count of 1 is a still, `<base>.png`;
# anything higher is a cycle, `<base>1..N.png` - Sprites.frameCount's own rule.
CYCLES = {
    "walk":     ("walk", 8),
    "look":     ("front_idle", 1),
    "sit":      ("sit", 1),
    "sitSide":  ("sit_side", 1),
    "sleep":    ("sleep", 4),
    "stressed": ("stressed", 2),
    "jump":     ("jump", 6),
}


def uri(weight: str, stem: str) -> str:
    path = SPRITES / weight / f"{stem}.png"
    if not path.exists():
        sys.exit(f"missing sprite: {path.relative_to(ROOT)} — run blender/build_all.sh")
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def squircle(n: float = 5.0, points: int = 56) -> str:
    """macOS icon mask as a clip-path: the superellipse |x|^n + |y|^n = 1.

    In percentages, so one value works at any icon size. A border-radius rounded
    rect is visibly different on the shoulders of the corner at 64px.
    """
    pts = []
    for i in range(points):
        t = 2 * math.pi * i / points
        c, s = math.cos(t), math.sin(t)
        x = math.copysign(abs(c) ** (2 / n), c)
        y = math.copysign(abs(s) ** (2 / n), s)
        pts.append(f"{50 + 50 * x:.2f}% {50 + 50 * y:.2f}%")
    return "polygon(" + ",".join(pts) + ")"


def main() -> None:
    data, sizes = {}, []
    for state, stem in WEIGHTED.items():
        data[state] = {w: uri(w, stem) for w in ("lean", "normal", "chonk")}
        sizes.append((state, 3, sum(len(v) for v in data[state].values())))
    for state, (stem, n) in CYCLES.items():
        names = [stem] if n == 1 else [f"{stem}{i + 1}" for i in range(n)]
        data[state] = [uri("normal", nm) for nm in names]
        sizes.append((state, n, sum(len(v) for v in data[state])))

    src = (ROOT / "loaf-showcase.src.html").read_text()
    out = (src.replace("__SPRITES__", json.dumps(data))
              .replace("__SQUIRCLE__", squircle()))
    dest = ROOT / "loaf-showcase.html"
    dest.write_text(out)

    for state, n, size in sorted(sizes, key=lambda r: -r[2]):
        print(f"  {state:<9} {n:>2} frame(s)  {size / 1_000_000:5.2f} MB")
    print(f"\n{dest.name}: {dest.stat().st_size / 1_000_000:.2f} MB")


if __name__ == "__main__":
    main()
