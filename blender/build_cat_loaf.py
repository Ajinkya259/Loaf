"""Build the LOAF - her resting pose, in profile. The one she is named after.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_loaf.py

A "cat loaf" is a cat at rest with all four paws folded underneath, so the body
becomes one compact rounded block with a head on the front. It is the pose a cat
actually settles into on a desk, and it is where the app's name comes from.

WHY THIS AND NOT AN UPRIGHT SEATED PROFILE. Five passes were spent on an upright sit
in profile (build_cat_sit_side.py) and every one read as a kangaroo. The reason is
structural rather than a tuning problem: an upright seated cat in profile is a
VERTICAL STACK of same-coloured boxes, and a voxel character is read almost entirely
from its outline. Stacked blocks of one colour fuse into a single column, so the pose
has to be carried by negative space alone - and every block added to describe the
anatomy fills more of that space back in. Head-on the same pose works, because there
the bell taper across the width does the work.

A loaf has the opposite property, and it is why this reads where the sit did not: it
is WIDER THAN TALL, so the silhouette is carried by the top edge - the curve from the
tail up over the back and down the face. That is the same outline the standing profile
already reads correctly with, minus the legs.

The three things this pose has to get right:
  * NO VISIBLE LEGS. Legs are what make it a crouch instead of a loaf. Only a shallow
    pale shelf of folded paws shows at the front.
  * THE HEAD SITS ON THE BODY, not above it on a neck. Any gap turns it back into a
    seated pose.
  * THE TOP EDGE IS ONE CONTINUOUS CURVE, rump to shoulder to head, with no dip
    between the body and the head - the dip is what would read as a neck.
"""
import bpy, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catlib as L
from catlib import PARTS, material, box
from build_cat import (COAT, UNDER, ACCENT, FACE_W, FACE_K,
                       setup_viewport, face_collections, sprite_stage,
                       face, render_to, SPRITES, SPRITE_UPP,
                       build_face, FACE_PARTS, FACE_FRONT_DECALS, FACE_CHEEK_DECALS)

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat_loaf.blend")

# Front = -Y, up = +Z, ground = z 0.
#
# The body is the standing body, dropped to the floor and shortened. It stays clearly
# WIDER THAN TALL - that ratio is the entire difference between this working and the
# five failed upright attempts.
BODY_Y,  BODY_Z  = 0.06, 0.29     # z 0.03..0.55, y -0.36..0.48
BODY_LEN, BODY_H = 0.84, 0.52
BODY_W   = 0.56

# Same head as every other pose. She is the same cat sitting down as standing up, and
# a head that shrinks with the pose was the bug that made the front sit read weak.
HEAD_S,  HEAD_W  = 0.66, 0.78
# Low and forward, OVERLAPPING the body's front. A head perched above the body with
# any gap under it reads as a neck, and a neck reads as a seated cat, not a loaf.
HEAD_Y,  HEAD_Z  = -0.34, 0.74

# Measured after the first render; the standing SPRITE_SIDE_DX does not transfer,
# because this silhouette sits further forward.
LOAF_DX = -18 * SPRITE_UPP


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

    # One body block on the floor, plus a slightly taller haunch at the back. The step
    # between them is the only interruption in the top edge, and it sits behind the
    # head where a real cat's hips are.
    box("Body",   0, BODY_Y, BODY_Z, BODY_W, BODY_LEN, BODY_H, m_coat)
    box("Haunch", 0, 0.34,   0.26,   BODY_W + 0.02, 0.34, 0.46, m_coat)

    # Pale underside, as a thin strip at the very bottom. Counter-shading: nearly every
    # cat is lighter underneath and the eye notices its absence before it can say why.
    box("Belly", 0, BODY_Y, 0.075, BODY_W + 0.01, BODY_LEN + 0.01, 0.09, m_under)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # Chest fill under the chin. Without it the head overhangs into empty air and the
    # gap reads as a neck.
    box("Chest", 0, -0.30, 0.30, 0.50, 0.24, 0.44, m_coat)

    # THE TUCKED PAWS - the single detail that says "loaf" rather than "crouch".
    # A shallow pale shelf peeking out at the front, and nothing else. No leg blocks:
    # any visible leg turns the pose back into a crouch.
    box("PawL", -0.15, -0.40, 0.07, 0.20, 0.22, 0.14, m_under)
    box("PawR",  0.15, -0.40, 0.07, 0.20, 0.22, 0.14, m_under)
    box("ToeL", -0.15, -0.48, 0.06, 0.20, 0.10, 0.12, m_acc)
    box("ToeR",  0.15, -0.48, 0.06, 0.20, 0.10, 0.12, m_acc)

    # TAIL wrapped along the near flank and round the front paws, with the tip hooked
    # up clear of everything.
    #
    # At x=-0.34 it is entirely OUTSIDE the body in X and on the camera side (the
    # profile rotates her +90 about Z, putting local -X nearest the lens), so nothing
    # can draw over it. The first attempt at the seated profile put the tail inside the
    # body's X range and it vanished completely - the same occlusion trap that made the
    # tail invisible in this project's very first render.
    box("Tail1", -0.34,  0.26, 0.09, 0.13, 0.44, 0.13, m_coat)
    box("Tail2", -0.34, -0.14, 0.09, 0.13, 0.40, 0.13, m_coat)
    box("Tail3", -0.34, -0.44, 0.20, 0.13, 0.13, 0.26, m_coat)


# ----------------------------------------------------------------------------
# A loafing cat breathes, turns its head and flicks its tail. Nothing else moves -
# that stillness is the point of the pose.
BONES = {
    "root":     ((0, BODY_Y, 0),             (0, BODY_Y, 0.16)),
    "spine":    ((0, 0.30, BODY_Z),          (0, -0.20, BODY_Z + 0.08)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((-0.34, 0.46, 0.09),        (-0.34, 0.04, 0.09)),
    "tailTip":  ((-0.34, 0.04, 0.09),        (-0.34, -0.44, 0.11)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}
PART_BONE = {
    "root":  ["Body", "Haunch", "Belly", "PawL", "PawR", "ToeL", "ToeR"],
    "spine": ["Chest"],
    "head":  FACE_PARTS,
    "tailBase": ["Tail1"],
    "tailTip":  ["Tail2", "Tail3"],
}


def build_armature():
    arm_data = bpy.data.armatures.new("CatRigLoaf")
    arm = bpy.data.objects.new("LoafResting", arm_data)
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
    face(arm, side=True, dx=LOAF_DX)
    show(FACE_CHEEK_DECALS, True); show(FACE_FRONT_DECALS, False)
    render_to(os.path.join(SPRITES, "loaf.png"))


if __name__ == "__main__":
    main()
