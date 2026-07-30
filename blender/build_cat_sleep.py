"""Build Loaf ASLEEP - stretched out on her side, in profile.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_sleep.py

WHY STRETCHED OUT, AFTER CURLED AND LOAFED BOTH FAILED.

Curled up was built first - the classic sleeping position - and read as an orange rock.
The loaf was built second and read as an orange rock with a dash on it. Both failed for
the same reason, and it is not a tuning problem:

    A RESTING CAT IS A SINGLE ROUNDED MASS, AND A SINGLE ROUNDED MASS HAS NO OUTLINE
    FEATURES. At 160x128 with flat colour, no fur and no line art, the outline is the
    entire read. A photo of a curled cat works because of texture this style has none
    of. Curling actively removes the only things that identify her - it tucks the head
    into the body and hides every limb.

Stretched out is the opposite, and that is the whole argument for it. Lying on her
side, the pose puts BACK the features the other two hid: front legs reaching forward
clear of everything, a head that is a distinct bump at the front, a hind leg, and a
tail laid out long behind. Six or seven separate things on the outline instead of one
lump. It is also unmistakably asleep - nothing awake lies flat and stretched - and
maximally different from every other state she has, which are all upright.

The two rules the other poses taught, both obeyed here:

  * VALUE CONTRAST, not just outline. Every state that reads well has three values in
    it: orange body, pale legs, dark boots. The loaf had one and stayed a blob however
    good its silhouette got.
  * The legs must sit BELOW the head, not beside it. In profile the head is wider in X
    than the legs, so it is nearer the camera and would simply draw over them.
"""
import bpy, os, sys, math
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

# Front = -Y, up = +Z, ground = z 0. Everything is LOW - nothing reaches half the
# height of the profile sit, which is what says "flat out" at a glance.
HEAD_Y,   HEAD_Z   = -0.62, 0.52    # z 0.19..0.85 - clear above the extended legs
CHEST_Y,  CHEST_Z  = -0.34, 0.16
BODY_Y,   BODY_Z   =  0.20, 0.20
HAUNCH_Y, HAUNCH_Z =  0.58, 0.22

SLEEP_DX = -6 * SPRITE_UPP


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

    # A long low body: haunch, barrel, chest. Slightly different heights so the top
    # edge has some shape rather than being one flat plank.
    box("Haunch", 0, HAUNCH_Y, HAUNCH_Z, BODY_W + 0.04, 0.40, 0.44, m_coat)
    box("Body",   0, BODY_Y,   BODY_Z,   BODY_W,        0.80, 0.40, m_coat)
    box("Chest",  0, CHEST_Y,  CHEST_Z,  BODY_W - 0.04, 0.44, 0.32, m_coat)

    # Pale belly along the bottom. She is lying on her side, so this is the part of her
    # actually facing us - the one pose where the pale underside should be generous.
    box("Belly", 0, 0.10, 0.055, BODY_W + 0.01, 0.96, 0.11, m_under)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k, eyes="closed")

    # FRONT LEGS REACHING FORWARD, flat along the ground and out past her nose.
    #
    # These are the pose. They sit entirely BELOW the head (head bottom 0.19, legs top
    # 0.18) because the head is wider in X, so it is nearer the camera and would draw
    # straight over them otherwise - which is exactly what killed the visible paws in
    # the loaf version.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.14, -0.74, 0.09, 0.20, 0.44, 0.18, m_under)
        box("ToeF" + sfx, sx * 0.14, -0.97, 0.08, 0.21, 0.14, 0.16, m_acc)

    # A hind leg flopped out behind, so the back half is not a bare block.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegB" + sfx, sx * 0.15, 0.62, 0.09, 0.22, 0.38, 0.18, m_under)
        box("ToeB" + sfx, sx * 0.15, 0.84, 0.08, 0.23, 0.14, 0.16, m_acc)

    # TAIL laid out long behind her with a lazy flick at the tip. Behind is empty
    # background, so it always reads - and a straight-out tail is what a stretched-out
    # cat has, where a wrapped one belongs to a curl.
    # Kept inside the canvas on purpose. Stretched out she spans 2.05 world units
    # against the sprite's 2.3 - the widest state by a long way, and the first version
    # reached 630px of a 640px frame, one tweak from clipping.
    tail_curve([(0.76, 0.14), (0.88, 0.10), (0.99, 0.085), (1.08, 0.10), (1.14, 0.16)],
               -0.30, 0.14, 0.10, m_coat)


# ----------------------------------------------------------------------------
# A sleeping cat breathes and twitches a tail. That is the entire repertoire.
BONES = {
    "root":     ((0, 0.30, 0),               (0, 0.30, 0.16)),
    "spine":    ((0, 0.50, 0.20),            (0, -0.30, 0.24)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((-0.30, 0.76, 0.14),        (-0.30, 0.99, 0.085)),
    "tailTip":  ((-0.30, 0.99, 0.085),       (-0.30, 1.14, 0.16)),
}
BONE_PARENT = {"spine": "root", "head": "spine",
               "tailBase": "root", "tailTip": "tailBase"}
TAIL_PARTS = []
PART_BONE = {
    "root":  ["Haunch", "LegBL", "LegBR", "ToeBL", "ToeBR"],
    "spine": ["Body", "Chest", "Belly", "LegFL", "LegFR", "ToeFL", "ToeFR"],
    "head":  FACE_PARTS,
    "tailBase": [],
    "tailTip":  [],
}


def build_armature():
    tail = [n for n in PARTS if n.startswith("Tail")]
    tail.sort(key=lambda n: int(n[4:]))
    half = len(tail) // 2
    PART_BONE["tailBase"] = tail[:half]
    PART_BONE["tailTip"] = tail[half:]

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
