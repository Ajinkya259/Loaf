# Loaf

A voxel cat who lives on the macOS dock as a desktop pet. She is a *status
indicator with a personality*: how much work is queued changes her body, what the
machine is doing changes her mood.

- **Task load → body size.** More/heavier tasks queued → she gets fatter and
  visibly more depressed. Nothing pending → lean and chill.
- **System load → posture/mood.** Overloaded machine → tense, hunched, small.
  Idle → she naps, or gets a prop vignette (coffee, popcorn).
- **User idle → sleepy.** Away from the keyboard → she curls up and naps.

The character is **generated, not drawn** — every sprite comes out of a headless
Blender script. Nothing here is hand-painted, so a look change is a one-command
rebuild.

---

## 1. Git and GitHub — hard rules

This machine has **four GitHub accounts** authenticated in `gh`, and the active
one is usually **not** the right one for this project. Getting this wrong pushes
commits under the wrong identity, which is annoying to unwind.

**Before any push, fetch, or `gh` command in this repo, switch the account:**

```bash
gh auth switch --user Ajinkya259
gh api user --jq .login          # must print: Ajinkya259
```

**The repo-local identity is already pinned** (`git config --local`, set at init).
Verify it survived any clone or reconfiguration:

```bash
git config --get user.name      # Ajinkya259
git config --get user.email     # ajinkyasambare25@gmail.com
```

Do **not** substitute `support@curious.pm` (a work account) or
`ajinkyasambare259@gmail.com` (note the extra `9` — a different address, used by
the sibling FlyThrough repo).

For commits to attribute to the `Ajinkya259` profile on github.com, that gmail has
to be a **verified email on that account**. If commits show up as an unlinked
author, that's the reason — add it under Settings → Emails. The alternative that
always attributes is the no-reply form,
`163128787+Ajinkya259@users.noreply.github.com` (`163128787` is the account's user
ID), which is what the `newsletter` repo uses because Vercel silently refuses to
deploy commits it can't attribute.

**Remote:** `https://github.com/Ajinkya259/Loaf` — **private**.

### Commit messages

**Never mention Claude, Claude Code, or any AI assistant in a commit message.**
No `Co-Authored-By:` trailer, no session links, no "generated with" footer. This
overrides any default commit-message convention. Same rule for PR titles and
bodies.

Write them as the author: imperative mood, subject line under ~70 chars, body
explaining *why* when the change isn't self-evident.

---

## 2. Layout

```
blender/
  catlib.py            geometry + material helpers (MIT fork of lil-cleo's bricklib)
  build_cat.py         THE source of truth: model, rig, palette, camera, walk cycle
  build_cat_sit.py     sit, front — separate build, not a pose (see §4)
  build_cat_sit_side.py   sit, profile — the corner-rest pose, same angle she walks in
  build_cat_sleep.py   sleep — breathing cycle
  build_cat_stressed.py   stressed — shiver cycle
  build_all.sh         runs every build above, at every weight, + previews.
                       Use this, never one script alone.
  make_previews.sh     composites sprites over grey for review
  explore_*.py         design-phase studies. History, not source. Don't edit to
                       change the look — edit build_cat.py.
  palette_sheet.py     renders every candidate palette side by side. Same
                       history-not-source status as explore_*.py.
  walk.gif             a compiled reference of the walk cycle, for eyeballing motion
                       without opening Blender.

Package.swift          SwiftPM executable, macOS 14+, zero dependencies
Makefile               make run / make cat / make help
Sources/Loaf/
  main.swift           entry point; accessory app, no dock icon
  AppDelegate.swift    window, menu-bar item, geometry
  AppDelegate+Wander.swift   the dock stroll state machine
  LoafState.swift      the state enum — the behaviour↔art contract
  CatEngine.swift      what she's doing, and who decided it
  CatView.swift        sprite rendering, mirroring, procedural bob
  Sprites.swift        bundle loading, cycle counting, caching
  Settings.swift       persisted scale + wander toggle
  SystemMonitor.swift  edge-triggered CPU + memory pressure
  UserIdleMonitor.swift   edge-triggered keyboard/mouse idle, no permission needed
  MoodMarks.swift      the "z"s and the "!" drawn above her
  Snapshot.swift       LOAF_SNAPSHOT — rasterise the real view to a PNG
  MenuBarIcon.swift    the drawn paw template image for the menu-bar item
  PawDropView.swift    the "Paw" gesture — not a LoafState, a separate overlay
                       window, drawn code-side rather than Blender. Menu-triggered
                       or on system wake; see §6
  Resources/sprites/<weight>/   ← Blender renders STRAIGHT INTO HERE (§3, §5)

SPRITE_CONTRACT.md     the Blender↔app interface. Read before touching either side.
Idea.md                original brain-dump. Superseded in places (see §6).
veo-prompts.md         Google Veo prompt pack (promo footage only, not sprites)
veo-output/ANALYSIS.md why Veo was disqualified as a sprite source
*.html                 design studies — open in Safari, don't publish as Artifacts
web/                   Three.js live-rig previewer — same armature as the sprite
                       build, posed continuously in a browser instead of baked to
                       stills. `web/serve.sh` to run it. Dev tool, not shipped.
ref/lil-cleo/          reference implementation, gitignored (see §5)
```

`.gitignore` explains each exclusion inline. The short version: `.blend` files and
~100MB of exploration renders are all regenerable from the scripts.

---

## 3. Rebuilding the cat

```bash
blender/build_all.sh
```

Blender lives at `/Applications/Blender.app/Contents/MacOS/Blender` (5.2.0, via
`brew install --cask blender`). Each script wipes the scene and rebuilds from
nothing, so geometry, rig and palette changes are all one command.

**Blender writes directly into `Sources/Loaf/Resources/sprites/`** — there is no copy
step between the renderer and the app, and there should never be one. A sync step is a
drift bug waiting to happen. A symlink was tried and does *not* work: SwiftPM's `.copy`
duplicates the link verbatim into the resource bundle, where its relative path no
longer resolves and the app silently finds no sprites at all.

**Always `build_all.sh`, never a single script.** The standing and sitting builds
drifted apart twice from single-script runs — once the stander kept obsolete ears
after only the sit was fixed, once the sit sprite was deleted outright by a clean
that only re-ran the stander.

**Review over grey, never raw.** Sprites ship with alpha and she has a pale
underside, so a raw sprite in any viewer composites over white and reviews as a
blank rectangle. This has already caused one false "the side view is gone?" alarm.
Use `previews/contact_sheet.png`, which also catches states drifting out of sync.

**Judge her at DISPLAY size, not render size — `previews/contact_small.png`.**
The renders are 640×512; the app draws her at 160×128. That is a 4× downscale, and
detail that looks fine on a full-size preview can disappear entirely on screen. A
profile sit was passed as good on the big previews and was an unrecognisable blob in
the app: its tail failed to clear her back line, which only matters once the fine
detail is gone and the silhouette is all that is left.

The corollary is a design rule, not just a review step: **at display size only the
silhouette survives.** What makes the walking sprite work is the tail standing clear
of the back, the gaps between the legs, and the step from head to shoulder — outline
features, every one. Any pose that doesn't hold those reads as an orange blob no
matter how correct its interior is.

**Draw curves as many small regular steps, never few big ones.** This took nine passes
on the profile sit and is the most transferable thing learned here. A sitting cat's
profile is one flowing line — up the legs, over the chest, round the head, then a long
curve down the back into the rump. Describing it with two or three large boxes gives
0.2–0.4 unit steps, which at display size are 14–28px corners: a staircase, not a
curve. The fix is the standard pixel-art one — six slabs of ~0.115 are ~3px each and
the eye integrates them into a smooth line.

Two corrections worth keeping, because both were tried and both were wrong:

- **Block count was never the issue.** "Use fewer, bigger blocks" was tried and made
  it worse. Big *irregular* steps read as corners; small *regular* ones read as a
  curve. It is the step size that matters.
- **Layer in the direction the mass stacks.** Building the curve from vertical columns
  bent the top down and the underside up at once, leaving a thin diagonal band with no
  mass — she read as a lizard. A seated cat is upright over a heavy rounded rear, so
  it has to be horizontal slabs.

**Pale belly is pose-dependent.** Standing, the underside is lit from below and a pale
band reads as counter-shading. Sitting, that same band lies flat on the ground line and
reads as a mat she's perched on. In seated poses the pale goes on the chest and front
legs instead.

---

## 4. The look — committed decisions

Locked into `build_cat.py`. Exploration is over.

| | |
|---|---|
| Coat | `#E8944A` — back, head, tail |
| Underside | `#F6F1E7` — belly, bib, legs |
| Accent | `#2B2B33` — socks, toes only, **not** ear tips |
| Face | `#FBF8F4` / `#1A1A1E` only |
| Lighting | hard axis suns, no shadows, **no specular** |

These look arbitrary from outside. They aren't:

**The face is monochrome and does not follow the coat.** It borrows nothing from
the body, so one face fits any colourway and she stays a single character instead
of becoming twelve different cats. It's also the highest-contrast region on the
model, which puts it where the eye should land first. Alternate colourways live in
`explore_pattern.py`; swapping the three coat constants is the whole change.

**Flat lighting is not a style preference.** Soft area lights smear a gradient
across each flat voxel face and she reads as generic 3D. Hard suns down the three
axes with shadows and specular off give one flat value per face direction.
Specular matters specifically: a hard sun on a glossy eye material blew the eyes to
solid white on the first attempt.

**Vertical slit pupils.** The most cat-specific feature available per block, and
animatable (wide = startled, narrow = focused) with no new sprites.

**Ears are one colour, with no dark tip.** The accent originally went on the ear
tips too. Head-on that was fatal: a dark cap terminates the taper, so each ear read
as a separate dark-topped post rather than a triangle growing out of the head —
three colours stacked in a 0.19-tall shape is too much information at sprite size.
Fixed in `82270c8`; see SPRITE_CONTRACT.md §3b.

**The sit is a separate build, not a pose.** Standing legs are single rigid blocks
with no knee, so no rotation folds the haunches. A sit needs different geometry —
the back legs collapse into one wide rump. Same reason `sleep` and `stressed` each
got their own build script instead of being posed from the stander.

**The face lives in ONE place: `build_face()` in `build_cat.py`.** Poses are separate
builds, so every pose needs its own copy of the head — which is precisely how the
standing and sitting cats drifted apart twice. Proportions are fractions of a
reference head (0.78 × 0.66), scaled, so a pose only declares how big its head is.
`FACE_PARTS` splices the part list into a pose's bone map. Never hand-copy face
geometry into a pose again.

**Her head must be the SAME SIZE in every pose.** The front sit uses a 0.50 head
against the stander's 0.66, so she loses a quarter of her head the moment she sits
down. An oversized head on a small body is the whole cute-quadruped trick, and it
applies to every pose. This is currently *wrong* in `build_cat_sit.py` and is the
single most likely reason the front sit reads weaker than the standing views.

### Open items

**Task load has no real source yet** — the Weight menu sets it by hand.

**The walk is a pendulum, not a walk** (§7), and jump frames 2–5 sit 4–8px below the
ground line while airborne. Both recorded with per-frame numbers in
SPRITE_CONTRACT.md.

### Superseded: the profile sit

**Fixed** — it took nine passes and the answer was never in the numbers. Kept below
because the failure modes are the transferable part.

The reasoning behind it is sound and worth keeping: profile is the informative angle
for a quadruped (head-on, a sitting cat hides its whole body behind its head), and
she currently snaps 90° to face the camera when she sits at a corner, which nothing
alive does. What defeated four passes:

| Tried | Result |
|---|---|
| Single-step back, tall torso | Kangaroo |
| Three-step staircase back | Kangaroo |
| Full-size head (0.64, not 0.54) | Better proportioned, still a kangaroo |
| Head pushed forward for a shoulder step | Still a kangaroo |

The remaining problem is that **head and torso fuse into one orange column** — the
recorded "cow" failure, where a head level with the back merges into the body. In the
standing pose the head clears it by sitting proud of the back line with a real
shoulder step, and no equivalent has been found for an upright seated body.

**Do not keep nudging numbers.** That is four passes of exactly the oscillation this
file warns about in §7. Get a reference image of a sitting cat in profile, measure its
proportions, and port them — the way measuring the Veo render fixed the standing
silhouette after four failed hand-tuned passes.

**Colour method that worked, reuse it:** score candidates in CIE L\* — coat-to-
underside gap ≥ 25, accent ≤ L\*22, eye ≥ 15 from coat — then confirm with a
grayscale squint test. 9 of 13 hand-picked colourways failed this. Value contrast
beats hue. Hue-shift shadows cooler rather than just darkening them.

---

## 5. The app

SwiftPM executable, macOS 14+, **zero third-party dependencies**, AppKit borderless
window + SwiftUI character view, accessory app (no dock icon) with a 🐾 menu-bar item.

```bash
make run                    # build + launch
LOAF_STATE=sit make run     # pin one state for inspection (idle | walk | look | sit)
make stop
```

The zero-dependency rule is deliberate and worth holding. She runs all day, every day:
every dependency is memory she holds the whole time, launch time on every login, and
supply chain for something that needs nothing but AppKit, SwiftUI and a folder of PNGs.

**Working today:** window on the dock; stroll → dwell → corner sit → sleep; jump with an
app-driven arc; eight states across three body weights (72 sprites); CPU/memory
reactions; sleeps early when you've stepped away; a "Paw" gesture that also fires on
system wake. 160×128pt at scale 1.0, ~1.7% CPU, ~90MB RSS, **zero permissions requested**.

### The two axes of the mechanic

They are deliberately separate, so they compose — she can be fat *and* frightened, which
is the "too much to do and the laptop is dying" case.

| Signal | Changes | How |
|---|---|---|
| Task load | her **body** | weight directory, applies to every pose |
| Machine load | her **posture** | `stressed` state, edge-triggered |

**Weight is a DIRECTORY, not a filename suffix** — `sprites/<weight>/<state>.png`.
Fatness applies to every pose, so as a suffix it is a cross product that multiplies
again with each new state (the 64-sprite trap). As a directory the contract inside each
folder is identical: a new state gets every weight free, a new weight gets every state
free. `Sprites.weight` is the only thing that knows.

How weight reads depends on the camera and had to be done per pose: **profile** is the
belly dropping (the back line stays pinned and the body grows downward, so her legs
appear to shorten); **front** is pure width; the **profile sit** swells in Y, because
there Y is screen-width.

**Task load is still set by hand** from the Weight menu. EventKit Reminders is the next
step — note it needs `requestFullAccessToReminders()` and
`NSRemindersFullAccessUsageDescription`, a *different* permission from FlyThrough's
calendar access.

### Marks drawn above her

`MoodMarks.swift` — drifting "z"s for sleep, a flashing "!" for stress.

These are not decoration, and the reason is the most useful thing learned about this art
style: **a low, solid pose has no negative space inside its outline, and at 160×128 the
outline is the entire read.** The gaps between her legs are most of why the idle sprite
works. Sleep took seven passes and none of them fixed it; a drifting "z" did, instantly,
because it doesn't depend on silhouette at all. Stress has the same problem and gets the
same answer.

Both share a treatment — white fill, hard black outline from four zero-radius shadows —
so they read as one language and survive a desktop of any colour. A single soft halo is
not enough: white vanishes on a light wallpaper, dark vanishes on a dark one. The "z"s
shipped invisible for exactly this reason.

### Seeing what the APP draws

```bash
LOAF_SNAPSHOT=/tmp/x.png LOAF_STATE=stressed ./.build/debug/Loaf
```

Rasterises the live SwiftUI view and exits, over a **white/dark split background**.

This exists because there was no way to check anything the app drew on top of a sprite.
Every visual check went through Blender's previews, which show only the sprite — so the
"z"s shipped invisible and the user found out, not the tooling. A plain background would
have hidden it too, hence the split.

Two design points that aren't obvious from reading the code:

**`CatEngine.pinned` is what stops the menu and the wander loop fighting.** Both want to
set her state. When you pick one from the menu it wins outright and `setAuto` silently
drops the wander loop's updates, so callers never need to know whether they're allowed
to move her.

**The menu is rebuilt on every open (`menuNeedsUpdate`)** rather than holding a dozen
`NSMenuItem` references in sync. That makes the "no art yet" section self-updating: a
state lights up the moment Blender renders its sprite, with no code change. Availability
comes from `Sprites.exists`, which accepts a still **or** a cycle — checking only one
marks either `sit` (a lone still) or `walk` (a cycle with no `walk.png`) as missing.

`ref/lil-cleo/` is a shipped MIT desktop pet solving nearly the same problem and is
the load-bearing reference. Re-clone with
`git clone https://github.com/ankitaggarwal/lil-cleo ref/lil-cleo`.

| File | How to use it |
|---|---|
| `ImageCharacterView.swift` | **Adapt closely** — sprite loading, `<state>1..N` cycling, `scaleEffect(x: facing)` mirroring, procedural motion layered on stills |
| `SystemMonitor.swift` | **Adapt closely** — edge-triggered signals, not per-tick polling. Its RAM-pressure hold timer is a real bug fix worth inheriting |
| `AppDelegate+Wander.swift` | **Adapt** — stroll → dwell → corner nap → wake-on-event, dock probing, sub-pixel accumulation |
| `Emotion.swift` | **Structure only** — 857 lines of a LEGO minifig's feelings. Take the shape (renderer-agnostic enum, one sprite + one line per case), write Loaf's own states |

Loaf's new axis is the one lil-cleo doesn't have: task load as body size.

**Sprites currently available:** `side_idle`, `front_idle`, `sit`, `walk1..8`.
Two contract details when writing the loader: map `sleep` explicitly to `sit`
(letting it hit the fallback chain gives a cat sleeping standing up), and drop
`hero` from lil-cleo's fallback chain — that's their sprite name, it doesn't exist
here.

**The fatness trap.** Fatness is a *modifier*, not a state: 4 weights × 8 states +
walk = **64 sprites**. Don't design it into the app until three test renders of
`side_idle` have been eyeballed. The cheap escape is weaker than it looks —
`scaleEffect(y:)` stretches legs and head too, and fatness has to read as belly
depth in Z, which is the axis the profile camera *does* see.

---

## 6. State model

Supersedes `Idea.md` where they disagree.

| Trigger | State | Built? |
|---|---|---|
| No tasks, user idle | sleepy → napping | **live** — `UserIdleMonitor`, no keyboard/mouse input for ~3min → `sleep` |
| No tasks, user present | chill + prop vignette (coffee, popcorn) | no — `chill` has no art, see §4 |
| Tasks piling up | fat **and** depressed — mood, not just size | weight is live; "depressed" mood on top of it isn't |
| Machine overloaded | stressed, hunched, ears flat | **live** — `SystemMonitor`, CPU/memory → `stressed` |
| System wake | morning greeting | **live**, minus the greeting text — `NSWorkspace.didWakeNotification` triggers the "Paw" gesture (`PawDropView.swift`) instead. A real greeting needs the brain layer below to have anything to say |

Props should use lil-cleo's `SHOW_FOR` map (props toggled per state on one base
pose) — already-solved architecture, don't invent a new mechanism.

`stressed`'s pose is built (`build_cat_stressed.py`, flat ears via geometry, not
rig bones — the earlier note that it was "blocked on ear bones" assumed posing
the standing rig, which was wrong: poses are separate builds). What's still
missing is triggering it from anything other than `SystemMonitor`.

Task-load source is still open. Recommendation: Apple Reminders via EventKit — no
OAuth, no backend, and the sibling FlyThrough project already proves the pattern.
Note Reminders needs `requestFullAccessToReminders()` +
`NSRemindersFullAccessUsageDescription`, which is a *different* permission from
FlyThrough's calendar access. Ship a manual 0–3 load override first regardless;
it's the debug affordance you want anyway.

---

## 7. Failure classes worth remembering

Each of these cost at least one wasted render.

**Recognition is judged from a single still frame.** It's silhouette, not motion.
No amount of gait work fixes a model that doesn't read standing still. Fix the
silhouette and re-check recognition *before* touching animation.

**When hand-tuning starts oscillating, stop and measure a reference that works.**
Four passes of nudging numbers produced, in order: a dog, a cow, a lamb, a rabbit.
The fix was measuring the Veo render's ratios, which inverted the model — the head
should be *bigger* than the body is deep. An oversized head on a small body is the
whole cute-quadruped trick.

**Ear shape decides the species.** Tall narrow ears set wide apart read
unmistakably as a rabbit. Cat ears are wider than tall, close to the centre line,
and small — about 20% of head height. Scaling ears up has produced a rabbit twice.

**Check both angles for every geometry change.** The tail once rose above the head
line at x≈0 and poked through the gap between the ears as a convincing third ear.
Completely invisible in profile.

**Occlusion is real depth, not z-index.** An ortho camera occludes by screen
footprint. A part hidden directly behind another is simply gone — the tail was
invisible in the very first render for exactly this reason. Offset parts
sideways so they clear the silhouette.

**`ls` the actual files before writing filename keys.** Python
`.replace(" ","_").replace("+","and")` yields `white_and_black`, not
`white_andblack`. This mismatch shipped twice.

**Save intermediate data back to disk.** A pack step once wrote its HTML output
directly without updating `pattern.json`, so every later step silently built on
retired data.

---

## 8. Working style

- **Build HTML as local project files and open in Safari. Never publish
  Artifacts.**
- **Phase the work.** Plan, build, and hand over one phase at a time for testing.
  Don't bulk-deliver.
- Prefer punchy and concise over exhaustive.
