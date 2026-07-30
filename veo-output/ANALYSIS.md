# Veo run 01 — analysis

Source: Gemini share link, downloaded 2026-07-25. Video at `deskitty_veo.mp4`.
`grid.png` = 12 frames across the full clip. `gait_row.png` = 6 consecutive frames
(half a second) to inspect the walk.

**Specs:** 1280×720, h264, 24 fps, 240 frames, 10.01s, AAC audio track present.

**This ran the ORANGE prompt** — the stale version that was still on the clipboard,
not the white cat with black points. Worth re-running if Veo continues.

---

## What worked

- **Green screen is clean and keyable.** Flat, saturated, no subject contamination.
- **The voxel style landed.** Hard-edged blocks, flat matte shading, no bevels, no fur
  strands. The negative prompt did its job.
- **It reads unmistakably as a cat** — hooked tail, ears, protruding muzzle, dark paws,
  correct chunky proportions. Honestly a better-looking character than the current
  Blender model.

## What failed — and these are disqualifying for sprites

1. **It's a 3/4 view, not a profile.** The prompt asked for "perfect side profile, flat
   orthographic-looking perspective." Veo delivered a perspective 3/4 with the face
   turned toward camera. **This alone breaks the sprite contract**: you cannot mirror a
   3/4 view for leftward travel — flip it and she faces backwards. Profile is
   non-negotiable for locomotion sprites and Veo ignored it.

2. **She isn't actually walking.** Across six consecutive frames (half a second) the
   legs barely move. There's no four-beat gait and no stride — it's a standing idle with
   body wobble. The single most important thing the clip needed to prove, it didn't.

3. **Geometry drifts frame to frame.** Measured over 80 sampled frames:

   | | spread | % of mean |
   |---|---|---|
   | silhouette height | 6px | 4% |
   | silhouette **width** | **32px** | **20%** |
   | horizontal centroid | 16px of 320 | 5% |

   Height is stable but width swings 20% — that's the body length and tail curl morphing
   between frames, not a stride. The silhouette is not stable enough to cut frames from.

4. **Watermark.** A ✦ sparkle sits bottom-right of every frame, and SynthID is almost
   certainly embedded invisibly. Croppable, but it constrains the frame.

5. **Ground shadow and a background gradient**, despite the prompt forbidding both. Not
   fatal for keying, but it means the prompt's background clause was partly ignored.

6. **Palette not followed.** Eyes came out white/pale rather than olive `#47572D`, and
   the ears grew pink inners that were never requested.

---

## Verdict

This is the predicted outcome, now with evidence: **Veo is a style and motion reference,
not a sprite source.** Points 1 and 2 are not prompt-tuning problems — a model that
won't hold an orthographic profile and won't animate a rigid four-beat gait can't
produce a walk cycle, which is the one state that mattered most.

Keep Blender for sprites. Keep Veo for the cinematic desk shot in `veo-prompts.md`
Section 3, where 3/4 perspective and a soft shadow are advantages rather than defects.

---

## Worth stealing into the Blender model

The Veo design beats the current build in four specific, portable ways:

- **Shorter, chunkier body.** The Blender cat is too long and lean; Veo's is stubbier
  and reads cuter at small sizes.
- **Taller dark paws.** More like boots than the current thin toe caps — reads much
  better as a marking than a sock.
- **Pink inner ears.** A second warm note echoing the nose; costs two blocks.
- **A softer tail curve** with more than two segments, instead of the current rigid L.
