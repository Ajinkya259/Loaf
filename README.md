# Loaf

A voxel cat who lives on your macOS dock. **How much work you have queued changes
her body; what your machine is doing changes her mood.**

<p align="center">
  <img src="docs/tour.gif" width="880" alt="Loaf walking along the macOS dock, sleeping in the corner, and bristling when the CPU spikes">
</p>

She's **generated, not drawn** — every sprite comes out of a headless Blender
script, so changing her look is one command, not a re-draw.

## The two signals

**Task load → her body.** Incomplete reminders in Reminders.app make her fatter.
Nothing pending and she's lean.

<p align="center">
  <img src="docs/weights.png" width="560" alt="Loaf at three body weights: lean, normal and chonk">
</p>

**Machine load → her posture.** CPU or memory under pressure and she stops,
hunches and bristles. Step away from the keyboard and she curls up and sleeps.
The two are independent, so she can be fat *and* frightened — which is the
"too much to do and the laptop is dying" case.

<p align="center">
  <img src="docs/states.png" width="880" alt="Loaf's eight poses: idle, walk, sit, sleep, stressed and look">
</p>

Plus: a paw drops from the menu bar when your Mac wakes and every 1–2 hours as a
water-break nudge; she's draggable; and she mutters LLM-generated one-liners
while idle, falling back to a fixed pool with no API key or on any network
hiccup.

## Install

```bash
git clone https://github.com/Ajinkya259/Loaf
cd Loaf
make run          # build and launch from source
make dist         # or: a real dist/Loaf.app + dist/Loaf.dmg
```

**macOS 14+ and Swift 6 command-line tools. Nothing else** — no third-party
packages, no CocoaPods, no npm, just AppKit, SwiftUI and a folder of PNGs. She
runs all day, so every dependency would be memory held the whole time and
supply-chain surface for something that needs none.

The packaged `.app` is ad-hoc signed (no Apple Developer ID here), so macOS
blocks the first launch — right-click → Open once, or
`xattr -dr com.apple.quarantine dist/Loaf.app`.

Everything is controlled from the 🐾 menu-bar item: **Autopilot** (the default),
**Weight**, **Actions**, **Settings**.

**One permission requested** — Reminders, for task load. No Accessibility, no
Calendar. Deny it and she keeps whatever weight the menu last set. Footprint is
~2% CPU and ~13 MB standing still, ~8% and ~30 MB while she's walking.

## How it works

Two independent halves.

**The art pipeline** (`blender/`) renders every pose at every body weight
straight into `Sources/Loaf/Resources/sprites/<weight>/` — no hand-drawing, and
no copy step between renderer and app. 8 states across 3 body weights: 72 sprite
files, because the cycles count too (walk is 8 frames, jump 6, sleep 4).

**The app** (`Sources/Loaf/`) is a SwiftPM executable: a borderless AppKit window
with a SwiftUI character view, running as a menu-bar accessory with no dock icon
of its own — she *is* the icon. A state machine strolls her along the dock for
~4 minutes before she rests, walks to a corner, sits, and eventually sleeps.
Three edge-triggered monitors watch the outside world: CPU and memory pressure,
keyboard/mouse idle, and incomplete Reminders.

```bash
blender/build_all.sh   # regenerate every sprite (needs Blender 5.2)
```

Always run that script rather than one build script alone — the poses have
drifted apart from each other twice that way.

| Where to read more | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | the design reference — palette, build rules, the state model, and every failure class that got us here |
| [`SPRITE_CONTRACT.md`](SPRITE_CONTRACT.md) | the exact Blender ↔ app interface: canvas size, ground line, naming |
| [`CONTEXT.md`](CONTEXT.md) | where things stand and what's next |

`loaf-showcase.html` is a self-contained tour of every state — a 1:1 diorama of a
1280×800 Mac, no server and no external requests. Regenerate it with
`python3 tools/build_showcase.py`, and edit `loaf-showcase.src.html` rather than
the built file.

## Known gaps

- The OpenRouter key reads from `LOAF_OPENROUTER_KEY`, not yet Keychain — fine
  for a terminal launch, but not for "Launch at login", which has no shell
  environment. `Keychain.swift` exists and is already checked as a fallback.
- No notarization on the packaged `.app` — that needs an Apple Developer Program
  membership this project doesn't have.

## Credits

[`lil-cleo`](https://github.com/ankitaggarwal/lil-cleo) (MIT) — the load-bearing
reference for the desktop-pet architecture; `blender/catlib.py` forks its
`bricklib`. [`three.js`](https://threejs.org) (MIT) — vendored in `web/` for the
live-rig previewer, a dev tool that ships with nothing.

## License

MIT — see [LICENSE](LICENSE). A personal project, public so anyone can build
their own cat.
