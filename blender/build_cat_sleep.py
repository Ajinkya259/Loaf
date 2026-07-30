"""Build Loaf CURLED UP ASLEEP, in profile.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sleep.py

The LOAF position - paws folded underneath, body a low mound, head up, eyes shut. The
pose the app is named after, and the one a cat actually settles into on a desk.

WHY NOT CURLED. Curled up is the classic sleeping position and it was built first, and
at 160x128 it was unreadable - a lumpy orange rock with a dark dash on it. The reason
is structural, not a tuning problem: curling TUCKS THE HEAD INTO THE BODY, and the head
is the single feature that identifies her as a cat. Ears, muzzle, eye, the step from
head to shoulder - all of it disappears into one mass, and flat voxel colour has no
fur, no shading and no outline to recover it with. A photograph of a curled cat reads
because of texture this style does not have.

The loaf keeps the head clear of the body, so ears and a shut eye still carry the
species, while the low wide mound and the absence of any leg still carry the sleep.

Two things carry the read, and neither is the body:

  * CLOSED EYES. A low curled body on its own reads as a cat resting. The shut lid is
    what makes it read as a cat ASLEEP. build_face(eyes="closed") keeps the open eye's
    width and centre so she doesn't appear to squint or shift her gaze between states.
  * THE TAIL WRAPPED PAST HER NOSE. Everything else here is one orange mass, so the
    tail is the only feature breaking the outline. It runs along the ground at
    x=-0.45 - outside even the head in X, on the camera side - and its tip carries on
    past her face into empty space, where nothing can occlude it, then hooks up.

Built as horizontal slabs of falling length, the same way the profile sit is: a curve
drawn as many small regular steps rather than a few big ones. See that file, and
CLAUDE.md, for why nine passes were needed to learn it.
"""
import bpy, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catlib as L
from catlib import PARTS, material, box
from build_cat import (COAT, UNDER, ACCENT, FACE_W, FACE_K, tail_curve,
                       setup_viewport, face_collections, sprite_stage,
                       face, render_to, SPRITES, SPRITE_UPP,
                       BODY_W, HEAD_S, HEAD_W,
                       build_face, FACE_PARTS, FACE_FRONT_DECALS, FACE_CHEEK_DECALS)

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat_sleep.blend")

# Front = -Y, up = +Z, ground = z 0.
#
# THE MOUND. Six horizontal slabs, floor upward: (z0, z1, y front, y back).
#
# Low and clearly WIDER THAN TALL - 1.45 across against 1.26 high including her ears,
# where the profile sit is 1.54 high. That difference is what says "resting" before
# any detail is read. Both edges pull in as it rises so it is a mound, not a box.
MOUND = [
    (0.000, 0.090, -0.36, 0.58),
    (0.090, 0.180, -0.40, 0.62),
    (0.180, 0.270, -0.40, 0.60),
    (0.270, 0.360, -0.36, 0.54),
    (0.360, 0.450, -0.26, 0.44),
    (0.450, 0.520, -0.10, 0.30),
]
SLAB_OVERLAP = 0.012   # added UPWARD, never centred, or the bottom slab breaks z=0

# Head UP and forward, resting on the front of the mound. Same size as every other
# pose - she is the same cat asleep as awake.
HEAD_Y, HEAD_Z = -0.50, 0.74     # z 0.41..1.07

TAIL_X = -0.45   # outside even the head (+-0.39) in X, and on the camera side

# Measured after the first render.
SLEEP_DX = -42 * SPRITE_UPP


def wipe():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.armatures,
                bpy.data.actions, bpy.data.cameras, bpy.data.lights):
        for d in list(blk):
            blk.remove(d)
    PARTS.clear()
    L.MATS.clear()


# ----------------------------------------------------------------------------
def build_model():
    m_coat  = material("Coat", COAT, rough=1.0)
    m_under = material("Under", UNDER, rough=1.0)
    m_acc   = material("Accent", ACCENT, rough=1.0)
    m_w     = material("FaceW", FACE_W, rough=1.0)
    m_k     = material("FaceK", FACE_K, rough=1.0)

    for i, (z0, z1, y0, y1) in enumerate(MOUND):
        box(f"Body{i}", 0, (y0 + y1) / 2, (z0 + z1) / 2 + SLAB_OVERLAP / 2,
            BODY_W, y1 - y0, z1 - z0 + SLAB_OVERLAP, m_coat)

    # Eyes shut. This is the state, not a detail - see the module docstring.
    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k, eyes="closed")

    # CHEST, filling from the floor up to her chin.
    #
    # Without it the head hangs forward of the mound with daylight underneath, and that
    # gap does not read as a neck - it reads as a hole punched through her, because at
    # sprite size a patch of background inside the silhouette is just a hole. A loafing
    # cat's chest does reach the ground; the head rests on top of it.
    # Deep enough to MEET the mound. At 0.34 it stopped at y=-0.37 while the mound
    # front had already pulled back to -0.26, leaving a slot of background between them
    # at shoulder height - another hole punched through her.
    box("Chest", 0, -0.50, 0.22, BODY_W - 0.04, 0.48, 0.44, m_coat)

    # Pale bib down the chest front. The only light note in the pose, and it has to sit
    # ABOVE the wrapped tail - anything pale at ground level here is simply drawn over.
    box("Bib", 0, -0.72, 0.28, 0.24, 0.06, 0.28, m_under)

    # NO LEGS AND NO PAWS. A visible leg turns a loaf into a crouch, and paws tucked at
    # ground level would be covered by the tail anyway.

    # THE TAIL, wrapped right round her and tucked up in front of her chest.
    #
    # A wrapped tail is mostly BEHIND the body in profile, so almost all of this curve
    # is correctly hidden. What has to read is the last third, arcing up through the
    # open space in front of her chest and below her chin - which is exactly where a
    # real loafing cat parks the tip.
    #
    # Laid along a RESAMPLED CURVE rather than as straight boxes. Three straight blocks
    # were tried and a wrapped tail has to be genuinely round, or it reads as a stick
    # lying next to her rather than as part of her.
    #
    # It stays clear of the muzzle (z 0.505 and up). Being nearer the camera the tail
    # draws over anything it shares screen space with, and an earlier version hooked
    # straight through her nose, which vanished.
    TAIL_PATH = [
        # The floor of this path is 0.072, not 0. A cube is placed ON each sample, so
        # its bottom sits half a thickness lower - at z 0.03 the tail broke through
        # z=0 and took the sprite's ground line from 24px to 14px.
        ( 0.60, 0.26), ( 0.52, 0.16), ( 0.38, 0.10), ( 0.18, 0.078),
        (-0.06, 0.072), (-0.30, 0.075), (-0.52, 0.09), (-0.70, 0.13),
        (-0.84, 0.21), (-0.92, 0.31), (-0.93, 0.42),
    ]
    global TAIL_PARTS
    TAIL_PARTS = tail_curve(TAIL_PATH, TAIL_X, 0.15, 0.10, m_coat)


# ----------------------------------------------------------------------------
# A sleeping cat breathes and flicks its tail. That is the entire repertoire.
BONES = {
    "root":     ((0, 0.20, 0),               (0, 0.20, 0.16)),
    "spine":    ((0, 0.26, 0.20),            (0, -0.20, 0.44)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((TAIL_X,  0.60, 0.26),      (TAIL_X, -0.06, 0.03)),
    "tailTip":  ((TAIL_X, -0.06, 0.03),      (TAIL_X, -0.93, 0.42)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}

_WAIST = 3
PART_BONE = {
    "root":  [f"Body{i}" for i in range(_WAIST)],
    "spine": [f"Body{i}" for i in range(_WAIST, len(MOUND))] + ["Chest", "Bib"],
    "head":  FACE_PARTS,
    # Filled in by build_armature(): the curve decides how many parts there are.
    "tailBase": [],
    "tailTip":  [],
}


TAIL_PARTS = []


def build_armature():
    # Split the resampled curve between the two tail bones, so a flick bends the tip
    # without swinging the whole wrap.
    half = len(TAIL_PARTS) // 2
    PART_BONE["tailBase"] = TAIL_PARTS[:half]
    PART_BONE["tailTip"] = TAIL_PARTS[half:]

    arm_data = bpy.data.armatures.new("CatRigSleep")
    arm = bpy.data.objects.new("LoafSleep", arm_data)
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


def show(names, visible):
    for n in names:
        PARTS[n].hide_render = not visible


def main():
    wipe()
    build_model()
    arm = build_armature()
    sprite_stage()
    setup_viewport()
    face_collections(FACE_FRONT_DECALS, FACE_CHEEK_DECALS)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print(f"SAVED {BLEND}")

    os.makedirs(SPRITES, exist_ok=True)
    face(arm, side=True, dx=SLEEP_DX)
    show(FACE_CHEEK_DECALS, True); show(FACE_FRONT_DECALS, False)
    render_to(os.path.join(SPRITES, "sleep.png"))


if __name__ == "__main__":
    main()
