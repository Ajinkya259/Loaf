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
# TWO MASSES ONLY: a rump on the ground at the back, and a narrow chest column at
# the front. THE GAP BETWEEN THEM IS THE POSE.
#
# Four earlier passes all produced a kangaroo, and the reason was the same every time:
# the silhouette was a solid mass from the ground to the head. That is what a seated
# bear is. A seated cat's profile is defined by three pieces of NEGATIVE space - under
# the chest between the front paws and the folded hind foot, under the chin where the
# head overhangs the chest, and behind the neck where the head is deeper than the
# chest. A three-step staircase back was tried and made it worse, because every extra
# block fills more of the silhouette in.
RUMP_Y,  RUMP_Z  = 0.26, 0.20     # z 0..0.40, y 0.00..0.52
CHEST_Y, CHEST_Z = -0.20, 0.52    # z 0.30..0.74 - bottom clear of the ground

# Same head as every other pose, and the same total height as the front sit, so the
# three states read as one cat. Head is 52% of her height in both.
HEAD_S,  HEAD_W  = 0.66, 0.78
HEAD_Y,  HEAD_Z  = -0.20, 0.99

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

    # Rump on the ground at the back. Nothing between it and the chest.
    box("Rump",  0, RUMP_Y,  RUMP_Z,  0.54, 0.52, 0.40, m_coat)
    # Narrow chest column, bottom CLEAR OF THE GROUND. 0.40 deep against a 0.66 head,
    # which buys 0.13 of chin overhang at the front and 0.13 of notch behind the neck -
    # the two undercuts that stop head and body fusing into one column.
    box("Chest", 0, CHEST_Y, CHEST_Z, 0.48, 0.40, 0.44, m_coat)

    # Pale bib down the chest front. Narrow, and stopping above the legs - a wide one
    # meeting them is the NAPPY that CLAUDE.md lists as a failure class.
    box("Bib", 0, -0.41, 0.54, 0.22, 0.06, 0.30, m_under)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k)

    # FOLDED HIND LEG, pulled BACK so it does not meet the front paws. The 0.12 gap it
    # leaves is the under-chest negative space, and that gap is doing more work for
    # this silhouette than any block in it.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("Hock" + sfx, sx * 0.24, 0.14, 0.09, 0.15, 0.44, 0.18, m_coat)
        box("PawB" + sfx, sx * 0.24, -0.02, 0.07, 0.17, 0.20, 0.14, m_under)

    # Front legs: vertical posts under the chin, pale with dark boots, as in every pose.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.15, -0.30, 0.22, 0.18, 0.20, 0.44, m_under)
        box("ToeF" + sfx, sx * 0.15, -0.36, 0.08, 0.19, 0.26, 0.16, m_acc)

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
    box("Tail1", -0.34,  0.24,  0.08, 0.13, 0.48, 0.13, m_coat)
    box("Tail2", -0.34, -0.22,  0.08, 0.13, 0.46, 0.13, m_coat)
    box("Tail3", -0.34, -0.51,  0.20, 0.13, 0.13, 0.28, m_coat)


# ----------------------------------------------------------------------------
# A sitting cat turns its head, flicks its tail and breathes. Nothing else moves.
BONES = {
    "root":     ((0, RUMP_Y, 0),            (0, RUMP_Y, 0.18)),
    "spine":    ((0, RUMP_Y, RUMP_Z),       (0, CHEST_Y, CHEST_Z + 0.26)),
    "head":     ((0, HEAD_Y + 0.22, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((-0.34, 0.45, 0.08),       (-0.34, -0.05, 0.08)),
    "tailTip":  ((-0.34, -0.05, 0.08),      (-0.34, -0.62, 0.10)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}
PART_BONE = {
    "root":  ["Rump", "HockL", "HockR", "PawBL", "PawBR",
              "LegFL", "LegFR", "ToeFL", "ToeFR"],
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
