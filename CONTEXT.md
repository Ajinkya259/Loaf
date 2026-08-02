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

Everything is controlled from the **🐾** in the menu bar — four rows: Autopilot,
Weight (still the manual override if Reminders access is denied), Actions (every
pose/gesture by hand), Settings.

```bash
LOAF_STATE=sleep make run                      # hold one state
LOAF_SNAPSHOT=/tmp/x.png LOAF_STATE=stressed ./.build/debug/Loaf   # see what the APP draws
LOAF_DEBUG=1 ./.build/debug/Loaf                # log CPU/memory/idle/paw/hydration/taskLoad
LOAF_IDLE_THRESHOLD=8 ./.build/debug/Loaf       # seconds, not the real ~180s, for testing
LOAF_HYDRATION_INTERVAL=8 ./.build/debug/Loaf   # seconds, not the real ~1-2h, for testing
blender/build_all.sh                            # re-render all 72 sprites (~3 min)
make dist                                       # dist/Loaf.app + dist/Loaf.dmg, installable
```

`git tag -l` → `v0.1-six-states`, `v0.2-both-axes`. Both are known-good.

---

## What works

Dock stroll (~4 minutes now, was 20-40s) → dwell → corner sit → sleep. Jumps (about
one stroll leg in seven). Draggable — picking her up wakes her, and she falls back to
the dock when dropped. Hover or click her directly and she greets you (`AppDelegate.
greet()`) — wakes her immediately if she was idle-asleep rather than waiting up to 5s
for the next poll, shows a short greeting bubble, and briefly turns to `.look` or
`.sit` (front). That's the only place `.sit` (front) is ever picked automatically —
every OTHER trigger respects "never turn to face the camera mid-stroll," but turning
to face someone who just looked at you directly is the correct response to that, not
a violation of it.

**Paw** in the menu is the same gesture (big menu-bar icon, drops down, double
pat, `PawDropView.swift`) — also fires on its own when the Mac wakes from sleep
(the "morning greeting" from CLAUDE.md §6, no text needed for it to read as one),
and every 1-2 hours paired with a water-reminder line (`Settings.hydrationReminders`,
its own toggle since a health nag and ambient personality are different enough in
kind that someone may want one without the other).

**Speech bubbles** (`SpeechBubbleView.swift`) — a random one-liner from a curated
pool, floated above her head while she's idle (not walking, not jumping, not
already asleep or stressed — those already have their own read and a bubble on
top would compete with it). Roughly every 1.5–4 minutes, or "Say something" in
the menu for an immediate one. `Settings.letHerTalk` turns it off. No LLM behind
it yet — this is the honest stand-in for that, described in `Idea.md`'s "brain
layer": a fixed pool, not real understanding, but enough to feel alive.

**Eight states × three weights = 72 sprites.** idle, walk, jump, sit (front), sit
(profile), sleep, stressed, look.

**Both axes of the mechanic are wired, and now both have a real source:**

| Signal | Changes | Source |
|---|---|---|
| Machine load | her posture (`stressed`) | **live** — CPU + memory, edge-triggered |
| User presence | sleep, early | **live** — `UserIdleMonitor`, no input for ~3min |
| Task load | her body (weight) | **live** — `TaskLoadMonitor`, incomplete Reminders |

Machine load outranks user-idle if both are true at once (`CatEngine.userIdle`) - a
background job left running while you stepped away still reads as stressed, not
asleep.

Zero third-party dependencies. **One** permission requested — Reminders, for task load.
`UserIdleMonitor`/`SystemMonitor` still need none. ~1.7% CPU, ~90MB RSS.

---

## Task load: done, via `TaskLoadMonitor.swift`

The thing every doc in this project pointed at as "the next job" for weeks. Incomplete
Reminders → `settings.weight`, `0-2 → lean`, `3-6 → normal`, `7+ → chonk`, exactly the
thresholds this section used to recommend before anything implemented them.

**The permission trap this section used to warn about, confirmed for real**: Reminders
is genuinely a different key from Calendar — `requestFullAccessToReminders()` +
`NSRemindersFullAccessUsageDescription`, not the Calendar pair FlyThrough uses.

**The trap this section DIDN'T see coming**: `swift run`/`swift build` produce a bare
Mach-O binary with no `.app` bundle, so there is no Info.plist for TCC to read the
usage-description string from at all — and without one, requesting access doesn't
degrade gracefully, it crashes outright. Fixed by embedding `Info.plist` directly into
the binary's own `__TEXT,__info_plist` section via linker flags in `Package.swift`
(`tools/package.sh`'s packaged `.app` gets its own separate copy of the same key).
Confirmed the embedding actually worked by extracting the section from the built
binary and diffing it against the source file, and confirmed the request itself works
by watching for `UserNotificationCenter.app` (the process that renders the real
permission dialog) rather than assuming a lack of crash meant success.

**Degrades gracefully, exactly as planned**: if access is denied, `onChange` simply
never fires again, and the Weight menu keeps working as a manual override, same as
before this file existed. No re-prompt loop, no nagging.

---

## Other open items

- **The walk is a pendulum, not a walk.** Symmetric sine on each hip; real gait needs
  stance/swing asymmetry. Judged fine at display size so far — don't touch it without
  looking at it in the app first.
- **Jump frames 2–5 sit 4–8px below the ground line.** Airborne, so nothing shows;
  frames 1 and 6 (crouch, landing) are fixed at exactly 24. Numbers in
  `SPRITE_CONTRACT.md`.
- **`chill` and `wake` aren't in `LoafState` at all right now** — dropped rather than
  shipped as permanently-disabled menu entries. They're still real ideas (see
  `CLAUDE.md` §6, the state model): `chill` wants the prop vignettes from
  lil-cleo's `SHOW_FOR` pattern (coffee, popcorn), `wake` wants a morning-stretch
  pose. Re-add as `LoafState` cases once either gets real Blender art — nothing else
  needs to change, the menu picks up a new case automatically.
- **`make app` / `make dist` build a real `Loaf.app`** (`tools/package.sh`, adapted
  from `ref/lil-cleo`'s own template) — icon generated from `front_idle.png`,
  `Info.plist` with `LSUIElement`, ad-hoc signed. No Developer ID identity on this
  machine, so no notarization step yet; on another Mac the first launch needs
  right-click → Open once. Verified for real, not just that it builds: launched the
  packaged binary directly, confirmed `lsappinfo` reports it as `type="UIElement"`
  (no dock icon), and confirmed sprites resolve from `Loaf_Loaf.bundle` inside the
  bundle rather than silently falling back to nothing.

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
| `Sources/Loaf/TaskLoadMonitor.swift` | the real task-load source — Reminders → weight |
| `tools/package.sh` | `make app` / `make dist` — builds the real, installable `.app` |
| `ref/lil-cleo/` | the reference implementation (gitignored; re-clone if missing) |
