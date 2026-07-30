"""Build Loaf's SIT in PROFILE - the same angle she walks in.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sit_side.py

A separate build, because a sit cannot be posed on the standing rig: the legs are
single rigid blocks with no knee, so no rotation folds the haunches.

THREE BODY BLOCKS, NOT SEVEN. This is the lesson of seven failed passes, and it is not
about numbers at all.

Each earlier attempt tried to describe the pose with MORE geometry - haunch, body,
chest, belly, bib, paw, toe - stacked into a diagonal staircase, on the theory that
more anatomy reads as more cat. It does the opposite. Every extra block adds another
step to the outline, and the app draws her at 160x128, where the interior detail is
gone and the outline is all that is left. A busy outline reads as a lump.

The walking sprite works because it is four big clean shapes: body, head, legs, tail.
So this pose is built the same way. The silhouette is a clean L - a tall column at the
front carrying the head, a low shelf behind it on the ground, one notch of daylight
underneath between the front paw and the rump, and the tail standing clear above.

The other rule it obeys, learned the same expensive way: THE TAIL MUST CLEAR THE BACK
AND SIT AGAINST EMPTY BACKGROUND. It is the most identifying shape in her profile.
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
RUMP_Y,  RUMP_Z  = 0.26, 0.19     # z 0..0.38,    y -0.01..0.53  - the low shelf
CHEST_Y, CHEST_Z = -0.20, 0.50    # z 0.24..0.76, y -0.43..0.03  - the tall column
HEAD_Y,  HEAD_Z  = -0.32, 1.09    # z 0.76..1.42  - sits exactly on top of the column

LEG_H = 0.50      # the front legs reach the ground; the chest above them does not

# Measured after the first render; the standing SPRITE_SIDE_DX does not transfer.
SIT_SIDE_DX = -17 * SPRITE_UPP


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

    # The low shelf and the tall column, with NOTHING between them. The chest stops
    # 0.24 above the floor, so daylight shows under it between the front paw and the
    # rump. That notch is the pose - fill it in and she is a lump again.
    box("Rump",  0, RUMP_Y,  RUMP_Z,  BODY_W + 0.02, 0.54, 0.38, m_coat)
    box("Chest", 0, CHEST_Y, CHEST_Z, BODY_W - 0.02, 0.46, 0.52, m_coat)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # Front legs: one pale column down the front to the ground, with a dark boot. Both
    # sit at the same Y, so in profile they read as a single column - which is exactly
    # what a sitting cat's front legs look like side-on.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.18, -0.34, LEG_H / 2, 0.20, 0.20, LEG_H, m_under)
        box("ToeF" + sfx, sx * 0.18, -0.38, 0.08, 0.21, 0.26, 0.16, m_acc)

    # Pale bib down the front of the column, stopping above the leg. A wide one that
    # meets the leg is the NAPPY that CLAUDE.md lists as a failure class.
    box("Bib", 0, -0.44, 0.58, 0.22, 0.06, 0.30, m_under)

    # THE TAIL, standing well clear of the rump and hooking forward.
    #
    # Behind her, because behind her is empty background and across the front is not -
    # a tail routed across the front has to pass through the body, where profile depth
    # simply occludes it. That trap has now cost this project three renders: the very
    # first one it ever made, and twice on this pose.
    box("Tail1", 0, 0.56, 0.55, 0.13, 0.13, 0.50, m_coat)
    box("Tail2", 0, 0.59, 0.90, 0.12, 0.14, 0.26, m_coat)
    box("Tail3", 0, 0.45, 1.00, 0.12, 0.28, 0.12, m_coat)


# ----------------------------------------------------------------------------
# A sitting cat turns its head, flicks its tail and breathes. Nothing else moves.
BONES = {
    "root":     ((0, RUMP_Y, 0),             (0, RUMP_Y, 0.16)),
    "spine":    ((0, RUMP_Y, RUMP_Z),        (0, CHEST_Y, CHEST_Z + 0.26)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((0, 0.56, 0.30),            (0, 0.56, 0.80)),
    "tailTip":  ((0, 0.56, 0.80),            (0, 0.45, 1.06)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}
PART_BONE = {
    "root":  ["Rump", "LegFL", "LegFR", "ToeFL", "ToeFR"],
    "spine": ["Chest", "Bib"],
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
