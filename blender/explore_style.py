"""Change how she's LIT, then re-explore colour on top of that.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/explore_style.py

Two problems were tangled together in the last pass:

  1. LIGHTING. Every render so far used soft area lights - a three-point studio rig.
     On flat axis-aligned voxel faces that produces mushy gradients smeared across
     each face, so the result reads as generic 3D rather than as designed voxel art.
     Fixed here with hard SUN lamps aimed straight down the three axes and shadows
     off: every face of every block then takes exactly ONE flat value, decided by
     which way it points. Top faces bright, front faces mid, side faces dark. That
     crisp three-tone step is the entire voxel-art look, and no palette change can
     substitute for it.

  2. PALETTE. The previous options were all naturalistic cat colours - white, ginger,
     grey, tuxedo, siamese - which is the obvious move and reads as obvious. These
     are designed palettes instead: she's a desktop object, not a photograph of an
     animal, so the colour can come from product design rather than from biology.
"""
import bpy, os, sys, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cat as BC
from catlib import rgb

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style")

#           fur        shade      ink        ink_soft   eye        nose       ear
PALETTES = {
    # cool grey body, near-black points, a sharp citrus eye. The eye is the whole
    # personality - unexpected, and high-contrast enough to survive at 40px.
    "slate":     ("#A3B2BD", "#8695A1", "#232A31", "#333C45", "#C9E85C", "#D98A93", "#C99BA2"),
    # muted lavender-grey with plum points. Reads cold and a bit nocturnal.
    "dusk":      ("#BCB0C4", "#9E92A8", "#37303F", "#4A4054", "#E8B54A", "#D18FA0", "#CE9AAC"),
    # pale sage, deep forest points, warm coral eye. Softest of the set.
    "moss":      ("#C9CFBA", "#ACB39B", "#2F3A2E", "#414D3F", "#E8846B", "#CC8A80", "#C99A90"),
    # bone and oxidised rust. The only warm-body option, and the most tactile.
    "bone":      ("#E6DCC7", "#C9BCA1", "#6B4535", "#825844", "#4A8FB5", "#C98A80", "#D0A091"),
    # near-monochrome with a cool blue shadow instead of a grey one - the trick that
    # stops white reading as "unpainted".
    "porcelain": ("#ECEAE4", "#C2CBD4", "#2A3038", "#3B434D", "#E8734E", "#DE8C93", "#DCA0A6"),

    # --- orange bodies -------------------------------------------------------
    # Orange is the one body colour that never loses against a light desktop, which
    # is the failure mode white has. All four keep near-black points for the same
    # structural reason, and all four take a COOL eye: warm-on-warm disappears, so
    # the accent has to come from the other side of the wheel to register at all.
    "marmalade": ("#E8944A", "#C97A34", "#3A2A22", "#4E382C", "#7FB069", "#D96F7A", "#E89A9E"),
    "apricot":   ("#F0B183", "#D29264", "#33303A", "#46424E", "#4E93C4", "#D9808E", "#E8A5AC"),
    "ember":     ("#D2733A", "#B25C2A", "#241E1E", "#362C2A", "#E8C86B", "#C96D78", "#D98F96"),
    "clay":      ("#C98A62", "#AC7050", "#3B2E38", "#4E3D49", "#5FA898", "#C97A80", "#D1949A"),
}


def flat_stage():
    """Hard axis-aligned suns, no shadows: one flat value per face direction."""
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = BC.SPRITE_ORTHO
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, BC.SPRITE_CAM_Y, BC.SPRITE_CAM_Z)
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam

    def sun(name, rot, energy, color="#FFFFFF"):
        ld = bpy.data.lights.new(name, type="SUN")
        ld.energy = energy
        ld.angle = 0.0                      # zero angular size = perfectly hard
        ld.use_shadow = False               # self-shadowing would break the flatness
        ld.color = rgb(color)[:3]
        ob = bpy.data.objects.new(name, ld)
        bpy.context.scene.collection.objects.link(ob)
        ob.rotation_euler = rot
        return ob

    sun("Top",   (0, 0, 0), 2.5)                                   # straight down  -> +Z faces
    sun("Front", (math.radians(90), 0, 0), 1.15, "#FFF6E8")        # toward +Y      -> -Y faces
    sun("Side",  (0, math.radians(-90), 0), 0.70, "#E6EEFF")       # toward +X      -> -X faces

    # Kill specular everywhere. A hard sun on a glossy face produces a blown highlight,
    # which is what turned the eyes into flat white holes on the first flat pass - the
    # eye material is the shiniest thing on her (roughness 0.25). Voxel art wants pure
    # albedo anyway: no gloss, no sheen, just the face's flat value.
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
    bg.inputs[0].default_value = (0.30, 0.31, 0.35, 1)   # lifts the unlit faces off black
    bg.inputs[1].default_value = 0.55

    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x, sc.render.resolution_y = BC.SPRITE_W, BC.SPRITE_H
    sc.view_settings.view_transform = "Standard"   # AgX would desaturate the accents
    return cam


def build(pal, flat=True):
    (BC.FUR_BASE, BC.FUR_SHADE, BC.INK,
     BC.INK_SOFT, BC.EYE_BLUE, BC.NOSE_PINK, BC.EAR_PINK) = pal
    BC.wipe()
    BC.build_model()
    arm = BC.build_armature()
    flat_stage() if flat else BC.sprite_stage()  # flat_stage also de-glosses materials
    return arm


def shot(arm, path, side):
    BC.face(arm, side=side)
    BC.show(BC.CHEEK_DECALS, side); BC.show(BC.FRONT_DECALS, not side)
    BC.render_to(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    # A/B the lighting on the existing white palette, so the change is isolated.
    white = ("#F2EEE6", "#D6CEC0", "#2B2B33", "#3E3E48", "#4E93C4", "#E0899C", "#E8A9B4")
    for tag, flat in (("soft", False), ("flat", True)):
        arm = build(white, flat=flat)
        shot(arm, os.path.join(OUT, f"ab_{tag}_side.png"), True)
        shot(arm, os.path.join(OUT, f"ab_{tag}_front.png"), False)

    for name, pal in PALETTES.items():
        arm = build(pal, flat=True)
        shot(arm, os.path.join(OUT, f"{name}_side.png"), True)
        shot(arm, os.path.join(OUT, f"{name}_front.png"), False)


if __name__ == "__main__":
    main()
