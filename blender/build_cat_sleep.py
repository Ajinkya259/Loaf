"""Build Loaf CURLED UP ASLEEP, in profile.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sleep.py

The classic cat sleeping position, and the one that reads best at sprite size: head
down flat, body curled into a low rounded mound, tail wrapped around the front with
the tip resting past her nose.

WHY CURLED AND NOT ONE OF THE OTHERS. A cat has a dozen recognisable sleeping poses -
belly up, sideways, paws over the face - but almost all of them are read from limb
detail, which is exactly what disappears when a 640x512 render is drawn at 160x128.
Curled up is read from the OUTLINE alone: one low wide dome. That also makes it
maximally distinct from every other state Loaf has, since idle, walk and both sits are
all upright with the head held high. At a glance, low and round means asleep.

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
from build_cat import (COAT, UNDER, ACCENT, FACE_W, FACE_K,
                       setup_viewport, face_collections, sprite_stage,
                       face, render_to, SPRITES, SPRITE_UPP,
                       BODY_W, HEAD_S, HEAD_W,
                       build_face, FACE_PARTS, FACE_FRONT_DECALS, FACE_CHEEK_DECALS)

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat_sleep.blend")

# Front = -Y, up = +Z, ground = z 0.
#
# THE DOME. Six horizontal slabs, floor upward: (z0, z1, y front, y back).
#
# Both edges pull inward as it rises, which is what makes it a mound rather than a
# box: the front runs -0.24, -0.30, -0.30, -0.24, -0.12, 0.04 and the back 0.60, 0.66,
# 0.64, 0.58, 0.48, 0.34. Widest just off the floor, exactly like a sleeping cat
# spreading slightly under its own weight.
# HER BACK ARCHES ABOVE HER HEAD. At six slabs the dome topped out at 0.60 against a
# head reaching 0.67, so the head stood proud of the body and the pair read as two
# lumps. A curled cat tucks its head LOW and arches its back over it, so the dome has
# to be the tallest thing in the pose.
DOME = [
    (0.000, 0.100, -0.24, 0.60),
    (0.100, 0.200, -0.30, 0.66),
    (0.200, 0.300, -0.30, 0.64),
    (0.300, 0.400, -0.26, 0.60),
    (0.400, 0.500, -0.18, 0.54),
    (0.500, 0.600, -0.06, 0.46),
    (0.600, 0.700,  0.08, 0.36),
    (0.700, 0.780,  0.20, 0.26),
]
SLAB_OVERLAP = 0.012   # added UPWARD, never centred, or the bottom slab breaks z=0

# The head rests ON THE FLOOR at the front, tucked against the body. Same size as
# every other pose - she is the same cat asleep as awake.
HEAD_Y, HEAD_Z = -0.44, 0.34     # z 0.01..0.67

TAIL_X = -0.45   # outside even the head (+-0.39) in X, and on the camera side

# Measured after the first render.
SLEEP_DX = -52 * SPRITE_UPP


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

    for i, (z0, z1, y0, y1) in enumerate(DOME):
        box(f"Body{i}", 0, (y0 + y1) / 2, (z0 + z1) / 2 + SLAB_OVERLAP / 2,
            BODY_W, y1 - y0, z1 - z0 + SLAB_OVERLAP, m_coat)

    # Eyes shut. This is the state, not a detail - see the module docstring.
    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k, eyes="closed")

    # One folded front paw peeking out under her chin. No legs: a curled cat has
    # nothing else showing, and a visible leg would turn the pose into a crouch.
    box("PawL", -0.15, -0.62, 0.075, 0.20, 0.26, 0.15, m_under)
    box("PawR",  0.15, -0.62, 0.075, 0.20, 0.26, 0.15, m_under)

    # THE TAIL, wrapped round the front and past her nose.
    #
    # Everything else in this pose is one orange mass, so the tail is the only thing
    # breaking the outline and it has to be unmistakable. It runs the length of her at
    # ground level, which is where a wrapped tail physically goes, and most of that run
    # is hidden behind her - correctly. What matters is the last stretch, which carries
    # on past her face (head front is -0.77) into empty space and then hooks up. That
    # part cannot be occluded by anything.
    # The hooked tip must also CLEAR HER MUZZLE. Being nearer the camera, the tail
    # draws over anything it shares screen space with, and the first version curled up
    # straight through the muzzle patch - so her nose vanished and the tip read as
    # part of her face. It now hooks up beyond y=-0.87, forward of the muzzle at
    # -0.86..-0.76.
    box("Tail1", TAIL_X,  0.38, 0.075, 0.13, 0.50, 0.15, m_coat)
    box("Tail2", TAIL_X, -0.14, 0.075, 0.13, 0.54, 0.15, m_coat)
    box("Tail3", TAIL_X, -0.62, 0.075, 0.13, 0.52, 0.15, m_coat)
    box("Tail4", TAIL_X, -0.95, 0.200, 0.13, 0.16, 0.22, m_coat)


# ----------------------------------------------------------------------------
# A sleeping cat breathes and flicks its tail. That is the entire repertoire.
BONES = {
    "root":     ((0, 0.20, 0),               (0, 0.20, 0.16)),
    "spine":    ((0, 0.30, 0.24),            (0, -0.10, 0.42)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((TAIL_X,  0.63, 0.075),     (TAIL_X, -0.41, 0.075)),
    "tailTip":  ((TAIL_X, -0.41, 0.075),     (TAIL_X, -0.99, 0.100)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}

_WAIST = 3
PART_BONE = {
    "root":  [f"Body{i}" for i in range(_WAIST)] + ["PawL", "PawR"],
    "spine": [f"Body{i}" for i in range(_WAIST, len(DOME))],
    "head":  FACE_PARTS,
    "tailBase": ["Tail1", "Tail2"],
    "tailTip":  ["Tail3", "Tail4"],
}


def build_armature():
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
