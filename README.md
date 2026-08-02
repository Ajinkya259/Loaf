# Loaf

A voxel cat who lives on your macOS dock as a desktop pet — a status indicator
with a personality. How much work is queued changes her body. What your machine
is doing changes her mood.

<p align="center">
  <img src="docs/screenshot.png" width="480" alt="Loaf, idle, shown on both a light and a dark background">
</p>

- **Task load → body size, live.** More incomplete reminders in Reminders.app →
  she gets fatter. Nothing pending → lean and chill.
- **System load → posture.** CPU or memory struggling → she stops, hunches,
  bristles. Recovers → back to normal.
- **You step away → she sleeps early.** No keyboard or mouse input for a few
  minutes and she settles down, rather than pacing the dock all night.
- **Your Mac wakes up → she waves.** A paw drops down from the menu bar as a
  "good morning."
- **Every 1-2 hours, a water-break nudge** — the same paw drop, paired with a
  reminder to go drink some water.
- **LLM-generated one-liners while she's idle** — sarcastic, a little bored,
  aware of her actual weight and whether the machine's struggling. Falls back
  to a curated fixed pool with no API key set, or on any network hiccup — no
  visible difference in behaviour either way.
- **Hover or click her directly and she greets you** — an immediate "Hey." and
  a glance in your direction, rather than waiting for the next idle check.
- Draggable. Pick her up and she wakes and looks at you; let go and she falls
  back to the dock instead of teleporting.
- **"Launch at login"** in the menu (once installed as a real `.app`), so a
  reboot doesn't silently end her until you remember to relaunch.

She's **generated, not drawn** — every sprite comes out of a headless Blender
script (`blender/build_cat*.py`). Nothing here is hand-painted, so changing her
look is one command, not a re-draw.

## Quick start

**Run from source** (for development — rebuilds on every launch):

```bash
git clone https://github.com/Ajinkya259/Loaf
cd Loaf
make run
```

**Install properly** — a real `Loaf.app` you drag to `/Applications`:

```bash
make app       # dist/Loaf.app only
make dist      # dist/Loaf.app + dist/Loaf.dmg
```

Ad-hoc signed (no Apple Developer ID on this machine yet), so on first launch
macOS will refuse to open it normally — right-click → Open once, or
`xattr -dr com.apple.quarantine dist/Loaf.app`.

Either way, she appears on the dock and everything is controlled from the 🐾
menu-bar item: **Autopilot** (the default — she does everything on her own),
**Weight** (task load, still hand-set — see [Status](#status)), **Actions**
(pin a specific pose or gesture by hand), **Settings** (display, size,
reaction toggles).

```bash
make run                        # build + launch from source
make stop                       # quit her
LOAF_STATE=sit make run         # pin one state for inspection instead of wandering
```

**Requirements:** macOS 14+, Xcode / Swift 6 command-line tools. Nothing else —
see [Zero dependencies](#zero-dependencies) below. Blender is only needed if
you're regenerating the art (see [Regenerating the art](#regenerating-the-art)).

## How it works

Two independent pieces:

1. **The art pipeline** (`blender/`) — headless Blender scripts build a voxel
   cat, rig it, and render every pose × body-weight combination straight into
   `Sources/Loaf/Resources/sprites/<weight>/`. There's no hand-drawing and no
   copy step between renderer and app.
2. **The app** (`Sources/Loaf/`) — a SwiftPM executable: an AppKit borderless
   window plus a SwiftUI character view, running as a menu-bar accessory app
   (no dock icon of its own — she *is* the icon). A small state machine
   (`AppDelegate+Wander.swift`) makes her stroll the dock (~4 minutes) before
   pausing, walking to a corner, sitting, and eventually sleeping. Three
   edge-triggered monitors watch the outside world: `SystemMonitor.swift`
   (CPU + memory pressure → stressed), `UserIdleMonitor.swift` (no
   keyboard/mouse input → sleeps early) — both permission-free — and
   `TaskLoadMonitor.swift` (incomplete Reminders → her weight, the one
   permission the app asks for). `PawDropView.swift` and
   `SpeechBubbleView.swift` are separate overlays layered above whatever pose
   she's in, not poses themselves — a "Paw" greeting on system wake and every
   1-2h as a water-break nudge, and speech bubbles either idle-triggered or
   immediate on hover/click. `LLMBrain.swift` (OpenRouter) generates the
   idle-triggered lines when an API key is set, falling back to
   `SpeechBubbleView`'s fixed pool otherwise.

8 states currently have art — idle, walk, look, sit (front), sit (profile),
sleep, stressed, jump — each rendered at 3 body weights, 72 sprites total.

For the full design reasoning (why the camera never moves, why weight is a
directory and not a filename, why sleep gets a drifting "z" instead of a
different pose, and every failure mode that got us here), see:

| File | What's in it |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | the design reference — palette, build rules, the state model, hard-won failure classes |
| [`CONTEXT.md`](CONTEXT.md) | where things stand right now and what's next, for picking the project back up cold |
| [`SPRITE_CONTRACT.md`](SPRITE_CONTRACT.md) | the exact Blender ↔ app interface (canvas size, ground line, naming) |

### Zero dependencies

No third-party Swift packages, no CocoaPods, no npm. Just AppKit, SwiftUI, and
a folder of PNGs. She runs all day, every day, so every dependency would be
memory held the whole time, launch cost on every login, and supply-chain
surface for something that doesn't need it.

**Zero third-party dependencies** stays true; **one permission requested** now —
Reminders, for task load (no Accessibility, no Calendar, no network). Deny it and
she just keeps using whatever weight the menu last set, no re-prompting.

### Resource footprint

Measured live on an M-series Mac, current build:

| | CPU | Memory (RSS) |
|---|---|---|
| Pinned / holding still | ~1.5–2% | ~13 MB |
| Wandering (default behaviour) | ~7–9% | ~25–30 MB |

CPU varies with machine load and display refresh rate — the character view
redraws on every frame it's animating, so a busy stroll costs more than
standing still. No polling loops, and nothing that runs when she isn't
visible. One exception to "no background network activity" as of `LLMBrain.
swift`: roughly every 1.5–4 minutes, one small request to OpenRouter for a
speech-bubble line, only while she's idle and only if an API key is set.
Nothing else in the app makes network calls.

### Regenerating the art

```bash
blender/build_all.sh
```

Needs Blender 5.2.0 at `/Applications/Blender.app/Contents/MacOS/Blender`
(`brew install --cask blender`). Rebuilds every pose at every body weight and
regenerates the review contact sheets in `blender/previews/`. Always run this
script — never a single build script alone (see `CLAUDE.md` §3 for why: the
poses have drifted apart from each other twice that way).

### Packaging the `.app`

```bash
tools/package.sh          # dist/Loaf.app + dist/Loaf.dmg
tools/package.sh app      # just the .app
```

Release build, an icon generated from `front_idle.png` (her front-facing,
"personality" angle, not profile), and ad-hoc code signing. Picks up a real
"Developer ID Application" identity from the keychain automatically if one's
ever added (`LOAF_SIGN_ID` to override) — until then, ad-hoc.

## Status

Working today: dock stroll → dwell → corner sit → sleep, jumps, dragging,
CPU/memory-driven stress reactions, sleeps early when you step away, a paw
greeting on system wake and every 1-2h as a water-break nudge, LLM-generated
speech bubbles (`LLMBrain.swift`, OpenRouter, falls back to a fixed pool),
an immediate greeting on hover/click, task load driven live by Reminders,
launch at login, a real installable `.app`, 72 sprites across 3 weights and
8 states.

Not done yet:

- **The OpenRouter key lives in `LOAF_OPENROUTER_KEY` for now**, not
  Keychain — fine for a terminal-launched dev build, but it won't be there
  for "Launch at login" (no shell environment behind an app SMAppService
  starts). `Keychain.swift` already exists and is checked as a fallback;
  it just needs a menu item to actually write to it.
- **No notarization** on the packaged `.app` — needs an Apple Developer
  Program membership this project doesn't have. Ad-hoc signed works fine
  locally; sharing it means a one-time right-click → Open for whoever runs it.
- Two more moods (`chill`, `wake`) are designed-but-not-built; see `CLAUDE.md`
  §6 for the intent behind them.

## Project layout

```
blender/                Blender build scripts — the source of truth for her model
Sources/Loaf/            the Swift app
  Resources/sprites/<weight>/   sprites Blender renders directly into
tools/package.sh         builds the real, installable .app + .dmg
web/                     a Three.js live-rig previewer, for iterating on motion
                         without a full Blender render (dev tool, not shipped)
ref/lil-cleo/            reference desktop-pet implementation (gitignored, see CLAUDE.md §5)
```

See `CLAUDE.md` §2 for the full annotated tree.
