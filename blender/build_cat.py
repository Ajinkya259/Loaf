"""Build the Loaf voxel cat from scratch in Blender, headless.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat.py

Second pass: the cat is now a **horizontal quadruped** - body running front-to-back
along Y, standing on four legs - instead of the upright bear-like figure of the first
pass (kept at cat_upright.blend / build_cat_upright.py.bak). Same 10-block grammar and
fur spec from the style pitch, re-proportioned so the silhouette reads as a cat.

The hero view is now the **side profile**, which is what a desktop pet walking across
the screen actually shows. That flips two things the upright version got for free:
the face has to live on the head's side faces (not just the front), and the key light
has to move to the camera side.

Re-runnable: wipes the scene and rebuilds from nothing every time.
"""
import bpy, os, sys, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catlib as L
from catlib import PARTS, material, box, rgb

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat.blend")
# Blender renders STRAIGHT INTO the Swift package. There is no copy step and there
# should never be one: a sync step between the renderer and the app is a drift bug
# waiting to happen, and this project has already lost time to two of them. Same
# arrangement as lil-cleo's render_states.py.
#
# A symlink here was tried first and does not work - SwiftPM's .copy duplicates the
# link verbatim into the resource bundle, where its relative path no longer resolves,
# and the app silently finds no sprites at all.
SPRITES = os.path.join(HERE, "..", "Sources", "Loaf", "Resources", "sprites")

# COMMITTED PALETTE - bicolour ginger with a monochrome face.
#
# Coat: orange back, head and tail; pale belly and legs; black socks. Chosen because
# orange is the one body colour that never loses against a light desktop, which is
# where the earlier white cat kept failing.
#
# Face: white and black only, no exceptions. It borrows nothing from the coat, so the
# same face works on any colourway and she stays one character instead of becoming a
# different cat every time the body changes. It is also the highest contrast anywhere
# on the model, landing exactly where you want the eye to go first.
#
# Every value here cleared a contrast audit in CIE L*: coat-to-underside gap >= 25,
# accent darker than L*22. Nine of thirteen earlier colourways failed it.
COAT      = "#E8944A"   # back, head, tail
UNDER     = "#F6F1E7"   # belly, bib, legs - a cat is always paler underneath
ACCENT    = "#2B2B33"   # socks and ear tips: the dark anchors that hold the silhouette
FACE_W    = "#FBF8F4"   # sclera, muzzle patch, inner ear
FACE_K    = "#1A1A1E"   # pupil, nose, mouth

# Alternate colourways live in blender/explore_pattern.py; swapping COAT/UNDER/ACCENT
# for any validated set there is the whole change.

# ----------------------------------------------------------------------------
# Layout constants, so the pose library can reason about the body without
# re-deriving magic numbers. Front = -Y (she faces -Y), up = +Z, ground = z 0.
#
# Proportions matter more here than in the upright build: in profile the head has to
# sit ABOVE the body's top plane with a visible step, or head and body read as one
# undifferentiated slab. The first horizontal pass had a 1.5-long, 0.6-tall body with
# a same-height head butted onto it and looked like a bench.
# Shorter and chunkier than the first pass, ported from the Veo run (veo-output/) -
# its proportions read noticeably cuter at sprite size than this model's original
# longer, leaner body.
# CAT-vs-QUADRUPED PASS. She read as a goat or small dog, and that judgment is made
# from a single still frame - it's silhouette, not motion. Four changes, in order of
# how much recognition each one buys:
#
#   1. HEAD HEIGHT. The old head sat +0.43 above the back on a tall square shoulder
#      step and read as a dog. Dropping it to level with the back (+0.08) was worse -
#      head and body merged into one slab and she read as a cow. The head needs to be
#      a DISTINCT block sitting slightly proud of the back line: a small step, +0.26,
#      and pushed forward so it overhangs the chest.
#   2. REAR HAUNCH. Four identical posts read as a table. A cat profile has a thick
#      rear haunch mass, clearly distinct from the front leg.
#   3. LOW-SLUNG. Body deeper, legs shorter. The old 0.54 body on 0.50 legs was leggy;
#      cats are long and low.
#   4. SHORT MUZZLE. The old 0.12 protrusion was a snout. Cat muzzles barely exist.
BODY_LEN  = 0.90   # along Y
BODY_W    = 0.52   # along X
BODY_H    = 0.46   # along Z
LEG_H     = 0.40
BODY_Z    = LEG_H + BODY_H / 2 - 0.04
BODY_FRONT = -BODY_LEN / 2
BODY_BACK  =  BODY_LEN / 2

# The head is BIGGER THAN THE BODY IS DEEP, and wider than the body too. Measured off
# the Veo render (veo-output/), which is the version that actually read as a cat. Every
# hand-tuned pass before this had it backwards - small head, long body, big ears - and
# produced in turn a dog, a cow, a lamb and a rabbit. An oversized head on a small body
# is the whole cute-quadruped trick; the ears are a detail on top of it, not the star.
HEAD_S    = 0.66
# The head is WIDER THAN IT IS TALL. A cube head is what made the front view read as
# a slab: at the same width as the body there was no head silhouette at all, just one
# continuous column. Width is the free axis here - X is invisible to the profile
# camera - so the front view can be fixed without touching the walk at all.
HEAD_W    = 0.78
HEAD_Y    = -0.62
HEAD_Z    = BODY_Z + 0.30          # sits well proud of the back - a real shoulder step
FACE_Y    = HEAD_Y - HEAD_S / 2
CHEEK_X   = HEAD_W / 2
MUZZLE_Y  = FACE_Y - 0.04

# Idea.md's core mechanic is task-load -> fatness. On the upright cat that was X
# (width, facing the camera); in profile X is invisible, so fatness now has to read
# as belly depth in Z. LEG_H 0.50 against a 0.46 belly clearance leaves room for the
# belly to drop most of the way to the floor before the legs stop making sense.


def wipe():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures,
                bpy.data.actions, bpy.data.cameras, bpy.data.lights):
        for d in list(blk):
            blk.remove(d)
    PARTS.clear()
    L.MATS.clear()


# ----------------------------------------------------------------------------
# THE FACE, ONCE.
#
# Every pose needs the same head, and the poses are separate builds because rigid legs
# cannot fold. That combination is exactly how the standing and sitting cats drifted
# apart twice before - the sit kept obsolete ears after only the stander was fixed, and
# a whole face redesign had to be hand-transcribed into the sit with its own set of
# scaled magic numbers. Three poses would have made that three copies.
#
# So the face lives here and every build calls it. Proportions are expressed as
# fractions of the reference head (0.78 wide x 0.66 deep) and scaled, so a pose only
# has to say how big its head is.
FACE_REF_W = 0.78
FACE_REF_S = 0.66


def build_face(head_w, head_s, head_y, head_z, m_coat, m_w, m_k,
               eyes="open", ear_dy=0.0):
    """Place the head and everything on it. Shared by every pose build.

    `head_w` is the width (X) and `head_s` the depth and height (Y and Z). Width is
    the free axis - X is invisible to the profile camera - which is why the front view
    could be fixed without touching the walk.

    `ear_dy` staggers the two ears fore-and-aft. They normally sit at the same Y, so in
    profile they overlap into ONE narrow stub - which is why a lying pose's ear reads as
    a horn rather than an ear. Offsetting them shows two ear shapes side by side, the
    most compact unmistakable cat signal there is. Only worth it where the head has no
    other structure around it; the standing poses are verified byte-identical at 0.0 and
    must stay that way.

    `eyes="closed"` swaps the open eye for a dark curved lid, for sleeping poses. It
    is not a detail: a low curled body still reads as a cat resting, and closed eyes
    are what make it read as a cat ASLEEP. The lid keeps the open eye's width and
    vertical centre so she does not appear to squint or shift her gaze between states.
    """
    kw = head_w / FACE_REF_W          # scale for anything measured across the face
    k  = head_s / FACE_REF_S          # scale for anything measured up or back
    face_y   = head_y - head_s / 2
    muzzle_y = face_y - 0.04 * k
    cheek_x  = head_w / 2

    box("Head", 0, head_y, head_z, head_w, head_s, head_s, m_coat)

    # Cheek flare. A cat's head head-on is round, widest across the cheeks, and a
    # single box cannot give that. These sit inside the head's Y and Z envelope, so
    # they widen the face without appearing in profile at all.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("Cheek" + sfx, sx * (cheek_x + 0.03 * kw), head_y - 0.02 * k,
            head_z - 0.11 * k, 0.07 * kw, 0.42 * k, 0.26 * k, m_coat)

    # EARS ARE TRIANGLES - a three-tier taper, at the head's top CORNERS, ONE COLOUR.
    #
    # Both ear failures this project has had came from the same mistake: treating the
    # ear as a block with a height instead of a shape with a taper. Tall narrow ears
    # spaced wide apart read as a rabbit (twice). Narrow towers with dark caps read as
    # horns - a dark cap terminates the taper, so the ear becomes a separate post
    # instead of a triangle growing out of the head. Height is not what makes an ear
    # read. The taper is.
    ear_z = head_z + head_s / 2                                   # head's top plane
    for sx, sfx in ((-1, "L"), (1, "R")):
        ex = sx * 0.26 * kw
        ey = head_y - 0.05 * k + sx * ear_dy
        box("Ear" + sfx,    ex, ey, ear_z + 0.035 * k,
            0.24 * kw, 0.15 * k, 0.07 * k, m_coat)
        box("EarMid" + sfx, ex, ey, ear_z + 0.105 * k,
            0.17 * kw, 0.15 * k, 0.07 * k, m_coat)
        box("EarTip" + sfx, ex, ey, ear_z + 0.1625 * k,
            0.10 * kw, 0.15 * k, 0.045 * k, m_coat)
        # SMALL inner ear. Filling the ear made each one a pale mound, and being the
        # brightest thing on her head it pulled the eye up to the ears, not the face.
        box("InEar" + sfx,  ex, ey - 0.075 * k, ear_z + 0.04 * k,
            0.11 * kw, 0.05 * k, 0.06 * k, m_w)
        box("InEarT" + sfx, ex, ey - 0.075 * k, ear_z + 0.105 * k,
            0.07 * kw, 0.05 * k, 0.06 * k, m_w)

    # Muzzle PATCH, not a protruding snout, and WIDER THAN TALL - head-on a cat's
    # muzzle is two whisker pads side by side, not a square.
    box("Muzzle", 0, muzzle_y, head_z - 0.16 * k,
        0.30 * kw, 0.10 * k, 0.15 * k, m_w)
    box("Nose",   0, muzzle_y - 0.06 * k, head_z - 0.12 * k,
        0.10 * kw, 0.06 * k, 0.07 * k, m_k)
    # NO MOUTH. Every version tried here read as a frown - a "w" turned down at the
    # corners worst of all, but even a straight bar is a dark line on a white patch,
    # which is a grimace. Real cats barely show a mouth from the front. If a state
    # ever needs one (a yawn, a meow) it belongs to THAT state, not to the base face
    # that is on screen all day.

    # Eyes: white sclera, black VERTICAL slit pupil - the most cat-specific feature
    # available, and it does more species work per block than anything else here.
    # BIG and TALLER THAN WIDE: a wide flat eye reads as a narrowed one whatever the
    # pupil does, which is most of why she used to look permanently annoyed.
    for sx, sfx in ((-1, "L"), (1, "R")):
        if eyes == "closed":
            # A shut lid: a dark bar the width of the open eye, with a shorter one
            # below the outer half, so it reads as a curve rather than a dash.
            box("Eye" + sfx, sx * 0.165 * kw, face_y - 0.02 * k, head_z + 0.05 * k,
                0.20 * kw, 0.05 * k, 0.045 * k, m_k)
            box("Pup" + sfx, sx * 0.20 * kw, face_y - 0.02 * k, head_z + 0.015 * k,
                0.10 * kw, 0.05 * k, 0.045 * k, m_k)
            continue
        box("Eye" + sfx, sx * 0.165 * kw, face_y - 0.02 * k, head_z + 0.05 * k,
            0.20 * kw, 0.05 * k, 0.19 * k, m_w)
        box("Pup" + sfx, sx * 0.165 * kw, face_y - 0.045 * k, head_z + 0.05 * k,
            0.055 * kw, 0.05 * k, 0.15 * k, m_k)
    # Cheek set: THE SAME EYE, glued to the head's X faces for profile renders. A flat
    # decal seen edge-on is a meaningless sliver, so only the set facing the camera is
    # ever rendered.
    #
    # These have to match the front set on screen, and for a while they did not. When
    # the front eyes were redesigned - bigger, taller than wide, moved lower - this set
    # was left behind at the old flat geometry, so she had big round eyes head-on and
    # small squinting ones in profile. Same character, two different faces depending on
    # which way she was pointing.
    #
    # The projections differ, so matching means matching what LANDS ON SCREEN, not the
    # numbers: in profile the eye's Y depth becomes its screen width, where head-on
    # that came from X. Hence 0.20 on Y here against 0.20 on X above, and an identical
    # 0.19 height and head_z + 0.05 placement in both.
    #
    # They also have to sit OUTBOARD OF THE CHEEKS. In profile X is depth, so the cheek
    # blocks - which stick out to cheek_x + 0.065 to widen the face head-on - were
    # nearer the camera than the eye at cheek_x + 0.02 and quietly clipped its lower
    # half. Pushing the decals out costs nothing: in profile X only decides what is in
    # front of what, never where anything lands on screen.
    for sx, sfx in ((-1, "L"), (1, "R")):
        if eyes == "closed":
            box("EyeSide" + sfx, sx * (cheek_x + 0.10 * kw), head_y - 0.13 * k,
                head_z + 0.05 * k, 0.05, 0.20 * k, 0.045 * k, m_k)
            box("PupSide" + sfx, sx * (cheek_x + 0.125 * kw), head_y - 0.19 * k,
                head_z + 0.015 * k, 0.05, 0.10 * k, 0.045 * k, m_k)
            continue
        box("EyeSide" + sfx, sx * (cheek_x + 0.10 * kw), head_y - 0.13 * k,
            head_z + 0.05 * k, 0.05, 0.20 * k, 0.19 * k, m_w)
        box("PupSide" + sfx, sx * (cheek_x + 0.125 * kw), head_y - 0.15 * k,
            head_z + 0.05 * k, 0.05, 0.055 * k, 0.15 * k, m_k)


def tail_curve(points, x, thick0, thick1, mat, prefix="Tail", step=0.075):
    """Lay a tapering tail along a smooth curve, and return the part names.

    `points` is a polyline in the (y, z) plane - the plane the profile camera sees.
    It gets resampled at `step` and a cube dropped at every sample, so consecutive
    cubes overlap and the chain reads as one rounded tube instead of a jointed arm.
    Thickness eases from `thick0` at the base to `thick1` at the tip.

    Three straight boxes were tried first and a wrapped tail needs to be genuinely
    CURVED - it is the one part of a sleeping cat that is unmistakably cat, and a
    straight bar along the floor reads as a stick lying next to her.

    `x` is depth in profile, so it decides only what the tail draws in front of, never
    where it lands on screen. Put it outside everything else on the camera side.
    """
    # Cumulative length, so the resample is even along the curve rather than bunching
    # wherever the control points happen to be dense.
    segs, total = [], 0.0
    for (y0, z0), (y1, z1) in zip(points, points[1:]):
        d = math.hypot(y1 - y0, z1 - z0)
        segs.append(d); total += d

    names, placed, i, walked = [], 0, 0, 0.0
    n = max(1, int(total / step))
    for j in range(n + 1):
        want = total * j / n
        while i < len(segs) - 1 and walked + segs[i] < want:
            walked += segs[i]; i += 1
        t = 0.0 if segs[i] == 0 else (want - walked) / segs[i]
        y = points[i][0] + t * (points[i + 1][0] - points[i][0])
        z = points[i][1] + t * (points[i + 1][1] - points[i][1])
        th = thick0 + (thick1 - thick0) * (j / n)
        name = f"{prefix}{placed}"
        box(name, x, y, z, th, th, th, mat)
        names.append(name); placed += 1
    return names


# Every part build_face() creates, so a pose's bone map can just splice this in
# instead of listing them by hand and silently missing one.
FACE_PARTS = (["Head", "CheekL", "CheekR",
               "EarL", "EarR", "EarMidL", "EarMidR", "EarTipL", "EarTipR",
               "InEarL", "InEarR", "InEarTL", "InEarTR",
               "Muzzle", "Nose",
               "EyeL", "EyeR", "PupL", "PupR",
               "EyeSideL", "EyeSideR", "PupSideL", "PupSideR"])

FACE_FRONT_DECALS = ("EyeL", "EyeR", "PupL", "PupR",
                     "InEarL", "InEarR", "InEarTL", "InEarTR")
FACE_CHEEK_DECALS = ("EyeSideL", "EyeSideR", "PupSideL", "PupSideR")


# ----------------------------------------------------------------------------
def build_model():
    m_coat  = material("Coat", COAT, rough=1.0)
    m_under = material("Under", UNDER, rough=1.0)
    m_acc   = material("Accent", ACCENT, rough=1.0)
    m_w     = material("FaceW", FACE_W, rough=1.0)
    m_k     = material("FaceK", FACE_K, rough=1.0)

    box("Body",   0, 0, BODY_Z, BODY_W, BODY_LEN, BODY_H, m_coat)
    box("Chest",  0, -0.55, BODY_Z, 0.50, 0.34, 0.52, m_coat)
    box("Haunch", 0, BODY_BACK - 0.10, BODY_Z - 0.05, 0.58, 0.42, 0.48, m_coat)
    # Pale underside. Counter-shading is not styling: nearly every cat is lighter
    # underneath, and the eye reads its absence as wrong before it can say why.
    box("Belly", 0, 0, BODY_Z - BODY_H / 2 + 0.045, BODY_W + 0.01, BODY_LEN + 0.01,
        0.09, m_under)
    box("Bib", 0, BODY_FRONT - 0.15, BODY_Z - 0.06, 0.26, 0.12, 0.32, m_under)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # Tail stays BELOW the top of the head. It sits at x~0, dead centre between the
    # ears, so any taller and it pokes through the gap and reads as a third ear -
    # invisible in profile, obvious head-on.
    box("Tail1", 0, BODY_BACK + 0.07, BODY_Z + 0.19, 0.13, 0.13, 0.38, m_coat)
    box("Tail2", 0, BODY_BACK + 0.10, BODY_Z + 0.46, 0.12, 0.14, 0.22, m_coat)
    box("Tail3", 0, BODY_BACK - 0.04, BODY_Z + 0.55, 0.12, 0.28, 0.12, m_coat)

    # Pale legs with black boots. Back legs thicker than front, the way a cat's are.
    for name, x, y, w in (("LegFL", -0.18, -0.28, 0.21), ("LegFR", 0.18, -0.28, 0.21),
                          ("LegBL", -0.19,  0.32, 0.25), ("LegBR", 0.19,  0.32, 0.25)):
        box(name, x, y, LEG_H / 2, w, w, LEG_H, m_under)
        box("Toe" + name[3:], x, y - 0.02, 0.08, w + 0.01, w + 0.04, 0.16, m_acc)


# ----------------------------------------------------------------------------
# Spine now runs horizontally front-to-back, so rotating it arches the back rather
# than leaning a torso. Legs stay parented to root, not spine, so an arch keeps the
# feet planted - which is what a cat arching its back actually does.
BONES = {
    "root":     ((0, 0, 0),                        (0, 0, 0.15)),
    "spine":    ((0, BODY_FRONT + 0.10, BODY_Z),   (0, BODY_BACK, BODY_Z)),
    "head":     ((0, HEAD_Y + 0.20, HEAD_Z),       (0, FACE_Y, HEAD_Z)),
    "tailBase": ((0, BODY_BACK, BODY_Z),            (0, BODY_BACK + 0.07, BODY_Z + 0.42)),
    "tailMid":  ((0, BODY_BACK + 0.07, BODY_Z + 0.42), (0, BODY_BACK + 0.10, BODY_Z + 0.66)),
    "tailTip":  ((0, BODY_BACK + 0.10, BODY_Z + 0.66), (0, BODY_BACK - 0.16, BODY_Z + 0.70)),
    "legFL":    ((-0.18, -0.28, LEG_H), (-0.18, -0.28, 0)),
    "legFR":    (( 0.18, -0.28, LEG_H), ( 0.18, -0.28, 0)),
    "legBL":    ((-0.19,  0.32, LEG_H), (-0.19,  0.32, 0)),
    "legBR":    (( 0.19,  0.32, LEG_H), ( 0.19,  0.32, 0)),
}
BONE_PARENT = {
    "spine": "root", "head": "spine", "tailBase": "spine", "tailMid": "tailBase",
    "tailTip": "tailMid",
    "legFL": "root", "legFR": "root", "legBL": "root", "legBR": "root",
}
PART_BONE = {
    "spine": ["Body", "Chest", "Belly", "Haunch", "Bib"],
    "head": FACE_PARTS,
    "tailBase": ["Tail1"],
    "tailMid": ["Tail2"],
    "tailTip": ["Tail3"],
    "legFL": ["LegFL", "ToeFL"], "legFR": ["LegFR", "ToeFR"],
    "legBL": ["LegBL", "ToeBL"], "legBR": ["LegBR", "ToeBR"],
}


def build_armature():
    arm_data = bpy.data.armatures.new("CatRig")
    arm = bpy.data.objects.new("Loaf", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    for name, (h, t) in BONES.items():
        b = eb.new(name)
        b.head, b.tail = Vector(h), Vector(t)
        b.use_deform = True
    for child, parent in BONE_PARENT.items():
        eb[child].parent = eb[parent]
    bpy.ops.object.mode_set(mode="OBJECT")

    for bone_name, parts in PART_BONE.items():
        bone = arm_data.bones[bone_name]
        P_ = bone.matrix_local.copy()
        P_.translation = bone.matrix_local @ Vector((0, bone.length, 0))
        Pinv = P_.inverted()
        for pname in parts:
            ob = PARTS.get(pname)
            if not ob:
                print(f"  WARN missing part {pname}"); continue
            ob.parent = arm
            ob.parent_type = "BONE"
            ob.parent_bone = bone_name
            ob.matrix_parent_inverse = Pinv
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    return arm


def aim_camera(cam, loc, target):
    """Ortho views must stay axis-pure, so the caller offsets the camera to frame
    the subject instead of aiming off-axis (which would tilt the projection)."""
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# THE SPRITE CONTRACT. Every state, every angle, every future pose renders through
# these numbers - see SPRITE_CONTRACT.md. This is the one thing that is genuinely
# expensive to change once the app ships, because the app anchors sprites bottom-centre
# and any drift in scale or ground line makes her jump between states.
#
# The camera NEVER moves. Ported from lil-cleo's render_states.py: a fixed camera plus
# a character that rotates is the only way to guarantee identical scale and an
# identical ground row across every state. Moving the camera per view - which is what
# this file used to do - lets both drift silently.
SPRITE_W, SPRITE_H = 640, 512
SPRITE_ORTHO = 2.3          # horizontal world coverage (640 is the larger dimension)
SPRITE_CAM_Z = 0.83         # puts ground z=0 about 25px above the bottom edge
SPRITE_CAM_Y = -9.0

# World units per rendered pixel - the conversion the app-facing numbers below use.
SPRITE_UPP = SPRITE_ORTHO / SPRITE_W        # 0.00359 world units / px

# Profile recentring. The model is deliberately NOT symmetric about its own Y axis -
# the head projects well forward of the body - so rotating it into profile put the
# silhouette a measured +62px right of the canvas centre (side_idle +64, walk frames
# +49.5..+69.5, mean +61.6) while the front views sat dead on 320.
#
# That mismatch is a real bug, not a cosmetic one. The app anchors bottom-centre and
# mirrors for leftward travel with scaleEffect(x: -1) about the window centre, so an
# off-centre profile teleports her ~124px sideways every single time she turns around.
#
# Applied in world X and ONLY for side renders (see face()). It cannot be baked into
# the model, because in the front view world X *is* screen X and the same shift would
# push the front views off-centre instead.
SPRITE_SIDE_DX = -62 * SPRITE_UPP

# Landscape, not lil-cleo's portrait 512x640: Brick is a humanoid minifig and is taller
# than he is wide in every pose, but a quadruped cat in profile is the opposite - 2.03
# wide against 1.56 tall. Portrait cannot hold the standing profile without shrinking
# her so far that the sitting states waste most of the frame.


def sprite_stage():
    """Fixed sprite camera + FLAT voxel lighting. Shared by every state build.

    Hard SUN lamps aimed straight down the three axes, shadows off, specular killed.
    Every face of every block then takes exactly ONE flat value decided by which way
    it points - top bright, front mid, side dark. That crisp three-tone step is the
    entire voxel-art look. The soft three-point studio rig this replaces smeared a
    gradient across each face and made the whole model read as generic 3D; no palette
    change could compensate for it.
    """
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = SPRITE_ORTHO
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, SPRITE_CAM_Y, SPRITE_CAM_Z)
    cam.rotation_euler = (math.radians(90), 0, 0)   # dead-on -Y, axis-pure ortho
    bpy.context.scene.camera = cam

    def sun(name, rot, energy, color="#FFFFFF"):
        ld = bpy.data.lights.new(name, type="SUN")
        ld.energy = energy
        ld.angle = 0.0            # zero angular size = perfectly hard
        ld.use_shadow = False     # self-shadowing would break the flatness
        ld.color = rgb(color)[:3]
        ob = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(ob)
        ob.rotation_euler = rot
        return ob

    sun("Top",   (0, 0, 0), 2.5)                              # down  -> +Z faces
    sun("Front", (math.radians(90), 0, 0), 1.15, "#FFF6E8")   # +Y    -> -Y faces
    sun("Side",  (0, math.radians(-90), 0), 0.70, "#E6EEFF")  # +X    -> -X faces

    # Specular off everywhere. A hard sun on a glossy face blows a highlight, which
    # turned the eyes into flat white holes the first time this was tried. Voxel art
    # wants pure albedo: no gloss, no sheen, just the face's flat value.
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if not b:
            continue
        b.inputs["Roughness"].default_value = 1.0
        for k in ("Specular IOR Level", "Specular"):
            if k in b.inputs:
                b.inputs[k].default_value = 0.0

    world = bpy.data.worlds.new("W"); bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.30, 0.31, 0.35, 1)   # lifts unlit faces off black
    bg.inputs[1].default_value = 0.55

    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x, sc.render.resolution_y = SPRITE_W, SPRITE_H
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"   # AgX would desaturate the accents
    return cam


def face(arm, side, dx=None):
    """Turn the character, never the camera.

    Loaf's front is -Y and camera-right is +X, so +90 degrees about Z puts her in
    profile facing screen-right. Only right-facing sprites are rendered - the app
    mirrors them for leftward travel, exactly as lil-cleo's ImageCharacterView does
    with scaleEffect(x: facing).

    Side renders also get SPRITE_SIDE_DX applied in world X, which recentres the
    profile silhouette on the canvas. Front renders must NOT get it - there, world X
    is screen X, so the same shift would knock the front views off centre.
    """
    arm.rotation_euler[2] = math.radians(90 if side else 0)
    # `dx` overrides the recentring shift. SPRITE_SIDE_DX was measured on the STANDING
    # profile, and a different pose has a different silhouette, so a pose that lands
    # outside +-12px of centre needs its own measured value rather than this one.
    arm.location[0] = (SPRITE_SIDE_DX if dx is None else dx) if side else 0.0


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {path}")


def setup_viewport():
    """Make the GUI open on a coloured cat instead of a grey one.

    Saved .blend files carry their UI, so this sticks. Two independent things had to
    change: materials now set diffuse_color (catlib) so Solid shading has a colour to
    show at all, and the 3D viewports switch to Material Preview so you see the actual
    lit shaders. Harmless in background mode - screens exist there too.
    """
    for sc in bpy.data.screens:
        for area in sc.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                space.shading.type = "MATERIAL"
                space.shading.color_type = "MATERIAL"     # fallback if user hits Solid
                space.shading.studio_light = "forest.exr"
                space.shading.studiolight_background_alpha = 0.0
                space.overlay.show_floor = True
                space.overlay.show_axis_x = True
                space.overlay.show_axis_y = True


def face_collections(front_names, cheek_names):
    """Split the two eye-decal sets into toggleable collections.

    The renders hide whichever set is edge-on via hide_render, but hide_render is a
    render-only flag - in the GUI viewport BOTH sets are visible at once, so she shows
    up with four eyes: two on the face and two more stuck to her cheeks. Collections
    fix that: cheek decals start hidden in the viewport, and the monitor icon next to
    Face_Cheek / Face_Front in the outliner swaps which set you're looking at. Neither
    flag touches rendering, so the sprite output is unchanged.
    """
    scene_col = bpy.context.scene.collection
    for cname, names, hide in (("Face_Front", front_names, False),
                               ("Face_Cheek", cheek_names, True)):
        col = bpy.data.collections.new(cname)
        scene_col.children.link(col)
        for n in names:
            ob = PARTS.get(n)
            if not ob:
                continue
            if ob.name in scene_col.objects:
                scene_col.objects.unlink(ob)
            col.objects.link(ob)
        col.hide_viewport = hide


def show(names, visible):
    for n in names:
        PARTS[n].hide_render = not visible


FRONT_DECALS = FACE_FRONT_DECALS
CHEEK_DECALS = FACE_CHEEK_DECALS

# ----------------------------------------------------------------------------
WALK_FRAMES = 8                     # matches lil-cleo's WALK_FRAMES
LEG_SWING   = math.radians(24)
TAIL_SWAY   = math.radians(9)
HEAD_DIP    = math.radians(3)


def rest_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)


def render_walk(arm, n=WALK_FRAMES):
    """Walk in place, sampled into `walk1..N.png`.

    Two-beat diagonal gait - front-left swings with back-right, front-right with
    back-left - which is what Minecraft's mobs do and what rigid single-segment legs
    can actually express. A real four-beat cat walk needs knees to fold; these legs
    are solid blocks pivoting at the hip, so the honest move is to lean into the
    blocky gait rather than fake an anatomy the model doesn't have.

    She does NOT travel across the frame. The app moves the window; the sprite only
    animates. Travel baked into the sprite would fight it and break the anchor.
    """
    pb = arm.pose.bones
    for i in range(n):
        ph = 2 * math.pi * i / n
        swing = LEG_SWING * math.sin(ph)
        pb["legFL"].rotation_euler[0] =  swing
        pb["legBR"].rotation_euler[0] =  swing
        pb["legFR"].rotation_euler[0] = -swing
        pb["legBL"].rotation_euler[0] = -swing
        # tail counter-sways a quarter-cycle behind the legs, tip lagging the base -
        # the lag is what stops it reading as one rigid stick
        pb["tailBase"].rotation_euler[0] = TAIL_SWAY * math.sin(ph + math.pi / 2)
        pb["tailMid"].rotation_euler[0]  = TAIL_SWAY * math.sin(ph + math.pi / 3)
        pb["tailTip"].rotation_euler[0]  = TAIL_SWAY * 1.4 * math.sin(ph + math.pi / 6)
        pb["head"].rotation_euler[0]     = HEAD_DIP * math.sin(2 * ph)
        render_to(os.path.join(SPRITES, f"walk{i + 1}.png"))
    rest_pose(arm)


# ----------------------------------------------------------------------------
# THE JUMP, as six hand-set poses rather than a sine cycle.
#
# A walk is periodic, so procedural curves suit it. A jump is not - it is a sequence of
# distinct beats, and the beats are what sell it: gather, push, tuck, stretch, reach,
# absorb. Sampling a curve would flatten exactly the asymmetry that makes it read.
#
# SHE DOES NOT RISE IN THESE SPRITES. The arc is the app's job, for the same reason the
# walk doesn't travel: the sprite anchors bottom-centre, so lifting her inside the frame
# would fight that anchor, and jump HEIGHT and LENGTH need to be real tunable numbers on
# the app side rather than something baked into art. What the sprites carry is the pose;
# what the app carries is the parabola. The only vertical movement here is the crouch
# and the landing squash, which are pose, not trajectory.
#
# NOTHING HERE MAY DROP HER BELOW z=0. The first version sank the rig 0.10 for the
# crouch and 0.08 for the landing, which put her feet through the floor and took those
# frames' ground line from 24px to 0 - she would have sunk half a body into the dock at
# both ends of every jump. The crouch is carried by the spine arch and the leg angles
# instead, and the app adds the squash.
#
# `lift` compensates the rotating-foot dip. Swinging a rigid leg about the hip carries
# the boot's trailing corner below the vertical foot position, so every posed frame
# measures a few pixels under the 24px ground line. Airborne frames don't care - the
# app has her off the ground anyway - but frames 1 and 6 are her CROUCH and her
# LANDING, when she is stationary and in contact, and a sink there is visible at the
# start and end of every single jump. Those two are lifted back to exactly 24.
#
# Degrees, then lift in world units: (spine, front legs, back legs, tail, head, lift)
JUMP_POSES = [
    (  7, -20,  22, -14,   7, 0.032),   # 1 gather  - coiled, weight back
    (-11, -34, -26, -18,  -5, 0.000),   # 2 push    - body extends, back legs drive
    ( -5,  32,  36,  -8,  -7, 0.000),   # 3 tuck    - airborne, legs gathered up
    (  0, -20,  28,   8,  -2, 0.000),   # 4 stretch - apex, reaching out long
    (  6, -38,  12,  16,   5, 0.000),   # 5 reach   - front legs down for the ground
    ( 10, -12, -18,  12,   9, 0.018),   # 6 absorb  - landed, compressing
]


def render_jump(arm):
    """Six jump poses, sampled into `jump1..6.png`."""
    pb = arm.pose.bones
    for i, (spine, legf, legb, tail, head, lift) in enumerate(JUMP_POSES):
        arm.location[2] = lift
        pb["spine"].rotation_euler[0] = math.radians(spine)
        for b in ("legFL", "legFR"):
            pb[b].rotation_euler[0] = math.radians(legf)
        for b in ("legBL", "legBR"):
            pb[b].rotation_euler[0] = math.radians(legb)
        pb["tailBase"].rotation_euler[0] = math.radians(tail)
        pb["tailMid"].rotation_euler[0]  = math.radians(tail * 1.3)
        pb["tailTip"].rotation_euler[0]  = math.radians(tail * 1.6)
        pb["head"].rotation_euler[0]     = math.radians(head)
        render_to(os.path.join(SPRITES, f"jump{i + 1}.png"))
    arm.location[2] = 0.0
    rest_pose(arm)


# ----------------------------------------------------------------------------
def main():
    wipe()
    build_model()
    arm = build_armature()
    sprite_stage()
    setup_viewport()
    face_collections(FRONT_DECALS, CHEEK_DECALS)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print(f"SAVED {BLEND}")

    os.makedirs(SPRITES, exist_ok=True)

    # side_idle: the locomotion angle, and the app's fallback sprite for any state
    # that has no art yet. Cheek eyes only - the front decals are edge-on here.
    face(arm, side=True)
    show(CHEEK_DECALS, True); show(FRONT_DECALS, False)
    render_to(os.path.join(SPRITES, "side_idle.png"))

    # front_idle: standing, facing camera. Mostly head, chest and legs now that the
    # body runs away from the camera.
    face(arm, side=False)
    show(CHEEK_DECALS, False); show(FRONT_DECALS, True)
    render_to(os.path.join(SPRITES, "front_idle.png"))

    # walk1..8: locomotion, so profile only.
    face(arm, side=True)
    show(CHEEK_DECALS, True); show(FRONT_DECALS, False)
    render_walk(arm)
    render_jump(arm)


if __name__ == "__main__":
    main()
