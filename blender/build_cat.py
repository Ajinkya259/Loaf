"""Build the Deskitty voxel cat from scratch in Blender, headless.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/build_cat.py

Second pass: the cat is now a **horizontal quadruped** - body running front-to-back
along Y, standing on four legs - instead of the upright bear-like figure of the first
pass (kept at cat_upright.blend / build_cat_upright.py.bak). Same 10-block grammar and
fur spec from the style pitch, re-proportioned so the silhouette reads as a cat.

The hero view is now the **side profile**, which is what a desktop pet walking across
the screen actually shows. That flips two things the upright version got for free:
the face has to live on the head's side faces (not just the front), and the key light
has to move to the camera side.

Re-runnable: wipes the scene and rebuilds from nothing every time.
"""
import bpy, os, sys, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catlib as L
from catlib import PARTS, material, box, rgb

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "cat.blend")
SPRITES = os.path.join(HERE, "sprites")   # all state sprites, one shared canvas

# COMMITTED PALETTE - bicolour ginger with a monochrome face.
#
# Coat: orange back, head and tail; pale belly and legs; black socks. Chosen because
# orange is the one body colour that never loses against a light desktop, which is
# where the earlier white cat kept failing.
#
# Face: white and black only, no exceptions. It borrows nothing from the coat, so the
# same face works on any colourway and she stays one character instead of becoming a
# different cat every time the body changes. It is also the highest contrast anywhere
# on the model, landing exactly where you want the eye to go first.
#
# Every value here cleared a contrast audit in CIE L*: coat-to-underside gap >= 25,
# accent darker than L*22. Nine of thirteen earlier colourways failed it.
COAT      = "#E8944A"   # back, head, tail
UNDER     = "#F6F1E7"   # belly, bib, legs - a cat is always paler underneath
ACCENT    = "#2B2B33"   # socks and ear tips: the dark anchors that hold the silhouette
FACE_W    = "#FBF8F4"   # sclera, muzzle patch, inner ear
FACE_K    = "#1A1A1E"   # pupil, nose, mouth

# Alternate colourways live in blender/explore_pattern.py; swapping COAT/UNDER/ACCENT
# for any validated set there is the whole change.

# ----------------------------------------------------------------------------
# Layout constants, so the pose library can reason about the body without
# re-deriving magic numbers. Front = -Y (she faces -Y), up = +Z, ground = z 0.
#
# Proportions matter more here than in the upright build: in profile the head has to
# sit ABOVE the body's top plane with a visible step, or head and body read as one
# undifferentiated slab. The first horizontal pass had a 1.5-long, 0.6-tall body with
# a same-height head butted onto it and looked like a bench.
# Shorter and chunkier than the first pass, ported from the Veo run (veo-output/) -
# its proportions read noticeably cuter at sprite size than this model's original
# longer, leaner body.
# CAT-vs-QUADRUPED PASS. She read as a goat or small dog, and that judgment is made
# from a single still frame - it's silhouette, not motion. Four changes, in order of
# how much recognition each one buys:
#
#   1. HEAD HEIGHT. The old head sat +0.43 above the back on a tall square shoulder
#      step and read as a dog. Dropping it to level with the back (+0.08) was worse -
#      head and body merged into one slab and she read as a cow. The head needs to be
#      a DISTINCT block sitting slightly proud of the back line: a small step, +0.26,
#      and pushed forward so it overhangs the chest.
#   2. REAR HAUNCH. Four identical posts read as a table. A cat profile has a thick
#      rear haunch mass, clearly distinct from the front leg.
#   3. LOW-SLUNG. Body deeper, legs shorter. The old 0.54 body on 0.50 legs was leggy;
#      cats are long and low.
#   4. SHORT MUZZLE. The old 0.12 protrusion was a snout. Cat muzzles barely exist.
BODY_LEN  = 0.90   # along Y
BODY_W    = 0.52   # along X
BODY_H    = 0.46   # along Z
LEG_H     = 0.40
BODY_Z    = LEG_H + BODY_H / 2 - 0.04
BODY_FRONT = -BODY_LEN / 2
BODY_BACK  =  BODY_LEN / 2

# The head is BIGGER THAN THE BODY IS DEEP, and wider than the body too. Measured off
# the Veo render (veo-output/), which is the version that actually read as a cat. Every
# hand-tuned pass before this had it backwards - small head, long body, big ears - and
# produced in turn a dog, a cow, a lamb and a rabbit. An oversized head on a small body
# is the whole cute-quadruped trick; the ears are a detail on top of it, not the star.
HEAD_S    = 0.66
HEAD_Y    = -0.62
HEAD_Z    = BODY_Z + 0.30          # sits well proud of the back - a real shoulder step
FACE_Y    = HEAD_Y - HEAD_S / 2
CHEEK_X   = HEAD_S / 2
MUZZLE_Y  = FACE_Y - 0.04

# Idea.md's core mechanic is task-load -> fatness. On the upright cat that was X
# (width, facing the camera); in profile X is invisible, so fatness now has to read
# as belly depth in Z. LEG_H 0.50 against a 0.46 belly clearance leaves room for the
# belly to drop most of the way to the floor before the legs stop making sense.


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

    box("Body",   0, 0, BODY_Z, BODY_W, BODY_LEN, BODY_H, m_coat)
    box("Chest",  0, -0.55, BODY_Z, 0.50, 0.34, 0.52, m_coat)
    box("Haunch", 0, BODY_BACK - 0.10, BODY_Z - 0.05, 0.58, 0.42, 0.48, m_coat)
    # Pale underside. Counter-shading is not styling: nearly every cat is lighter
    # underneath, and the eye reads its absence as wrong before it can say why.
    box("Belly", 0, 0, BODY_Z - BODY_H / 2 + 0.045, BODY_W + 0.01, BODY_LEN + 0.01,
        0.09, m_under)
    box("Bib", 0, BODY_FRONT - 0.15, BODY_Z - 0.06, 0.26, 0.12, 0.32, m_under)

    box("Head", 0, HEAD_Y, HEAD_Z, HEAD_S, HEAD_S, HEAD_S, m_coat)
    # Ears small relative to the head - about a fifth of its height. Scaled up they
    # read as a rabbit, every time.
    ear_z = HEAD_Z + HEAD_S / 2 + 0.07
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("Ear" + sfx,    sx * 0.19, HEAD_Y - 0.05, ear_z, 0.17, 0.15, 0.14, m_coat)
        box("EarTip" + sfx, sx * 0.19, HEAD_Y - 0.05, ear_z + 0.09, 0.12, 0.11, 0.05, m_acc)
        box("InEar" + sfx,  sx * 0.19, HEAD_Y - 0.125, ear_z + 0.01, 0.10, 0.05, 0.09, m_w)

    # Contrasting muzzle PATCH, not a protruding snout. This is the single biggest
    # thing the reference design had that the hand-built one didn't.
    box("Muzzle", 0, MUZZLE_Y, HEAD_Z - 0.15, 0.30, 0.10, 0.20, m_w)
    box("Nose",   0, MUZZLE_Y - 0.06, HEAD_Z - 0.08, 0.11, 0.06, 0.07, m_k)
    for sx in (-1, 1):
        box(f"Mouth{sx}",  sx * 0.055, MUZZLE_Y - 0.055, HEAD_Z - 0.19, 0.07, 0.05, 0.04, m_k)
        box(f"MouthD{sx}", sx * 0.09,  MUZZLE_Y - 0.055, HEAD_Z - 0.215, 0.05, 0.05, 0.04, m_k)

    # Eyes: white sclera, black VERTICAL pupil. The slit is the most cat-specific
    # feature available - no other common pet has one - and it does more species work
    # per block than anything else on the model.
    box("EyeL", -0.17, FACE_Y - 0.02, HEAD_Z + 0.09, 0.18, 0.05, 0.11, m_w)
    box("EyeR",  0.17, FACE_Y - 0.02, HEAD_Z + 0.09, 0.18, 0.05, 0.11, m_w)
    box("PupL", -0.17, FACE_Y - 0.045, HEAD_Z + 0.09, 0.045, 0.05, 0.11, m_k)
    box("PupR",  0.17, FACE_Y - 0.045, HEAD_Z + 0.09, 0.045, 0.05, 0.11, m_k)
    box("EyeSideL", -CHEEK_X - 0.02, HEAD_Y - 0.15, HEAD_Z + 0.09, 0.05, 0.18, 0.11, m_w)
    box("EyeSideR",  CHEEK_X + 0.02, HEAD_Y - 0.15, HEAD_Z + 0.09, 0.05, 0.18, 0.11, m_w)
    box("PupSideL", -CHEEK_X - 0.045, HEAD_Y - 0.15, HEAD_Z + 0.09, 0.05, 0.045, 0.11, m_k)
    box("PupSideR",  CHEEK_X + 0.045, HEAD_Y - 0.15, HEAD_Z + 0.09, 0.05, 0.045, 0.11, m_k)

    # Tail stays BELOW the top of the head. It sits at x~0, dead centre between the
    # ears, so any taller and it pokes through the gap and reads as a third ear -
    # invisible in profile, obvious head-on.
    box("Tail1", 0, BODY_BACK + 0.07, BODY_Z + 0.19, 0.13, 0.13, 0.38, m_coat)
    box("Tail2", 0, BODY_BACK + 0.10, BODY_Z + 0.46, 0.12, 0.14, 0.22, m_coat)
    box("Tail3", 0, BODY_BACK - 0.04, BODY_Z + 0.55, 0.12, 0.28, 0.12, m_coat)

    # Pale legs with black boots. Back legs thicker than front, the way a cat's are.
    for name, x, y, w in (("LegFL", -0.18, -0.28, 0.21), ("LegFR", 0.18, -0.28, 0.21),
                          ("LegBL", -0.19,  0.32, 0.25), ("LegBR", 0.19,  0.32, 0.25)):
        box(name, x, y, LEG_H / 2, w, w, LEG_H, m_under)
        box("Toe" + name[3:], x, y - 0.02, 0.08, w + 0.01, w + 0.04, 0.16, m_acc)


# ----------------------------------------------------------------------------
# Spine now runs horizontally front-to-back, so rotating it arches the back rather
# than leaning a torso. Legs stay parented to root, not spine, so an arch keeps the
# feet planted - which is what a cat arching its back actually does.
BONES = {
    "root":     ((0, 0, 0),                        (0, 0, 0.15)),
    "spine":    ((0, BODY_FRONT + 0.10, BODY_Z),   (0, BODY_BACK, BODY_Z)),
    "head":     ((0, HEAD_Y + 0.20, HEAD_Z),       (0, FACE_Y, HEAD_Z)),
    "tailBase": ((0, BODY_BACK, BODY_Z),            (0, BODY_BACK + 0.07, BODY_Z + 0.42)),
    "tailMid":  ((0, BODY_BACK + 0.07, BODY_Z + 0.42), (0, BODY_BACK + 0.10, BODY_Z + 0.66)),
    "tailTip":  ((0, BODY_BACK + 0.10, BODY_Z + 0.66), (0, BODY_BACK - 0.16, BODY_Z + 0.70)),
    "legFL":    ((-0.18, -0.28, LEG_H), (-0.18, -0.28, 0)),
    "legFR":    (( 0.18, -0.28, LEG_H), ( 0.18, -0.28, 0)),
    "legBL":    ((-0.19,  0.32, LEG_H), (-0.19,  0.32, 0)),
    "legBR":    (( 0.19,  0.32, LEG_H), ( 0.19,  0.32, 0)),
}
BONE_PARENT = {
    "spine": "root", "head": "spine", "tailBase": "spine", "tailMid": "tailBase",
    "tailTip": "tailMid",
    "legFL": "root", "legFR": "root", "legBL": "root", "legBR": "root",
}
PART_BONE = {
    "spine": ["Body", "Chest", "Belly", "Haunch", "Bib"],
    "head": ["Head", "EarL", "EarR", "EarTipL", "EarTipR", "InEarL", "InEarR",
             "Muzzle", "Nose", "Mouth-1", "Mouth1", "MouthD-1", "MouthD1",
             "EyeL", "EyeR", "PupL", "PupR",
             "EyeSideL", "EyeSideR", "PupSideL", "PupSideR"],
    "tailBase": ["Tail1"],
    "tailMid": ["Tail2"],
    "tailTip": ["Tail3"],
    "legFL": ["LegFL", "ToeFL"], "legFR": ["LegFR", "ToeFR"],
    "legBL": ["LegBL", "ToeBL"], "legBR": ["LegBR", "ToeBR"],
}


def build_armature():
    arm_data = bpy.data.armatures.new("CatRig")
    arm = bpy.data.objects.new("Deskitty", arm_data)
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


def aim_camera(cam, loc, target):
    """Ortho views must stay axis-pure, so the caller offsets the camera to frame
    the subject instead of aiming off-axis (which would tilt the projection)."""
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# THE SPRITE CONTRACT. Every state, every angle, every future pose renders through
# these numbers - see SPRITE_CONTRACT.md. This is the one thing that is genuinely
# expensive to change once the app ships, because the app anchors sprites bottom-centre
# and any drift in scale or ground line makes her jump between states.
#
# The camera NEVER moves. Ported from lil-cleo's render_states.py: a fixed camera plus
# a character that rotates is the only way to guarantee identical scale and an
# identical ground row across every state. Moving the camera per view - which is what
# this file used to do - lets both drift silently.
SPRITE_W, SPRITE_H = 640, 512
SPRITE_ORTHO = 2.3          # horizontal world coverage (640 is the larger dimension)
SPRITE_CAM_Z = 0.83         # puts ground z=0 about 25px above the bottom edge
SPRITE_CAM_Y = -9.0

# Landscape, not lil-cleo's portrait 512x640: Brick is a humanoid minifig and is taller
# than he is wide in every pose, but a quadruped cat in profile is the opposite - 2.03
# wide against 1.56 tall. Portrait cannot hold the standing profile without shrinking
# her so far that the sitting states waste most of the frame.


def sprite_stage():
    """Fixed sprite camera + FLAT voxel lighting. Shared by every state build.

    Hard SUN lamps aimed straight down the three axes, shadows off, specular killed.
    Every face of every block then takes exactly ONE flat value decided by which way
    it points - top bright, front mid, side dark. That crisp three-tone step is the
    entire voxel-art look. The soft three-point studio rig this replaces smeared a
    gradient across each face and made the whole model read as generic 3D; no palette
    change could compensate for it.
    """
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = SPRITE_ORTHO
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, SPRITE_CAM_Y, SPRITE_CAM_Z)
    cam.rotation_euler = (math.radians(90), 0, 0)   # dead-on -Y, axis-pure ortho
    bpy.context.scene.camera = cam

    def sun(name, rot, energy, color="#FFFFFF"):
        ld = bpy.data.lights.new(name, type="SUN")
        ld.energy = energy
        ld.angle = 0.0            # zero angular size = perfectly hard
        ld.use_shadow = False     # self-shadowing would break the flatness
        ld.color = rgb(color)[:3]
        ob = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(ob)
        ob.rotation_euler = rot
        return ob

    sun("Top",   (0, 0, 0), 2.5)                              # down  -> +Z faces
    sun("Front", (math.radians(90), 0, 0), 1.15, "#FFF6E8")   # +Y    -> -Y faces
    sun("Side",  (0, math.radians(-90), 0), 0.70, "#E6EEFF")  # +X    -> -X faces

    # Specular off everywhere. A hard sun on a glossy face blows a highlight, which
    # turned the eyes into flat white holes the first time this was tried. Voxel art
    # wants pure albedo: no gloss, no sheen, just the face's flat value.
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if not b:
            continue
        b.inputs["Roughness"].default_value = 1.0
        for k in ("Specular IOR Level", "Specular"):
            if k in b.inputs:
                b.inputs[k].default_value = 0.0

    world = bpy.data.worlds.new("W"); bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.30, 0.31, 0.35, 1)   # lifts unlit faces off black
    bg.inputs[1].default_value = 0.55

    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x, sc.render.resolution_y = SPRITE_W, SPRITE_H
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"   # AgX would desaturate the accents
    return cam


def face(arm, side):
    """Turn the character, never the camera.

    Deskitty's front is -Y and camera-right is +X, so +90 degrees about Z puts her in
    profile facing screen-right. Only right-facing sprites are rendered - the app
    mirrors them for leftward travel, exactly as lil-cleo's ImageCharacterView does
    with scaleEffect(x: facing).
    """
    arm.rotation_euler[2] = math.radians(90 if side else 0)


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {path}")


def setup_viewport():
    """Make the GUI open on a coloured cat instead of a grey one.

    Saved .blend files carry their UI, so this sticks. Two independent things had to
    change: materials now set diffuse_color (catlib) so Solid shading has a colour to
    show at all, and the 3D viewports switch to Material Preview so you see the actual
    lit shaders. Harmless in background mode - screens exist there too.
    """
    for sc in bpy.data.screens:
        for area in sc.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                space.shading.type = "MATERIAL"
                space.shading.color_type = "MATERIAL"     # fallback if user hits Solid
                space.shading.studio_light = "forest.exr"
                space.shading.studiolight_background_alpha = 0.0
                space.overlay.show_floor = True
                space.overlay.show_axis_x = True
                space.overlay.show_axis_y = True


def face_collections(front_names, cheek_names):
    """Split the two eye-decal sets into toggleable collections.

    The renders hide whichever set is edge-on via hide_render, but hide_render is a
    render-only flag - in the GUI viewport BOTH sets are visible at once, so she shows
    up with four eyes: two on the face and two more stuck to her cheeks. Collections
    fix that: cheek decals start hidden in the viewport, and the monitor icon next to
    Face_Cheek / Face_Front in the outliner swaps which set you're looking at. Neither
    flag touches rendering, so the sprite output is unchanged.
    """
    scene_col = bpy.context.scene.collection
    for cname, names, hide in (("Face_Front", front_names, False),
                               ("Face_Cheek", cheek_names, True)):
        col = bpy.data.collections.new(cname)
        scene_col.children.link(col)
        for n in names:
            ob = PARTS.get(n)
            if not ob:
                continue
            if ob.name in scene_col.objects:
                scene_col.objects.unlink(ob)
            col.objects.link(ob)
        col.hide_viewport = hide


def show(names, visible):
    for n in names:
        PARTS[n].hide_render = not visible


FRONT_DECALS = ("EyeL", "EyeR", "PupL", "PupR", "InEarL", "InEarR")
CHEEK_DECALS = ("EyeSideL", "EyeSideR", "PupSideL", "PupSideR")

# ----------------------------------------------------------------------------
WALK_FRAMES = 8                     # matches lil-cleo's WALK_FRAMES
LEG_SWING   = math.radians(24)
TAIL_SWAY   = math.radians(9)
HEAD_DIP    = math.radians(3)


def rest_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)


def render_walk(arm, n=WALK_FRAMES):
    """Walk in place, sampled into `walk1..N.png`.

    Two-beat diagonal gait - front-left swings with back-right, front-right with
    back-left - which is what Minecraft's mobs do and what rigid single-segment legs
    can actually express. A real four-beat cat walk needs knees to fold; these legs
    are solid blocks pivoting at the hip, so the honest move is to lean into the
    blocky gait rather than fake an anatomy the model doesn't have.

    She does NOT travel across the frame. The app moves the window; the sprite only
    animates. Travel baked into the sprite would fight it and break the anchor.
    """
    pb = arm.pose.bones
    for i in range(n):
        ph = 2 * math.pi * i / n
        swing = LEG_SWING * math.sin(ph)
        pb["legFL"].rotation_euler[0] =  swing
        pb["legBR"].rotation_euler[0] =  swing
        pb["legFR"].rotation_euler[0] = -swing
        pb["legBL"].rotation_euler[0] = -swing
        # tail counter-sways a quarter-cycle behind the legs, tip lagging the base -
        # the lag is what stops it reading as one rigid stick
        pb["tailBase"].rotation_euler[0] = TAIL_SWAY * math.sin(ph + math.pi / 2)
        pb["tailMid"].rotation_euler[0]  = TAIL_SWAY * math.sin(ph + math.pi / 3)
        pb["tailTip"].rotation_euler[0]  = TAIL_SWAY * 1.4 * math.sin(ph + math.pi / 6)
        pb["head"].rotation_euler[0]     = HEAD_DIP * math.sin(2 * ph)
        render_to(os.path.join(SPRITES, f"walk{i + 1}.png"))
    rest_pose(arm)


# ----------------------------------------------------------------------------
def main():
    wipe()
    build_model()
    arm = build_armature()
    sprite_stage()
    setup_viewport()
    face_collections(FRONT_DECALS, CHEEK_DECALS)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print(f"SAVED {BLEND}")

    os.makedirs(SPRITES, exist_ok=True)

    # side_idle: the locomotion angle, and the app's fallback sprite for any state
    # that has no art yet. Cheek eyes only - the front decals are edge-on here.
    face(arm, side=True)
    show(CHEEK_DECALS, True); show(FRONT_DECALS, False)
    render_to(os.path.join(SPRITES, "side_idle.png"))

    # front_idle: standing, facing camera. Mostly head, chest and legs now that the
    # body runs away from the camera.
    face(arm, side=False)
    show(CHEEK_DECALS, False); show(FRONT_DECALS, True)
    render_to(os.path.join(SPRITES, "front_idle.png"))

    # walk1..8: locomotion, so profile only.
    face(arm, side=True)
    show(CHEEK_DECALS, True); show(FRONT_DECALS, False)
    render_walk(arm)


if __name__ == "__main__":
    main()
