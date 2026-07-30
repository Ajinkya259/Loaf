"""Build Loaf's SIT in PROFILE - the same angle she walks in.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sit_side.py

A separate build, because a sit cannot be posed on the standing rig: the legs are
single rigid blocks with no knee, so no rotation folds the haunches.

THE BACK IS A CURVE, NOT A STAIRCASE. This is what eight earlier passes got wrong, and
the mistake was subtler than it looks.

A sitting cat's profile is one continuous flowing line - up the front legs, over the
chest, up the neck, round the head, then a long curve down the back into the rump on
the ground. Every earlier attempt drew that line with two or three large boxes, which
gives 0.2-0.4 unit steps. At the 160x128 size the app actually draws her, those are
14-28 pixel corners: not a curve, a flight of stairs. She read as a lump every time.

The fix is the standard pixel-art one. A curve is drawn as MANY SMALL REGULAR STEPS,
not few big ones. Her body here is six horizontal slabs of falling length, each about
0.115 tall - roughly 3 pixels on screen - so the eye integrates them into one smooth
line instead of reading each as a corner.

HORIZONTAL slabs, and that detail cost a render of its own. An attempt with vertical
columns curved the top down and the underside up at once, which left a thin diagonal
band with no mass in it: she read as a lizard. A seated cat's back is close to UPRIGHT
above a heavy rounded rear, so the shape has to be layered in the direction the mass
actually stacks.

The count of blocks was never the point. Big irregular steps read as corners; small
regular ones read as a curve.

The other rule this obeys, learned expensively: THE TAIL MUST CLEAR THE BACK AND SIT
AGAINST EMPTY BACKGROUND. It is the most identifying shape in her whole profile.
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
BLEND = os.path.join(HERE, "cat_sit_side.blend")

# Front = -Y, up = +Z, ground = z 0.
#
# THE BODY AS A CURVE. Six horizontal slabs, floor upward: (z0, z1, y front, y back).
#
# Read down the fourth column and it is her back curving in as it rises - 0.46, 0.48,
# 0.45, 0.38, 0.28, 0.14 - which is the line that says "sitting cat" more than anything
# else in the pose. The third column is her chest, near-vertical with a slight bulge.
#
# Slabs, not columns. A first attempt curved the TOP down and the UNDERSIDE up at the
# same time, which left a thin diagonal band with no mass in it - she read as a lizard.
# A seated cat's back is close to UPRIGHT with a heavy rounded rear, so the shape has
# to be built in horizontal layers of falling length, not vertical ones of falling
# height.
BACK = [
    (0.000, 0.115, -0.30, 0.46),
    (0.115, 0.230, -0.35, 0.48),
    (0.230, 0.345, -0.37, 0.45),
    (0.345, 0.460, -0.39, 0.38),
    (0.460, 0.575, -0.40, 0.28),
    (0.575, 0.690, -0.39, 0.14),
]

SLAB_OVERLAP = 0.012   # slabs overlap in z; a gap would show as a seam through her

HEAD_Y, HEAD_Z = -0.34, 1.02     # z 0.69..1.35, sitting on the top slab
LEG_H = 0.50

# Measured after the first render; the standing SPRITE_SIDE_DX does not transfer.
SIT_SIDE_DX = -24 * SPRITE_UPP


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

    # The curved body, in horizontal layers. Width is constant: X is invisible to the
    # profile camera, so every unit of effort belongs in the Y-Z outline.
    for i, (z0, z1, y0, y1) in enumerate(BACK):
        # The overlap is added UPWARD, not centred. Centred, the bottom slab dipped
        # 0.006 below z=0 and pushed the sprite's ground line from 24px to 22px - she
        # would have sunk two pixels every time she sat down.
        box(f"Body{i}", 0, (y0 + y1) / 2, (z0 + z1) / 2 + SLAB_OVERLAP / 2,
            BODY_W, y1 - y0, z1 - z0 + SLAB_OVERLAP, m_coat)

    # NO pale belly strip in this pose. Standing, the underside is lit from below and a
    # pale band there reads as counter-shading. Sitting, that same band lies flat along
    # the ground line and reads as a mat she is perched on. Her pale goes on the chest
    # and the front legs instead, where it is doing the same job with none of the
    # ambiguity.

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # Front legs: one pale column to the ground with a dark boot. Both sit at the same
    # Y, so in profile they read as a single column - which is what a sitting cat's
    # front legs look like side-on.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.18, -0.34, LEG_H / 2, 0.20, 0.20, LEG_H, m_under)
        box("ToeF" + sfx, sx * 0.18, -0.38, 0.08, 0.21, 0.26, 0.16, m_acc)

    # Pale bib down the front of the chest, stopping above the leg. A wide one that
    # meets the leg is the NAPPY that CLAUDE.md lists as a failure class.
    box("Bib", 0, -0.40, 0.60, 0.22, 0.06, 0.26, m_under)

    # THE TAIL, curving up clear of the rump and hooking forward.
    #
    # Behind her, because behind her is empty background and across the front is not -
    # a tail routed across the front has to pass through the body, where profile depth
    # simply occludes it. That trap has now cost this project three renders: its very
    # first one, and twice on this pose.
    box("Tail1", 0, 0.50, 0.42, 0.13, 0.13, 0.44, m_coat)
    box("Tail2", 0, 0.52, 0.75, 0.12, 0.14, 0.24, m_coat)
    box("Tail3", 0, 0.39, 0.85, 0.12, 0.28, 0.12, m_coat)


# ----------------------------------------------------------------------------
# A sitting cat turns its head, flicks its tail and breathes. Nothing else moves.
BONES = {
    "root":     ((0, 0.25, 0),               (0, 0.25, 0.16)),
    "spine":    ((0, 0.20, 0.30),            (0, -0.10, 0.72)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((0, 0.50, 0.20),            (0, 0.50, 0.64)),
    "tailTip":  ((0, 0.50, 0.64),            (0, 0.39, 0.91)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}

# The slabs split at the waist, so a breathing spine lifts her chest without dragging
# her planted rump off the floor.
_WAIST = 3
PART_BONE = {
    "root":  [f"Body{i}" for i in range(_WAIST)]
             + ["LegFL", "LegFR", "ToeFL", "ToeFR"],
    "spine": [f"Body{i}" for i in range(_WAIST, len(BACK))] + ["Bib"],
    "head":  FACE_PARTS,
    "tailBase": ["Tail1"],
    "tailTip":  ["Tail2", "Tail3"],
}


def build_armature():
    arm_data = bpy.data.armatures.new("CatRigSitSide")
    arm = bpy.data.objects.new("LoafSitSide", arm_data)
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
    face(arm, side=True, dx=SIT_SIDE_DX)
    show(FACE_CHEEK_DECALS, True); show(FACE_FRONT_DECALS, False)
    render_to(os.path.join(SPRITES, "sit_side.png"))


if __name__ == "__main__":
    main()
