"""Render the cat in every candidate palette, for picking one.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/palette_sheet.py

Reuses build_cat's geometry wholesale and only swaps the seven colour constants before
each rebuild, so what changes between these images is colour and nothing else. Runs all
palettes in one Blender process rather than one launch each.

Note what the existing geometry already is: a body with darker ears, tail and toes. That
is a COLOURPOINT pattern - so siamese isn't a restyle here, it's the pattern the model
was already built for. Tuxedo is the interesting one because it inverts the roles: the
points stay dark and the *accents* (muzzle, bib, socks) go white.
"""
import bpy, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cat as BC

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palettes")

#            fur        shade      ink        ink_soft   eye        nose       ear
PALETTES = {
    "white":   ("#F2EEE6", "#D6CEC0", "#2B2B33", "#3E3E48", "#4E93C4", "#E0899C", "#E8A9B4"),
    "ginger":  ("#E39A55", "#C87E3C", "#8E4A1E", "#A05A28", "#6E8F4A", "#D97590", "#E8A2A8"),
    "siamese": ("#EDE3D2", "#D8C9B2", "#4A382E", "#5C4638", "#5FA8D8", "#C9948E", "#D9B3A5"),
    "tuxedo":  ("#33333D", "#F0EDE6", "#22222A", "#F0EDE6", "#8FC46B", "#D98FA0", "#C98A96"),
    "grey":    ("#A9AEB8", "#8D94A0", "#3C4048", "#4C525C", "#D9A24B", "#B98C94", "#C9A0A8"),
}


def apply(pal):
    (BC.FUR_BASE, BC.FUR_SHADE, BC.INK,
     BC.INK_SOFT, BC.EYE_BLUE, BC.NOSE_PINK, BC.EAR_PINK) = pal


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, pal in PALETTES.items():
        apply(pal)
        BC.wipe()
        BC.build_model()
        arm = BC.build_armature()
        BC.sprite_stage()

        BC.face(arm, side=True)
        BC.show(BC.CHEEK_DECALS, True); BC.show(BC.FRONT_DECALS, False)
        BC.render_to(os.path.join(OUT, f"{name}_side.png"))

        BC.face(arm, side=False)
        BC.show(BC.CHEEK_DECALS, False); BC.show(BC.FRONT_DECALS, True)
        BC.render_to(os.path.join(OUT, f"{name}_front.png"))


if __name__ == "__main__":
    main()
