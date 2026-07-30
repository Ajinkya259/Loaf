# Picking this back up

A resumption note, not a spec. `CLAUDE.md` is the reference — read that for the palette,
the build rules and the failure classes. This file is just *where things stand and what
to do next*.

---

## Run it in 30 seconds

```bash
cd ~/Desktop/untitled/Loaf
make run                    # build + launch; she appears on the dock
make stop
```

Everything is controlled from the **🐾** in the menu bar: pick a state, Weight, Size,
Show, React to system load.

```bash
LOAF_STATE=sleep make run                      # hold one state
LOAF_SNAPSHOT=/tmp/x.png LOAF_STATE=stressed ./.build/debug/Loaf   # see what the APP draws
LOAF_DEBUG=1 ./.build/debug/Loaf                # log every CPU/memory sample
blender/build_all.sh                            # re-render all 72 sprites (~3 min)
```

`git tag -l` → `v0.1-six-states`, `v0.2-both-axes`. Both are known-good.

---

## What works

Dock stroll → dwell → corner sit → sleep. Jumps (about one stroll leg in seven).
Draggable — picking her up wakes her, and she falls back to the dock when dropped.

**Eight states × three weights = 72 sprites.** idle, walk, jump, sit (front), sit
(profile), sleep, stressed, look.

**Both axes of the mechanic are wired, but only one has a real source:**

| Signal | Changes | Source |
|---|---|---|
| Machine load | her posture (`stressed`) | **live** — CPU + memory, edge-triggered |
| Task load | her body (weight) | **hand-set from the menu** |

Zero third-party dependencies. Zero permissions requested. ~1.7% CPU, ~90MB RSS.

---

## The next job: give task load a real source

This is the only thing standing between the app and the idea it was built for. Everything
downstream already exists — `Settings.weight` drives all 72 sprites, so this is purely
about producing a number.

Recommended source is **Apple Reminders via EventKit**: no OAuth, no backend, no task-entry
UI to build, and the sibling `~/Desktop/untitled/FlyThrough` already proves the EventKit
pattern in Swift.

1. `TaskLoad.swift` — count incomplete reminders due today, weight by priority.
2. Map to a weight. Suggested start: `0–2 → lean`, `3–6 → normal`, `7+ → chonk`.
3. Set `settings.weight`. That is the entire integration.
4. Keep the menu picker as a manual override — it is the only way to check the art
   without editing your real todo list.

**The one thing that will trip you up:** Reminders is *not* the same permission as
Calendar. FlyThrough uses `requestFullAccessToEvents()` +
`NSCalendarsFullAccessUsageDescription`. You need
**`requestFullAccessToReminders()` + `NSRemindersFullAccessUsageDescription`**. Copying
FlyThrough's code verbatim will compile and then silently return no reminders.

Note this is also the first thing that asks the user for a permission. Worth deciding
whether she degrades gracefully (stay at `normal`, never prompt again) rather than
nagging.

---

## Other open items

- **The walk is a pendulum, not a walk.** Symmetric sine on each hip; real gait needs
  stance/swing asymmetry. Judged fine at display size so far — don't touch it without
  looking at it in the app first.
- **Jump frames 2–5 sit 4–8px below the ground line.** Airborne, so nothing shows;
  frames 1 and 6 (crouch, landing) are fixed at exactly 24. Numbers in
  `SPRITE_CONTRACT.md`.
- **`chill` and `wake` are still unbuilt** — they show greyed out in the menu, which is
  automatic, not hardcoded. `chill` wants the prop vignettes from the state model
  (coffee, popcorn) via lil-cleo's `SHOW_FOR` pattern.
- **No `.app` bundle yet.** `swift run` only. `ref/lil-cleo/tools/package.sh` is a
  working template for the .app + .dmg, including ad-hoc signing.

---

## Four things that will waste your time if you forget them

**Check the GitHub account before pushing.** Four are authed in `gh` and the active one
defaults to the wrong one. `gh auth switch --user Ajinkya259`. Full rules in `CLAUDE.md`
§1, including that commit messages never mention AI.

**Judge her at display size, never at render size.** `previews/contact_small.png`. The
renders are 640×512 and the app draws her at 160×128 — detail that looks fine full-size
disappears entirely on screen. This cost seven passes on the sleeping pose alone.

**At display size, only the silhouette survives.** The gaps between her legs are most of
why the idle sprite reads. A pose without outline features cannot be rescued by
reshaping it — that is what `MoodMarks.swift` is for, and why sleep and stress each get
a symbol drawn above them.

**Verify what the APP draws, not what Blender rendered.** `LOAF_SNAPSHOT`. Every visual
check used to go through Blender previews, which show only the sprite — that is how the
"z"s shipped invisible (white glyphs on a light desktop) and stayed that way until a
human noticed.

---

## Map

| File | |
|---|---|
| `CLAUDE.md` | the reference — palette, build rules, failure classes |
| `SPRITE_CONTRACT.md` | the Blender↔app interface. Read before changing either side |
| `Idea.md` | the original brain-dump. Superseded in places |
| `blender/build_cat.py` | source of truth: model, rig, palette, camera, walk, jump |
| `Sources/Loaf/LoafState.swift` | the behaviour↔art contract. Start here in the app |
| `ref/lil-cleo/` | the reference implementation (gitignored; re-clone if missing) |
