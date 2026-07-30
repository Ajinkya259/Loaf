"""Build Loaf's SIT pose in PROFILE.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sit_side.py

A third build, because a sit cannot be posed on the standing rig (rigid single-segment
legs cannot fold a knee) and the front sit cannot simply be rendered from the side.

That second point is the whole reason this file exists rather than an extra render in
build_cat_sit.py. An early attempt did exactly that and the result read as a marmot:
the front sit's silhouette is a BELL, tiers narrowing upward, and a bell is a shape in
X - the width axis, which is exactly what a profile camera cannot see. Seen edge-on it
flattens into a featureless slab. That failure is often quoted here as "a sit doesn't
survive profile", but it is really "front-designed geometry doesn't survive profile".

A sit designed FOR profile reads better than the front one, not worse. Head-on, a
sitting cat hides its entire body behind its head; in profile you get the whole
diagnostic shape at once - rump planted on the ground, back rising to the shoulder,
straight front legs, head up and forward, tail curled around the paws. For a
quadruped, profile is the informative angle.

It also fixes a behavioural glitch. She walks the dock in profile, and on reaching a
corner she used to snap round to face the camera to sit down. Nothing turns 90 degrees
to sit. With this she stays in profile the whole way.

The silhouette rules, since they differ from the front sit's:
  * The BACK LINE carries the pose - a clear rise from a low rump to a high shoulder.
    Flat, and she reads as a loaf of bread; too steep, and she reads as a begging dog.
  * The FOLDED HIND LEG must be visible as its own shape along the ground, or the
    rump reads as a sack she is sitting on rather than part of her.
  * The TAIL must clear the body's silhouette in Y and Z. In the front sit it sweeps
    across in X, which from a side camera is depth - it would vanish into the body
    entirely. This is the same occlusion trap that made the tail invisible in the very
    first render this project ever produced.
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
BLEND = os.path.join(HERE, "cat_sit_side.blend")

# Front = -Y, up = +Z, ground = z 0. Same convention as every other build.
#
# The back is a THREE-STEP STAIRCASE - rump, loin, shoulder - not a single step. One
# step gave a low box behind a vertical column, which read as a kangaroo: the whole
# character of a sitting cat is in the diagonal from the ground to the shoulder.
RUMP_Y,  RUMP_Z  = 0.22, 0.19
LOIN_Y,  LOIN_Z  = 0.02, 0.44
TORSO_Y, TORSO_Z = -0.08, 0.58

# THE HEAD IS THE SAME SIZE AS WHEN SHE IS STANDING. It is the same cat.
#
# This was the real reason the first two attempts read as a kangaroo, not the back
# line. The front sit uses a 0.50 head against the stander's 0.66 - she loses a
# quarter of her head the moment she sits down - and copying that scale here left a
# small head on a tall stacked body, which is a kangaroo's proportions exactly.
#
# An oversized head on a small body is the whole cute-quadruped trick and it is
# already recorded as this project's most valuable proportion lesson. It applies to
# every pose, not just the standing one.
HEAD_S,  HEAD_W  = 0.64, 0.76
# Sits OVER the chest, only slightly forward. At -0.36 it overhung by 0.23 and she
# read as begging.
HEAD_Y,  HEAD_Z  = -0.34, 1.10

# Measured after the first render: the standing SPRITE_SIDE_DX is -62px, but this pose
# has a different silhouette - taller, and its mass sits further back - so it needs its
# own recentring shift rather than inheriting one measured on the stander.
SIT_SIDE_DX = -32 * SPRITE_UPP


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

    # The back line, as a rising staircase: rump on the ground, loin, then shoulder.
    box("Rump",  0, RUMP_Y,  RUMP_Z,  0.54, 0.62, 0.38, m_coat)
    box("Loin",  0, LOIN_Y,  LOIN_Z,  0.52, 0.50, 0.40, m_coat)
    box("Torso", 0, TORSO_Y, TORSO_Z, 0.48, 0.42, 0.44, m_coat)

    # Pale bib down the chest front. Narrow, and stopping well above the legs - a wide
    # one meeting the legs is the NAPPY that CLAUDE.md lists as a failure class and
    # that came back in the front sit the moment it was recoloured.
    box("Bib", 0, -0.30, 0.56, 0.22, 0.06, 0.28, m_under)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # FOLDED HIND LEG. The single most cat-specific thing in a profile sit: the thigh
    # stays high and back while the shin folds forward flat along the ground, so the
    # foot ends up beside the front paws. Without it the rump is just a box on the floor.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("Hock" + sfx, sx * 0.24, 0.05, 0.09, 0.15, 0.52, 0.18, m_coat)
        box("PawB" + sfx, sx * 0.24, -0.26, 0.07, 0.17, 0.22, 0.14, m_under)

    # Front legs: straight vertical posts under the shoulder, pale with dark boots,
    # the same as every other pose.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.15, -0.38, 0.25, 0.18, 0.22, 0.50, m_under)
        box("ToeF" + sfx, sx * 0.15, -0.44, 0.08, 0.19, 0.28, 0.16, m_acc)

    # TAIL, and the only part of this pose that needs real care.
    #
    # A profile camera occludes by depth, so a tail tucked inside the body's X range is
    # simply gone - which is what happened on the first attempt at x=-0.22 against a
    # body spanning +-0.27. This is the same trap that made the tail invisible in the
    # very first render this project ever produced.
    #
    # Two things fix it. It sits at x=-0.34, entirely OUTSIDE the body in X and on the
    # camera side (rotating +90 about Z for the profile puts her local -X nearest the
    # lens), so nothing can ever draw over it. And its route is chosen so the part that
    # matters lands in EMPTY screen space: the run along the ground passes behind her
    # legs, which is where a real tail would be, and the tip emerges and hooks up in
    # front of her front paws (front edge y=-0.52), where nothing else is. The upturn
    # is what stops the forward sweep reading as a doormat.
    box("Tail1", -0.34,  0.20,  0.08, 0.13, 0.50, 0.13, m_coat)
    box("Tail2", -0.34, -0.30,  0.08, 0.13, 0.52, 0.13, m_coat)
    box("Tail3", -0.34, -0.62,  0.20, 0.13, 0.13, 0.28, m_coat)


# ----------------------------------------------------------------------------
# A sitting cat turns its head, flicks its tail and breathes. Nothing else moves.
BONES = {
    "root":     ((0, RUMP_Y, 0),            (0, RUMP_Y, 0.18)),
    "spine":    ((0, RUMP_Y, RUMP_Z),       (0, TORSO_Y, TORSO_Z + 0.28)),
    "head":     ((0, HEAD_Y + 0.22, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((-0.34, 0.45, 0.08),       (-0.34, -0.05, 0.08)),
    "tailTip":  ((-0.34, -0.05, 0.08),      (-0.34, -0.62, 0.10)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}
PART_BONE = {
    "root":  ["Rump", "HockL", "HockR", "PawBL", "PawBR",
              "LegFL", "LegFR", "ToeFL", "ToeFR"],
    "spine": ["Loin", "Torso", "Bib"],
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
    sprite_stage()          # the same fixed camera and canvas as every other state
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
