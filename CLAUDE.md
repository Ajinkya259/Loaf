# Deskitty

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

**Remote:** `https://github.com/Ajinkya259/Deskitty` — **private**.

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
  build_cat_sit.py     the sit — separate build, not a pose (see §4)
  build_all.sh         runs both builds + previews. Use this, never one alone.
  make_previews.sh     composites sprites over grey for review
  explore_*.py         design-phase studies. History, not source. Don't edit to
                       change the look — edit build_cat.py.
  sprites/             ← the app's assets. Tracked. Everything else here is not.

SPRITE_CONTRACT.md     the Blender↔app interface. Read before touching either side.
Idea.md                original brain-dump. Superseded in places (see §6).
veo-prompts.md         Google Veo prompt pack (promo footage only, not sprites)
veo-output/ANALYSIS.md why Veo was disqualified as a sprite source
*.html                 design studies — open in Safari, don't publish as Artifacts
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

**Always `build_all.sh`, never a single script.** The standing and sitting builds
drifted apart twice from single-script runs — once the stander kept obsolete ears
after only the sit was fixed, once the sit sprite was deleted outright by a clean
that only re-ran the stander.

**Review over grey, never raw.** Sprites ship with alpha and she has a pale
underside, so a raw sprite in any viewer composites over white and reviews as a
blank rectangle. This has already caused one false "the side view is gone?" alarm.
Use `previews/contact_sheet.png`, which also catches states drifting out of sync.

---

## 4. The look — committed decisions

Locked into `build_cat.py`. Exploration is over.

| | |
|---|---|
| Coat | `#E8944A` — back, head, tail |
| Underside | `#F6F1E7` — belly, bib, legs |
| Accent | `#2B2B33` — socks, ear tips |
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

**The sit is a separate build, not a pose.** Standing legs are single rigid blocks
with no knee, so no rotation folds the haunches. A sit needs different geometry —
the back legs collapse into one wide rump. Same reason a future `sleep` will need
its own build.

**Colour method that worked, reuse it:** score candidates in CIE L\* — coat-to-
underside gap ≥ 25, accent ≤ L\*22, eye ≥ 15 from coat — then confirm with a
grayscale squint test. 9 of 13 hand-picked colourways failed this. Value contrast
beats hue. Hue-shift shadows cooler rather than just darkening them.

---

## 5. The app

**Not built yet.** Planned: SwiftPM executable, macOS 14+, **zero third-party
dependencies**, AppKit borderless window + SwiftUI character view, `LSUIElement`
accessory app with a menu-bar item.

`ref/lil-cleo/` is a shipped MIT desktop pet solving nearly the same problem and is
the load-bearing reference. Re-clone with
`git clone https://github.com/ankitaggarwal/lil-cleo ref/lil-cleo`.

| File | How to use it |
|---|---|
| `ImageCharacterView.swift` | **Adapt closely** — sprite loading, `<state>1..N` cycling, `scaleEffect(x: facing)` mirroring, procedural motion layered on stills |
| `SystemMonitor.swift` | **Adapt closely** — edge-triggered signals, not per-tick polling. Its RAM-pressure hold timer is a real bug fix worth inheriting |
| `AppDelegate+Wander.swift` | **Adapt** — stroll → dwell → corner nap → wake-on-event, dock probing, sub-pixel accumulation |
| `Emotion.swift` | **Structure only** — 857 lines of a LEGO minifig's feelings. Take the shape (renderer-agnostic enum, one sprite + one line per case), write Deskitty's own states |

Deskitty's new axis is the one lil-cleo doesn't have: task load as body size.

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

| Trigger | State |
|---|---|
| No tasks, user idle | sleepy → napping |
| No tasks, user present | chill + prop vignette (coffee, popcorn) |
| Tasks piling up | fat **and** depressed — mood, not just size |
| Machine overloaded | stressed, hunched, ears flat |
| System wake | morning greeting |

Props should use lil-cleo's `SHOW_FOR` map (props toggled per state on one base
pose) — already-solved architecture, don't invent a new mechanism.

`stressed` is **blocked on ear bones** — flattened ears are the most readable
stress cue and the ears currently ride the head bone.

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
