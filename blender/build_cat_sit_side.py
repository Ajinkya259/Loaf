"""Build Loaf's SIT in PROFILE - the same angle she walks in.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sit_side.py

A separate build, because a sit cannot be posed on the standing rig: the legs are
single rigid blocks with no knee, so no rotation folds the haunches.

DERIVED FROM THE STANDING PROFILE, NOT DESIGNED FROM SCRATCH. This matters, and it is
the whole reason this version works where five earlier ones did not.

Those five all started from "what does a sitting cat look like?" and built a new
silhouette - a bell, a three-step staircase back, an upright stack with negative space
cut into it. Every one read as a kangaroo, because an upright seated body in profile is
a column of same-coloured boxes and a voxel character is read almost entirely from its
outline.

This one starts from the standing profile, which already reads correctly, and applies
the only change a real cat makes when it sits down: THE REAR DROPS TO THE GROUND AND
THE FRONT STAYS UP. Same body, same head, same tail, same legs - the haunch slides down
to the floor, the back legs fold under it, and the front legs stay straight. The back
becomes a slope from a low rump to a high shoulder instead of a level line.

That is also this project's own rule applied properly for once: when hand-tuning starts
oscillating, stop guessing and measure a reference that already works. The reference was
never a photograph. It was the standing cat in the next file.
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
# The rear is on the floor and the front is held up, so the body runs UPHILL from back
# to front. Three blocks stepping up - haunch, body, chest - give that slope. They are
# the same blocks the standing build uses, at different heights.
HAUNCH_Y, HAUNCH_Z = 0.32, 0.25    # z 0..0.50 - the rump, planted
BODY_Y,   BODY_Z   = -0.10, 0.60   # z 0.38..0.82
CHEST_Y,  CHEST_Z  = -0.46, 0.68   # z 0.44..0.92

# Same head as every other pose, at the same total height as the front sit, so the two
# sits are unmistakably the same cat from either angle. Head is 52% of her height.
HEAD_Y,   HEAD_Z   = -0.55, 0.99

LEG_H = 0.46      # a little longer than standing: sitting, the front legs are locked

# Measured after the first render. The standing SPRITE_SIDE_DX does not transfer - this
# silhouette carries more of its mass behind the shoulder.
SIT_SIDE_DX = -46 * SPRITE_UPP


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

    # The uphill back line: rump on the floor, body, then shoulder.
    box("Haunch", 0, HAUNCH_Y, HAUNCH_Z, BODY_W + 0.06, 0.50, 0.50, m_coat)
    box("Body",   0, BODY_Y,   BODY_Z,   BODY_W,        0.56, 0.44, m_coat)
    box("Chest",  0, CHEST_Y,  CHEST_Z,  BODY_W - 0.02, 0.34, 0.48, m_coat)

    # Pale underside along the belly, exactly as the standing build has it. Counter-
    # shading: nearly every cat is lighter underneath, and the eye reads its absence as
    # wrong before it can say why.
    box("Belly", 0, BODY_Y, BODY_Z - 0.22 + 0.045, BODY_W + 0.01, 0.57, 0.09, m_under)
    # Chest bib. Narrow, and clear of the legs - a wide one meeting them is the NAPPY
    # that CLAUDE.md lists as a failure class.
    box("Bib", 0, CHEST_Y - 0.17, CHEST_Z - 0.04, 0.24, 0.08, 0.34, m_under)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # Front legs: straight, locked, under the shoulder. The same blocks as standing.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.18, -0.46, LEG_H / 2, 0.21, 0.21, LEG_H, m_under)
        box("ToeF" + sfx, sx * 0.18, -0.48, 0.08, 0.22, 0.25, 0.16, m_acc)

    # The folded back foot, poking forward from under the rump. It leaves a clear gap to
    # the front boots, and that gap is the one piece of negative space this pose needs -
    # without it the whole underside is a solid bar and she reads as sitting on a plinth.
    # TUCKED AGAINST THE HAUNCH, not out in front of it. Set forward at y=-0.02 with a
    # dark toe cap of its own, the pair read at display size as a pale block and a dark
    # block lying detached under her - dropped debris rather than a foot. The dark cap
    # is gone and the paw now overlaps the haunch, so it reads as part of her.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("PawB" + sfx, sx * 0.19, 0.08, 0.075, 0.23, 0.34, 0.15, m_under)

    # THE SAME HOOKED TAIL as the standing build, dropped to match the lowered rump.
    #
    # Behind her, not curled round the front. A tail routed across the front has to pass
    # through the body, and in profile X is depth, so it is simply occluded - the trap
    # that made the tail invisible in this project's first ever render, and again on the
    # first attempt at this pose. Behind the rump is empty screen space, so it always
    # reads.
    # It has to RISE CLEAR OF THE BACK LINE. This is the single most identifying shape
    # in her profile: in the walk the tail stands well above the back and hooks
    # forward against empty background, and that read is most of why the walking
    # sprite works at 160px.
    #
    # The first version of this pose topped the tail out at z 0.83 against a back at
    # 0.82, so it merged straight into the body mass and the whole silhouette went
    # amorphous. Judged at full render size it looked fine; at display size it was
    # gone. Now it clears the back by 0.33, matching the standing pose's 0.38.
    box("Tail1", 0, 0.62, 0.70, 0.13, 0.13, 0.50, m_coat)
    box("Tail2", 0, 0.65, 1.02, 0.12, 0.14, 0.26, m_coat)
    box("Tail3", 0, 0.51, 1.11, 0.12, 0.28, 0.12, m_coat)


# ----------------------------------------------------------------------------
# A sitting cat turns its head, flicks its tail and breathes. Nothing else moves.
BONES = {
    "root":     ((0, HAUNCH_Y, 0),           (0, HAUNCH_Y, 0.16)),
    "spine":    ((0, HAUNCH_Y, HAUNCH_Z),    (0, CHEST_Y, CHEST_Z + 0.24)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((0, 0.62, 0.45),            (0, 0.62, 0.95)),
    "tailTip":  ((0, 0.62, 0.95),            (0, 0.51, 1.17)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}
PART_BONE = {
    "root":  ["Haunch", "PawBL", "PawBR",
              "LegFL", "LegFR", "ToeFL", "ToeFR"],
    "spine": ["Body", "Belly", "Chest", "Bib"],
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
