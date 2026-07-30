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
# HER HEAD IS LOW. At z 0.52 it stood 0.45 clear of a 0.40-tall body and the pose read
# as a bottle - a tall vertical slab on a flat base. A cat lying on its side keeps its
# head near body height with the EARS as the highest point, and the whole silhouette
# stays long and low: 2.15 wide against 0.88 tall.
HEAD_Y,   HEAD_Z   = -0.56, 0.38    # z 0.05..0.71, ears to 0.90
NECK_Y,   NECK_Z   = -0.24, 0.13    # z 0..0.26 - LOW, so a notch opens above it
BODY_Y,   BODY_Z   =  0.16, 0.17    # z 0..0.34 - the DIP between head and hip
HAUNCH_Y, HAUNCH_Z =  0.56, 0.23    # z 0..0.46 - the hip bump

# THE TOP EDGE NEEDS THREE FEATURES, NOT ONE FLAT LINE.
#
# This is what six earlier passes at this pose all missed. Every state that reads well
# - idle, walk, both sits - is a VERTICAL composition: head, body and legs stack, so
# they separate from each other for free. Lying down is horizontal, so everything sits
# at one height and fuses into a bar, and no amount of detail inside that bar helps
# when the outline is all that survives at 160x128.
#
# So the outline is given shape deliberately: head HIGH at 0.71, a neck DIP to 0.26,
# the mid-body LOW at 0.34, then the hip BUMP back up to 0.46 before the tail. Four
# changes of direction along the top, where before there was one.

SLEEP_DX = -8 * SPRITE_UPP


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
    box("Haunch", 0, HAUNCH_Y, HAUNCH_Z, BODY_W + 0.04, 0.40, 0.46, m_coat)
    box("Body",   0, BODY_Y,   0.14,     BODY_W,        0.56, 0.28, m_coat)
    # THE FLANK is the only part that breathes, and it is split out purely so it CAN.
    #
    # It rides on top of the body, so it owns the visible top edge between neck and
    # hip - but its underside is 0.23 clear of the floor, with solid body beneath it.
    # That means it can rise and fall without any risk of a limb breaking through z=0,
    # which is exactly what happened when the whole spine breathed: the pivot sits 1.4
    # units from her extended front legs, so 2.6 degrees swung them 18px into the floor
    # and took one frame's ground line from 24px to 4px.
    box("Flank",  0, BODY_Y,   0.30,     BODY_W,        0.52, 0.14, m_coat)
    # THE NECK, and it is the point of this layout. It is deliberately LOW - it joins
    # the head to the body along the floor and stops at z 0.28, which opens a notch of
    # background above it between the back of her head and the front of her body.
    #
    # Without that notch head and body are one mass, and then the ear on top reads as a
    # horn growing out of a lump rather than as an ear on a head. It has to be a NOTCH
    # and not a gap, though: pulling the body back without a neck under it punches a
    # hole clean through her, which at sprite size is just a hole.
    box("Neck", 0, NECK_Y, NECK_Z, BODY_W - 0.06, 0.30, 0.26, m_coat)

    # Pale belly, but SHORT and central. She is lying on her side so the pale underside
    # should show - it just must not run the full length, because then it joins the
    # pale legs at both ends into one unbroken bar along the floor, which reads as a
    # shadow she is sitting on rather than as any part of her.
    box("Belly", 0, 0.16, 0.05, BODY_W + 0.01, 0.50, 0.10, m_under)

    # ear_dy staggers the two ears fore-and-aft. At the same Y they overlap into one
    # narrow stub in profile, which is why her ear read as a horn; offset, you get two
    # ear shapes, and that is the most compact unmistakable cat signal available. Worth
    # it here precisely because a lying head has no other structure around it.
    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k,
               eyes="closed", ear_dy=0.10)

    # FRONT LEGS REACHING FORWARD, flat along the ground and out past her nose.
    #
    # These are the pose. They sit entirely BELOW the head (head bottom 0.19, legs top
    # 0.18) because the head is wider in X, so it is nearer the camera and would draw
    # straight over them otherwise - which is exactly what killed the visible paws in
    # the loaf version.
    # They now reach out from under her CHIN rather than from under her head, which is
    # what lets the head sit low. Forward of the head's front edge there is nothing to
    # occlude them, so the clearance problem disappears instead of being worked around.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.14, -0.94, 0.09, 0.20, 0.30, 0.18, m_under)
        box("ToeF" + sfx, sx * 0.14, -1.05, 0.08, 0.21, 0.14, 0.16, m_acc)

    # A hind leg flopped out behind, so the back half is not a bare block.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegB" + sfx, sx * 0.15, 0.62, 0.09, 0.22, 0.30, 0.18, m_under)
        box("ToeB" + sfx, sx * 0.15, 0.80, 0.08, 0.23, 0.14, 0.16, m_acc)

    # TAIL laid out long behind her with a lazy flick at the tip. Behind is empty
    # background, so it always reads - and a straight-out tail is what a stretched-out
    # cat has, where a wrapped one belongs to a curl.
    # Kept inside the canvas on purpose. Stretched out she spans 2.05 world units
    # against the sprite's 2.3 - the widest state by a long way, and the first version
    # reached 630px of a 640px frame, one tweak from clipping.
    # Leaves from the TOP of the hip bump and sweeps down and out, so it is clear of
    # the body against empty background for most of its length.
    tail_curve([(0.72, 0.34), (0.86, 0.25), (0.97, 0.19), (1.04, 0.19), (1.08, 0.27)],
               -0.30, 0.14, 0.10, m_coat)


# ----------------------------------------------------------------------------
# A sleeping cat breathes and twitches a tail. That is the entire repertoire.
BONES = {
    "root":     ((0, 0.30, 0),               (0, 0.30, 0.16)),
    "spine":    ((0, 0.44, 0.26),            (0, -0.12, 0.30)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((-0.30, 0.72, 0.34),        (-0.30, 0.97, 0.19)),
    "tailTip":  ((-0.30, 0.97, 0.19),        (-0.30, 1.08, 0.27)),
}
# HEAD HANGS OFF ROOT, NOT SPINE. As a child of spine it inherited the breath, and
# with the spine pivot 1.35 units from her chin that swung the head's front-bottom
# corner 26px - straight through the floor on half the cycle. Only the flank breathes
# from the spine; the head gets its own much smaller nod.
BONE_PARENT = {"spine": "root", "head": "root",
               "tailBase": "root", "tailTip": "tailBase"}
TAIL_PARTS = []
PART_BONE = {
    # Everything that touches the floor stays on root, so nothing the breath drives
    # can ever reach z=0.
    "root":  ["Haunch", "Body", "Neck", "Belly",
              "LegFL", "LegFR", "ToeFL", "ToeFR",
              "LegBL", "LegBR", "ToeBL", "ToeBR"],
    "spine": ["Flank"],
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


# SHE BREATHES, and this is the single most important thing in the pose.
#
# A cat lying on the floor is a solid mass touching the ground along its whole length,
# so unlike every standing pose it has NO negative space inside its outline - and the
# holes between her legs are most of why the idle sprite reads. Seven passes of
# reshaping the outline could not manufacture the gaps this pose does not have.
#
# Motion is the way out. A shape that visibly breathes reads as a sleeping animal; the
# identical shape frozen reads as a rock. Four frames of a slow spine lift, played at
# 1.5fps, is one breath every 2.7 seconds - a real resting rate for a cat.
BREATH_FRAMES = 4
BREATH = math.radians(4.0)


def render_breath(arm):
    pb = arm.pose.bones
    for i in range(BREATH_FRAMES):
        ph = 2 * math.pi * i / BREATH_FRAMES
        # Tiny. A visible heave reads as panting, not sleeping - the whole effect
        # should be barely perceptible until you notice it isn't a still image.
        pb["spine"].rotation_euler[0] = BREATH * math.sin(ph)
        pb["head"].rotation_euler[0] = BREATH * 0.5 * math.sin(ph)
        # The tail lags a quarter cycle, so she doesn't pulse as one rigid object.
        pb["tailTip"].rotation_euler[0] = BREATH * 1.6 * math.sin(ph + math.pi / 2)
        render_to(os.path.join(SPRITES, f"sleep{i + 1}.png"))


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
    render_breath(arm)


if __name__ == "__main__":
    main()
