"""Build Loaf STRESSED - hunched, ears flat, in profile.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat_stressed.py

The machine-load half of the mechanic. Task load changes her BODY (see the weight
directories); machine load changes her POSTURE. Keeping them on separate axes is what
lets them compose - she can be fat and frightened at once, which is exactly the "too
much to do and the laptop is dying" case.

Three signals carry it, in order of how much each one buys:

  * EARS FLAT. The strongest thing a cat has. `build_face(ears="flat")` sweeps them
    back along the skull instead of standing them up, so the head's outline goes from
    pointed to rounded. Note the old claim that this was "blocked on ear bones" was
    wrong: that assumed posing the standing rig, but poses are separate BUILDS, so
    flat ears are just different geometry.
  * THE BACK ARCHES ABOVE THE HEAD. In every other state her head is the highest
    thing; here the shoulders are. That inversion is what reads as hunched, and it
    works at sprite size because it changes the outline rather than any detail.
  * PUPILS ROUND AND HUGE. `eyes="wide"`. Her normal vertical slit is the most
    cat-specific feature on the model, so losing it is precisely what alarm looks like.

Plus a low bristled tail held straight out behind, and short braced legs.
"""
import bpy, os, sys, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catlib as L
from catlib import PARTS, material, box
from build_cat import (COAT, UNDER, ACCENT, FACE_W, FACE_K, tail_curve,
                       setup_viewport, face_collections, sprite_stage,
                       face, render_to, SPRITES, SPRITE_UPP,
                       BODY_W, HEAD_S, HEAD_W, girth, belly,
                       build_face, FACE_PARTS, FACE_FRONT_DECALS, FACE_CHEEK_DECALS)

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat_stressed.blend")

# Front = -Y, up = +Z, ground = z 0.
#
# THE ARCH. Horizontal slabs of falling length, peaking BEHIND her shoulder at y≈0.07 -
# the Halloween-cat hump. Her head tops out at 0.71 and the arch at 0.74, so the back
# is the highest point in the pose, which is true in no other state she has.
# The first two attempts crouched her and kept the arch shallow - 0.74 against a
# normal back line of 0.82 - and she read as a lizard. A frightened cat does the
# opposite of making itself small: it goes UP, on stiff straight legs, with the back
# humped well ABOVE its own head. She now tops out higher than she stands.
ARCH = [
    (0.40, 0.52, -0.30, 0.46),
    (0.52, 0.64, -0.28, 0.44),
    (0.64, 0.76, -0.22, 0.40),
    (0.76, 0.88, -0.12, 0.32),
    (0.88, 0.98,  0.00, 0.22),
]
SLAB_OVERLAP = 0.012

HEAD_Y, HEAD_Z = -0.62, 0.52     # z 0.19..0.85 - held LOW, below the arch
LEG_H = 0.44                     # stiff and straight, not crouched

STRESS_DX = -52 * SPRITE_UPP


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

    for i, (z0, z1, y0, y1) in enumerate(ARCH):
        ym, yh = (y0 + y1) / 2, belly(y1 - y0)
        box(f"Body{i}", 0, ym, (z0 + z1) / 2 + SLAB_OVERLAP / 2,
            girth(BODY_W), yh, z1 - z0 + SLAB_OVERLAP, m_coat)

    # Chest, filling from the floor up to her chin. Without it the head hangs off the
    # front of the arch with daylight under it, and at sprite size background inside
    # the silhouette is not a gap - it is a hole.
    box("Chest", 0, -0.48, 0.34, girth(BODY_W - 0.04), 0.36, 0.68, m_coat)
    # NECK, bridging her head to the front of the arch.
    #
    # Without it the arch pulls back faster than the head does and a slot of background
    # opens between them at shoulder height - and at sprite size background inside the
    # silhouette is not a gap, it is a hole. She read as two separate objects.
    box("Neck", 0, -0.30, 0.62, girth(BODY_W - 0.08), 0.32, 0.36, m_coat)

    build_face(HEAD_W, HEAD_S, HEAD_Y, HEAD_Z, m_coat, m_w, m_k,
               eyes="wide", ears="flat")

    # Short braced legs. Crouched, not standing - she is making herself small.
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("LegF" + sfx, sx * 0.17, -0.36, LEG_H / 2, 0.20, 0.20, LEG_H, m_under)
        box("ToeF" + sfx, sx * 0.17, -0.39, 0.08, 0.21, 0.25, 0.16, m_acc)
        box("LegB" + sfx, sx * 0.18,  0.34, LEG_H / 2, 0.23, 0.23, LEG_H, m_under)
        box("ToeB" + sfx, sx * 0.18,  0.37, 0.08, 0.24, 0.27, 0.16, m_acc)

    # TAIL PUFFED AND STRAIGHT UP, which is the iconic frightened-cat shape and the
    # single most legible thing in the pose.
    #
    # The first version held it low and straight out behind, 1.5 units of thick bar
    # along the floor - she read as a crocodile. Length was the problem, not thickness:
    # a long horizontal tail dominates a compact body and flattens the whole
    # silhouette. Upright it adds height instead of width, and it sits against empty
    # sky above the arch where nothing can merge with it.
    #
    # Thicker than her normal tail throughout, because a frightened cat bristles.
    tail_curve([(0.36, 0.86), (0.48, 1.02), (0.56, 1.18), (0.58, 1.34)],
               -0.30, 0.21, 0.17, m_coat)


# ----------------------------------------------------------------------------
BONES = {
    "root":     ((0, 0.20, 0),               (0, 0.20, 0.16)),
    "spine":    ((0, 0.30, 0.46),            (0, -0.24, 0.58)),
    "head":     ((0, HEAD_Y + 0.24, HEAD_Z), (0, HEAD_Y - HEAD_S / 2, HEAD_Z)),
    "tailBase": ((-0.30, 0.40, 0.88),        (-0.30, 0.60, 1.20)),
    "tailTip":  ((-0.30, 0.60, 1.20),        (-0.30, 0.62, 1.36)),
}
BONE_PARENT = {"spine": "root", "head": "root",
               "tailBase": "root", "tailTip": "tailBase"}
PART_BONE = {
    "root":  ["Chest", "Neck", "LegFL", "LegFR", "ToeFL", "ToeFR",
              "LegBL", "LegBR", "ToeBL", "ToeBR"],
    "spine": [f"Body{i}" for i in range(len(ARCH))],
    "head":  FACE_PARTS,
    "tailBase": [],
    "tailTip":  [],
}


def build_armature():
    tail = sorted((n for n in PARTS if n.startswith("Tail")), key=lambda n: int(n[4:]))
    half = len(tail) // 2
    PART_BONE["tailBase"] = tail[:half]
    PART_BONE["tailTip"] = tail[half:]

    arm_data = bpy.data.armatures.new("CatRigStressed")
    arm = bpy.data.objects.new("LoafStressed", arm_data)
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


# A tense cat is not still - it trembles. Two frames of a tiny shiver, played fast,
# which is the same trick the sleeping breath uses in reverse: there the motion had to
# be slow to read as calm, here it has to be quick to read as alarm.
SHIVER_FRAMES = 2
SHIVER = math.radians(1.6)


def render_shiver(arm):
    pb = arm.pose.bones
    for i in range(SHIVER_FRAMES):
        d = SHIVER if i == 0 else -SHIVER
        pb["spine"].rotation_euler[0] = d
        pb["head"].rotation_euler[0] = -d * 0.7
        pb["tailTip"].rotation_euler[0] = d * 2.2
        render_to(os.path.join(SPRITES, f"stressed{i + 1}.png"))


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
    face(arm, side=True, dx=STRESS_DX)
    show(FACE_CHEEK_DECALS, True); show(FACE_FRONT_DECALS, False)
    render_shiver(arm)


if __name__ == "__main__":
    main()
