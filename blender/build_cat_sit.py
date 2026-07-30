"""Build Loaf's SIT pose - front facing.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sit.py

Why this is a separate build and not a pose on the standing rig: the standing legs are
single rigid blocks with no knee, so nothing you rotate will fold the haunches. A real
sit changes which blocks exist - the back legs collapse into a wide rump the cat rests
on, and the front legs become straight vertical posts. So the sit gets its own geometry
laying out the same block vocabulary and the same palette, imported from build_cat.

It still gets a rig, cut down to what a sitting cat actually does: turn its head, flick
its tail, and breathe. No leg bones - a sitting cat's legs don't go anywhere.

Front-facing ONLY, and that's a rule rather than a preference. lil-cleo's
render_states.py splits its angles the same way: profile is for locomotion (side_idle,
walk, run) and everything expressive is rendered front-on. A sit isn't locomotion. It
also doesn't survive profile - the bell taper that makes the pose read lives in X, the
width axis, which is exactly what a side camera cannot see, so in profile she flattens
into a slab. An early side render of this pose read as a marmot.
"""
import bpy, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catlib as L
from catlib import PARTS, material, box
from build_cat import (COAT, UNDER, ACCENT, FACE_W, FACE_K,
                       setup_viewport, face_collections, sprite_stage,
                       face, render_to, SPRITES)

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat_sit.blend")

# Silhouette target: a bell. Widest at the rump on the ground, tapering up through the
# torso to a narrow head, with two straight front legs dropped down the centre and the
# tail curled around the front. That taper is the whole reason a sit reads as a sit.
RUMP_W   = 0.76     # each tier must be clearly narrower than the one below it, or the
TORSO_W  = 0.60     # stack reads as a box tower instead of a cat
HEAD_S   = 0.50
HEAD_W   = 0.60     # wider than tall, for the same reason as the standing build
RUMP_Z   = 0.21     # rump centre; sits flat on the ground
TORSO_Z  = 0.65
HEAD_Z   = 1.14
HEAD_Y   = -0.06
FACE_Y   = HEAD_Y - HEAD_S / 2
MUZZLE_Y = FACE_Y - 0.06
CHEEK_X  = HEAD_W / 2


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
    m_fur   = material("Coat", COAT, rough=1.0)
    m_shade = material("Under", UNDER, rough=1.0)
    m_ink   = material("Accent", ACCENT, rough=1.0)
    m_toe   = m_ink
    m_eye   = material("FaceW", FACE_W, rough=1.0)
    m_nose  = material("FaceK", FACE_K, rough=1.0)
    m_ear   = m_eye

    # Rump: the folded back legs, read as one wide block resting on the ground.
    box("Rump",  0, 0.14, RUMP_Z, RUMP_W, 0.54, 0.42, m_fur)
    box("Torso", 0, 0.04, TORSO_Z, TORSO_W, 0.44, 0.58, m_fur)
    # NARROW chest bib that stops well clear of the legs.
    #
    # This block was 0.34 wide and 0.46 tall, and directly below it sat two pale front
    # legs almost touching at the centre line. Together they made one unbroken cream
    # panel from chin to floor - the NAPPY, which CLAUDE.md already lists as a known
    # failure class from the white build. It came straight back the moment the sit was
    # recoloured. A cat has a white BIB, a patch with coat visible on both sides of it,
    # never a white front panel.
    box("Bib", 0, -0.19, TORSO_Z + 0.06, 0.20, 0.14, 0.30, m_shade)

    box("Head", 0, HEAD_Y, HEAD_Z, HEAD_W, HEAD_S, HEAD_S, m_fur)
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("Cheek" + sfx, sx * (HEAD_W / 2 + 0.022), HEAD_Y - 0.015, HEAD_Z - 0.085,
            0.05, 0.32, 0.20, m_fur)

    # Same three-tier tapered ear as the standing build, scaled to this smaller head.
    # No dark tip: a cap terminates the taper and each ear reads as a post instead of
    # a triangle. Small inner, or it becomes the brightest thing on her head.
    ear_z = HEAD_Z + HEAD_S / 2
    for sx, sfx in ((-1, "L"), (1, "R")):
        ex = sx * 0.20
        box("Ear" + sfx,    ex, HEAD_Y - 0.04, ear_z + 0.027, 0.18, 0.12, 0.055, m_fur)
        box("EarMid" + sfx, ex, HEAD_Y - 0.04, ear_z + 0.081, 0.13, 0.12, 0.055, m_fur)
        box("EarTip" + sfx, ex, HEAD_Y - 0.04, ear_z + 0.125, 0.08, 0.12, 0.035, m_fur)
        box("InEar" + sfx,  ex, HEAD_Y - 0.10, ear_z + 0.030, 0.08, 0.04, 0.045, m_ear)
        box("InEarT" + sfx, ex, HEAD_Y - 0.10, ear_z + 0.081, 0.05, 0.04, 0.045, m_ear)

    box("Muzzle", 0, MUZZLE_Y, HEAD_Z - 0.12, 0.23, 0.10, 0.11, m_eye)
    box("Nose",   0, MUZZLE_Y - 0.06, HEAD_Z - 0.09, 0.08, 0.06, 0.055, m_nose)
    # No mouth - every version of one read as a frown. See the standing build.

    # Big round eyes with a vertical slit, not wide flat slabs. A wide flat eye reads
    # as a narrowed one whatever the pupil does, and that was most of why she looked
    # permanently annoyed.
    box("EyeL", -0.125, FACE_Y - 0.02, HEAD_Z + 0.04, 0.15, 0.05, 0.145, m_eye)
    box("EyeR",  0.125, FACE_Y - 0.02, HEAD_Z + 0.04, 0.15, 0.05, 0.145, m_eye)
    box("PupL", -0.125, FACE_Y - 0.045, HEAD_Z + 0.04, 0.042, 0.05, 0.115, m_nose)
    box("PupR",  0.125, FACE_Y - 0.045, HEAD_Z + 0.04, 0.042, 0.05, 0.115, m_nose)
    box("EyeSideL", -CHEEK_X - 0.04, HEAD_Y - 0.09, HEAD_Z + 0.04, 0.05, 0.11, 0.11, m_eye)
    box("EyeSideR",  CHEEK_X + 0.04, HEAD_Y - 0.09, HEAD_Z + 0.04, 0.05, 0.11, 0.11, m_eye)

    # Front legs, set WIDE APART so the coat shows between them. They stay pale, to
    # match the standing build - what caused the nappy was the two of them meeting at
    # the centre line under a wide bib, not the colour itself.
    for name, x in (("LegFL", -0.20), ("LegFR", 0.20)):
        box(name, x, -0.30, 0.24, 0.19, 0.22, 0.48, m_shade)
        box("Toe" + name[3:], x, -0.33, 0.09, 0.20, 0.28, 0.18, m_toe)
    # Back paws peeking out beside the rump - without them the base reads as a plinth.
    # Kept clear of the front boots, or the whole base becomes one black bar.
    for name, x in (("PawBL", -0.36), ("PawBR", 0.36)):
        box(name, x, -0.10, 0.07, 0.18, 0.30, 0.14, m_toe)

    # Tail curled around the front, the way a sitting cat parks it over its own paws.
    # Runs back along the right flank, sweeps across the front, then hooks up at the
    # tip - the upturn is what stops the front sweep reading as a doormat.
    #
    # COAT-coloured, not accent. It was accent here and coat in the standing build, so
    # her tail changed colour depending on whether she was sitting down - and being
    # dark it also merged with the boots and back paws into a single black bar along
    # the floor that read as a plinth. Left over from the white-cat palette, where the
    # tail genuinely was black.
    box("Tail1", 0.45, 0.15, 0.10, 0.14, 0.50, 0.14, m_fur)
    box("Tail2", 0.22, -0.40, 0.10, 0.50, 0.14, 0.14, m_fur)
    box("Tail3", -0.06, -0.40, 0.22, 0.14, 0.14, 0.22, m_fur)


# ----------------------------------------------------------------------------
# Cut-down rig: a sitting cat turns its head, flicks its tail and breathes. That's it.
BONES = {
    "root":     ((0, 0.10, 0),          (0, 0.10, 0.18)),
    "spine":    ((0, 0.10, RUMP_Z),     (0, 0.02, TORSO_Z + 0.25)),
    "head":     ((0, HEAD_Y + 0.20, HEAD_Z), (0, FACE_Y, HEAD_Z)),
    "tailBase": ((0.45, 0.40, 0.10),    (0.45, -0.10, 0.10)),
    "tailTip":  ((0.45, -0.10, 0.10),   (-0.06, -0.40, 0.10)),
    "legFL":    ((-0.15, -0.30, 0.48),  (-0.15, -0.30, 0)),
    "legFR":    (( 0.15, -0.30, 0.48),  ( 0.15, -0.30, 0)),
}
BONE_PARENT = {
    "spine": "root", "head": "spine", "tailBase": "root", "tailTip": "tailBase",
    "legFL": "root", "legFR": "root",
}
PART_BONE = {
    "root": ["Rump", "PawBL", "PawBR"],
    "spine": ["Torso", "Bib"],
    "head": ["Head", "CheekL", "CheekR",
             "EarL", "EarR", "EarMidL", "EarMidR", "EarTipL", "EarTipR",
             "InEarL", "InEarR", "InEarTL", "InEarTR",
             "Muzzle", "Nose",
             "EyeL", "EyeR", "PupL", "PupR", "EyeSideL", "EyeSideR"],
    "tailBase": ["Tail1"],
    "tailTip": ["Tail2", "Tail3"],
    "legFL": ["LegFL", "ToeFL"], "legFR": ["LegFR", "ToeFR"],
}


def build_armature():
    arm_data = bpy.data.armatures.new("CatRigSit")
    arm = bpy.data.objects.new("LoafSit", arm_data)
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


# ----------------------------------------------------------------------------
# Content spans x -0.35..0.47, y -0.50..0.40, z 0..1.64. The tail pushes the mass
# slightly to +X, so the front camera offsets to match rather than sitting on centre.
VIEW_X, VIEW_Z = 0.06, 0.82


def show(names, visible):
    for n in names:
        PARTS[n].hide_render = not visible


FRONT_DECALS = ("EyeL", "EyeR", "PupL", "PupR",
                "InEarL", "InEarR", "InEarTL", "InEarTR")
CHEEK_DECALS = ("EyeSideL", "EyeSideR")


# ----------------------------------------------------------------------------
def main():
    wipe()
    build_model()
    arm = build_armature()
    sprite_stage()          # same fixed camera + canvas as every other state
    setup_viewport()
    face_collections(FRONT_DECALS, CHEEK_DECALS)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print(f"SAVED {BLEND}")

    os.makedirs(SPRITES, exist_ok=True)
    face(arm, side=False)
    show(FRONT_DECALS, True); show(CHEEK_DECALS, False)
    render_to(os.path.join(SPRITES, "sit.png"))


if __name__ == "__main__":
    main()
