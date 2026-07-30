# Loaf — Google Veo prompt pack

Prompts for generating Loaf's states as video, matched to the voxel character we
built in Blender (`blender/build_cat.py`, renders at `blender/cat_side.png` and
`blender/cat_idle.png`).

---

## 0. Read this first

**Start from image-to-video, not text-to-video.** Feed `blender/cat_side.png` as the
input/first frame and let Veo animate it. Text-to-video will invent a different cat on
every clip and you'll spend the whole session fighting drift. The Blender render already
locks the palette, the proportions and the block grammar — that's the thing Veo is worst
at holding and you already have it for free. Only use the pure-text prompts (Section 2)
for exploration, or for states whose silhouette differs so much from the render that the
input frame fights you (chonk, sleep).

**What Veo will not give you:**

- **No alpha channel.** Output is opaque video. That's why every sprite prompt below
  specifies a flat chroma background — you key it out afterwards (Section 4).
- **No guaranteed seamless loop.** Generate longer than you need and find a loop
  segment, or ping-pong the clip.
- **No exact palette.** Treat the hex values as steering, not a contract. Quantize to
  your real palette in post.
- **Soft edges.** Veo's natural instinct is to round, bevel and light things
  cinematically. The negative prompt is doing real work here — don't drop it.
- **Short clips** (~8s on current tiers — check yours). Fine: a walk cycle needs 8–12
  frames, not 200.

Honest read: for *shipping sprites*, the Blender pipeline is still the reliable path —
it gives you exact repeatability, real alpha, and a rig you can pose. Veo's genuine wins
here are (a) motion reference — watch how a real animator would time the tail flick and
the startle, then key that into the rig, and (b) the promo/demo footage in Section 3,
which Blender would be painful for. Use it for those and you'll be happy.

---

## 1. The blocks (paste these into every sprite prompt)

### 1a. STYLE + ANATOMY — always include

> Minecraft-style voxel cat character, built entirely from a small number of hard-edged
> rectangular blocks with sharp 90-degree corners. No bevels, no rounded edges, no
> organic curves, no fur strands, no whiskers. Flat matte surfaces with soft even
> shading. Chunky low-poly game-asset look — not photoreal, not fluffy, not Pixar-style.
>
> Exact palette: a WHITE cat with black points. Body, head, ears, legs and snout are warm
> off-white #F2EEE6, with the belly and underside a slightly darker warm grey #D6CEC0. The
> tail is entirely soft black #2B2B33, and so are the tips of both ears. The bottom of each
> paw is capped in a slightly softer black #3E3E48, like small dark socks. Eyes are flat
> pale blue #4E93C4. Nose is a small dusty pink #E0899C. Nothing is pure white and nothing
> is pure black.
>
> Exact anatomy: a horizontal four-legged cat standing on four short square legs. A
> rectangular body block runs front to back. The cube head sits raised ABOVE the line of
> the back, with a clear step at the shoulders. Two small square ears on top of the head,
> wider than they are tall and set close to the centre line — NOT tall narrow rabbit ears.
> A short square snout protrudes from the front of the head with the pink nose block at
> its tip. A thin square-sectioned tail rises from the rump and hooks forward at the tip —
> the tail is visibly thinner than the ears. The head is large relative to the body; cute,
> stubby proportions.

### 1b. CAMERA + BACKGROUND — always include for sprite work

> Camera: locked off and completely static. Perfect side profile, flat orthographic-looking
> perspective at the cat's mid-body height, cat facing screen right, full body in frame
> with even margins. No camera movement whatsoever — no pan, no dolly, no zoom, no
> handheld drift, no parallax, no rack focus.
>
> Background: 100% flat uniform chroma green #00B140, edge to edge. No gradient, no
> vignette, no floor plane, no horizon line, no cast shadow, no ground-contact shadow, no
> environment, no props, no text.
>
> Lighting: soft, even and constant for the entire shot. No flicker, no changing light, no
> lens flare, no colour shift.
>
> Audio: silent. No music, no sound effects, no dialogue, no purring.

### 1c. NEGATIVE PROMPT — paste into the negative field every time

```
photorealistic fur, realistic cat, rounded edges, bevels, smooth organic shapes, whiskers,
anime, cel-shading outlines, text, watermark, logo, UI overlay, human hands, camera
movement, zoom, pan, background scenery, floor, ground shadow, motion blur, depth of
field, colour shift, character redesign mid-shot, extra limbs, two tails, morphing
geometry, flickering
```

---

## 2. The state prompts

Each one = **1a + 1b + the Action block below**, with 1c in the negative field. The states
map to Idea.md's mechanic: body size tracks task load, posture tracks system stress.

### IDLE — neutral, nothing happening

> Action: the cat stands still in profile and idles. Very subtle, loopable motion only —
> slow shallow breathing that lifts and lowers the chest and back by a tiny amount; the
> tail tip sways gently side to side about once every two seconds; the ears twitch once;
> it blinks twice, the eye block briefly collapsing to a thin dark line and reopening. The
> feet stay planted. The body does not travel. The cat ends the shot in exactly the same
> pose and the same position it started in.

### WALK — travelling across the desktop

> Action: the cat walks at a steady relaxed pace in profile, walking in place as if on a
> treadmill so its body stays perfectly centred in frame and does not travel across the
> screen. Clear four-beat blocky gait: the legs swing forward and back as rigid blocks
> pivoting at the shoulder and hip, never bending, stretching or deforming. A slight
> up-and-down bob of the body in time with the steps. The tail sways in opposition to the
> stride. The head stays level and forward-facing. Constant speed throughout with no
> acceleration and no pause, so the motion loops seamlessly.

### CHONK — high task load

Fatness is the task-load axis. In profile that has to read as **belly depth**, not width.

> Action: the same cat, but noticeably fatter — the body block is deeper and taller, the
> belly hangs low and nearly closes the gap to the floor, and the legs look short and
> stubby underneath it. It stands still and sighs: one slow heavy breath that visibly
> expands and settles the belly, the tail drooping and giving a single lazy flick, the head
> dipping slightly. Everything else is identical — same palette, same block grammar, same
> head, same face, same camera.

Generate this at 2–3 fatness levels by swapping "noticeably fatter" for "slightly rounder"
/ "very round, almost spherical body block, belly touching the floor."

### STRESSED — high CPU

> Action: the same cat, tense and frightened. It hunches down low and compact, legs tucked
> in close beneath it, back arched up, ears flattened backwards against the head, tail
> held low and tucked in tight along the body. It flinches — one quick sharp startle, then
> small nervous shivers. Eyes wide open and unblinking. The head snaps to look around once.
> Small, quick, jittery movements — not smooth, not graceful.

### CHILL — system idle, nothing queued

> Action: the same cat, relaxed and cool, wearing chunky blocky black over-ear headphones
> (two flat square ear cups in #1F1F1F joined by a square band over the top of the head)
> and small flat black rectangular sunglasses covering both eye blocks. It is lounging,
> sitting with the front legs straight and the haunches down, head nodding gently and
> rhythmically to a beat, tail flicking in time. Relaxed, confident, unbothered. The
> headphones and sunglasses are built from the same hard-edged blocks as the rest of the
> cat, same flat matte shading.

### WAKE / MORNING GREETING

> Action: the cat wakes up and stretches. It starts lying down flat and curled, then rises:
> the front legs stretch far forward while the haunches stay up and the back arches down in
> a deep cat stretch, tail lifting straight up; then it pulls upright into a normal standing
> profile, shakes its head once, and blinks awake. One continuous smooth motion, ending
> standing perfectly still in the neutral idle pose.

### SIT — front facing

Use `blender/cat_sit_front.png` as the input frame for this one, not `cat_side.png`.

> Action: the cat sits upright facing the camera, front legs straight and vertical, back
> legs folded beneath it, tail curled around the front of its paws with the tip hooked up.
> It holds the sitting pose and looks around: the head turns smoothly left, pauses, turns
> right, pauses, then returns to centre — the body stays completely still while the head
> moves. It blinks twice. The tail tip flicks once. Alert, calm, attentive. The cat does
> not stand up, does not lie down, and does not move from its spot.

### SLEEP

> Action: the cat is curled up asleep on its side, body settled into a compact block, tail
> wrapped around towards the nose, eyes closed — the eye blocks replaced by thin flat
> horizontal dark lines. The only motion is slow deep breathing that gently raises and
> lowers the body, and one ear twitching once. Extremely still and calm.

---

## 3. Promo / demo shot (not a sprite — ignore 1b and 1c here)

This is where Veo genuinely beats the Blender pipeline. For a launch post or README demo:

> Cinematic close-up product shot. A warm sunlit wooden desk with a modern laptop showing a
> code editor, slightly out of focus in the background. In sharp focus in the foreground, a
> small Minecraft-style voxel cat stands on the desk surface at the base of the screen —
> [paste style + anatomy block 1a] — in profile facing right, breathing gently and flicking
> her tail, then turning her head towards camera and blinking once.
>
> Shallow depth of field, soft morning window light, gentle dust motes in the air, 35mm
> lens, static locked-off camera, no camera movement. Warm, cosy, indie-software mood.
> Audio: quiet room tone and soft distant keyboard typing, no music.

Variant for the stress state — same setup, but: *"the laptop fan audibly spins up, and the
cat flinches, flattens her ears and hunches down small next to the keyboard."*

---

## 4. Video → sprite sheet

```bash
# 1. Key the green and pull frames at sprite rate, nearest-neighbour so edges stay crisp
ffmpeg -i clip.mp4 \
  -vf "chromakey=0x00B140:0.12:0.02,fps=12,scale=256:-1:flags=neighbor" \
  -pix_fmt rgba frames/f_%03d.png

# 2. If the key leaves green fringing on the orange fur, despill first
ffmpeg -i clip.mp4 \
  -vf "despill=type=green:mix=0.5,chromakey=0x00B140:0.14:0.03,fps=12,scale=256:-1:flags=neighbor" \
  -pix_fmt rgba frames/f_%03d.png

# 3. Quantize to the real Loaf palette (make palette.png from your 4 hex swatches)
ffmpeg -i frames/f_%03d.png -i palette.png \
  -lavfi "paletteuse=dither=none" -pix_fmt rgba out/f_%03d.png

# 4. Pack into a horizontal strip
ffmpeg -i out/f_%03d.png -filter_complex "tile=12x1" walk_sheet.png
```

Green is still the right key colour — it appears nowhere on a white/black/pink/pale-blue
cat. But **despill is now mandatory, not optional**: white fur picks up far more green
bounce from the backdrop than orange fur did, and an unspilled key will leave her looking
faintly seasick. Always use the second command, never the first.

Don't switch to blue (the pale blue eyes will punch holes) or magenta (it'll eat the pink
nose). If green spill proves unfixable, the fallback is a **mid-grey #808080** backdrop
plus rotoscoping rather than keying — slower, but white-on-grey at least has an edge to
trace.

---

## 5. Practical order of attack

1. Image-to-video from `cat_side.png` with the **IDLE** action. If the character survives
   8 seconds without drifting, the pipeline works and everything else is a variation.
2. **WALK** next — it's the one that either works or immediately tells you Veo can't hold
   blocky rigid-limb motion, which is the real go/no-go for sprite generation.
3. If those two hold up, do the state set. If they don't, keep Veo for Section 3 and pose
   the states on the Blender rig instead — the armature is already built for it
   (`spine` arches the back for STRESSED, the four leg bones stagger for WALK).
