"""Multi-colour coat PATTERNS - the part most real cats actually have.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/explore_pattern.py

Every palette pass before this gave her one body colour plus dark points. Real cats are
mostly not like that: orange-and-white bicolours, vans, tuxedos, calicos and tabbies are
all *patterns* - the same coat split across the body in a particular arrangement.

So colour is now two independent choices:

  PATTERN  - which parts take which of three slots
  COLOURWAY - what those three slots actually are

Which means combinations multiply instead of adding. Six patterns x N colourways, and
adding a colourway is one line.

Slots, by the job they do rather than by hue:
  A  primary   - the dominant coat
  B  secondary - the pale counter-colour (belly, chest, muzzle - where a real cat is
                 nearly always lighter, because that is where the sun does not reach)
  C  accent    - socks, ear tips, and whatever needs to anchor the silhouette
"""
import bpy, os, sys, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cat as BC
import explore_style as ES
from catlib import PARTS, material, box

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pattern")

# ---- part groups -----------------------------------------------------------
G = {
    "core":  ["Body", "Haunch", "Chest"],
    "under": ["Belly", "Bib"],
    "head":  ["Head", "EarL", "EarR"],
    "face":  ["Muzzle"],
    "legs":  ["LegFL", "LegFR", "LegBL", "LegBR"],
    "feet":  ["ToeFL", "ToeFR", "ToeBL", "ToeBR"],
    "tail":  ["Tail1", "Tail2", "Tail3"],
    "tips":  ["EarTipL", "EarTipR"],
}

# Which slot each group takes. "-" means leave whatever build_cat gave it.
PATTERNS = {
    # exactly the ask: orange back/head/tail, white underside and legs, black socks
    "bicolour": dict(core="A", head="A", tail="A", under="B", face="B", legs="B",
                     feet="C", tips="C"),
    # mostly white, colour only where a van cat carries it - head and tail
    "van":      dict(core="B", head="A", tail="A", under="B", face="B", legs="B",
                     feet="C", tips="A"),
    # coloured body, white bib and white socks - a tuxedo in reverse
    "tuxedo":   dict(core="A", head="A", tail="A", under="B", face="B", legs="A",
                     feet="B", tips="A"),
    # white cat wearing a coloured cap and a dark tail: calico-ish three-way split
    "calico":   dict(core="B", head="A", tail="C", under="B", face="B", legs="B",
                     feet="C", tips="C"),
    # all one coat, dark socks and ear tips only - the current build, for comparison
    "solid":    dict(core="A", head="A", tail="A", under="B", face="B", legs="A",
                     feet="C", tips="C"),
    # coat plus darker banding across the back
    "tabby":    dict(core="A", head="A", tail="A", under="B", face="B", legs="A",
                     feet="C", tips="C"),
}

#                    A primary   B secondary  C accent    eye        nose
COLOURWAYS = {
    # Every entry below is validated against three rules, measured in CIE L*:
    #   L*(B) - L*(A) >= 25   coat vs underside. This is the one that matters most -
    #                         pixel-art guidance is unanimous that VALUE contrast beats
    #                         hue, and 9 of the previous 13 colourways failed it.
    #   L*(C) <= 22           the accent has to be genuinely dark to anchor the feet.
    #   |L*(eye) - L*(A)| >= 15  or the eye vanishes into the face. Old ginger scored
    #                         1.7 here: a green eye and orange fur at the same value.
    # Plus hue-shifting: slot B shifts COOLER than A rather than merely lighter, which
    # is what stops the underside reading as "the same colour with the lights up".

    # --- survived the audit ---------------------------------------------------
    "marmalade": ("#D2733A", "#EFE7D8", "#241E1E", "#E8C86B", "#C96D78"),
    "russet":    ("#B5512F", "#F0E4D4", "#2A1E1C", "#F0D97E", "#C97A80"),
    "chocolate": ("#8B6248", "#E8DCC8", "#2A211C", "#8FC46B", "#C08878"),
    "smoke":     ("#8E97A3", "#F0F0F2", "#22262C", "#C9E85C", "#D98A93"),
    "ginger":    ("#E8944A", "#F6F1E7", "#2B2B33", "#3D6E4A", "#E08A9C"),

    # --- dark bodies: the entire family that was missing ----------------------
    # Nothing before this had a dark coat, so every option sat in the same narrow
    # value band. These have the widest A/B separation in the set by a distance.
    "midnight":  ("#2E3138", "#C6CDD6", "#14161A", "#E8C44B", "#D9909A"),
    "cocoa":     ("#4A3A32", "#E4D6C0", "#1E1814", "#8FC46B", "#C99080"),
    "forest":    ("#34453B", "#DDE6DC", "#171F1A", "#E8A24B", "#D08E96"),

    # --- hue-shifted: cool underside against a warm coat ----------------------
    "rustsky":   ("#B5512F", "#C9D6DF", "#1E1A1C", "#F0D97E", "#C97A80"),
    "honey":     ("#B57A22", "#CBD6DE", "#23262B", "#7FC4E8", "#D9909A"),

    # --- bold, and still inside the rules -------------------------------------
    "berry":     ("#5A6BA8", "#DCE0EE", "#1C1E2E", "#E8B54A", "#D98CA4"),
    "rose":      ("#C4506A", "#F7E6E4", "#2A1A20", "#A8D96B", "#D97A8E"),
}


def recolor(names, mat):
    for n in names:
        ob = PARTS.get(n)
        if ob:
            ob.data.materials.clear()
            ob.data.materials.append(mat)


def paint(pattern, cw):
    A, B, C, _, _ = cw
    mats = {"A": material("A", A, rough=1.0), "B": material("B", B, rough=1.0),
            "C": material("C", C, rough=1.0)}
    for group, slot in PATTERNS[pattern].items():
        if slot in mats:
            recolor(G[group], mats[slot])

    if pattern == "tabby":
        # Three bands across the back plus a ringed tail. Stripes are what separate a
        # tabby from a plain coat, and on a blocky body they have to be whole blocks -
        # anything thinner vanishes at sprite size.
        dark = material("Aband", C, rough=1.0)
        for i, y in enumerate((-0.22, 0.02, 0.26)):
            box(f"Band{i}", 0, y, BC.BODY_Z + BC.BODY_H / 2 - 0.03,
                BC.BODY_W + 0.012, 0.10, 0.10, dark)
        recolor(["Tail2"], dark)


# The eye is LOCKED, not per-colourway. Letting it drift with the coat is what makes
# twelve colourways read as twelve different cats instead of one cat in twelve coats -
# and it was the bug behind ginger showing green eyes while the face study showed gold.
# THE FACE IS MONOCHROME. White sclera, white muzzle patch, black nose, black mouth,
# black pupil - the same two values regardless of what the coat is doing. Two reasons
# it works better than a tinted face:
#   1. It borrows nothing from the coat, so one face fits all twelve colourways and she
#      stays one character rather than becoming twelve different cats.
#   2. White-and-black is the highest contrast available anywhere on the model, and it
#      lands on the face - which is exactly where you want the eye to go first.
FACE_WHITE = "#FBF8F4"
FACE_BLACK = "#1A1A1E"
EYE_HUE    = FACE_WHITE      # sclera, not an iris colour
INNER_EAR  = FACE_WHITE


def eye_slit():
    """White sclera with a black vertical pupil. Two colours, no glint - at sprite size
    a catchlight is fighting for about four pixels, and against a white sclera it has
    nothing left to contrast with anyway."""
    dark = material("Pup", FACE_BLACK, rough=1.0)
    y  = BC.FACE_Y - 0.045
    sy = BC.HEAD_Z + 0.09
    for sx in (-1, 1):
        box(f"Pu{sx}", sx * 0.17, y, sy, 0.045, 0.05, 0.11, dark)


def mono_face():
    """Muzzle patch white, nose and mouth black, inner ear white."""
    w = material("FaceW", FACE_WHITE, rough=1.0)
    k = material("FaceK", FACE_BLACK, rough=1.0)
    for names, m in ((("Muzzle",), w), (("InEarL", "InEarR"), w), (("Nose",), k)):
        for n in names:
            ob = PARTS.get(n)
            if ob:
                ob.data.materials.clear(); ob.data.materials.append(m)
    # the mouth the body renders never had - a "w" under the nose
    for sx in (-1, 1):
        box(f"Mo{sx}", sx * 0.055, BC.MUZZLE_Y - 0.055, BC.HEAD_Z - 0.19,
            0.07, 0.05, 0.04, k)
        box(f"MoD{sx}", sx * 0.09, BC.MUZZLE_Y - 0.055, BC.HEAD_Z - 0.215,
            0.05, 0.05, 0.04, k)


def build(pattern, cwname):
    cw = COLOURWAYS[cwname]
    A, B, C, eye, nose = cw
    BC.FUR_BASE, BC.FUR_SHADE, BC.INK, BC.INK_SOFT = A, B, C, C
    BC.EYE_BLUE, BC.NOSE_PINK, BC.EAR_PINK = EYE_HUE, FACE_BLACK, INNER_EAR
    BC.wipe()
    BC.build_model()
    eye_slit()
    paint(pattern, cw)
    mono_face()          # after paint(), so the coat never overwrites the face
    arm = BC.build_armature()
    ES.flat_stage()
    return arm


def shot(arm, path, side):
    BC.face(arm, side=side)
    BC.show(BC.CHEEK_DECALS, side); BC.show(BC.FRONT_DECALS, not side)
    BC.render_to(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    for pat in PATTERNS:
        for cw in COLOURWAYS:
            arm = build(pat, cw)
            shot(arm, os.path.join(OUT, f"{pat}__{cw}__side.png"), True)
            shot(arm, os.path.join(OUT, f"{pat}__{cw}__front.png"), False)


if __name__ == "__main__":
    main()
