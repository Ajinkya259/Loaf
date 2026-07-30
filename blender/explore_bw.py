"""Explore the white-and-black space: where the black sits, and the eye accent.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/explore_bw.py

A monochrome cat has almost no colour decisions, which makes the few it has carry all
the weight. Two axes:

  MARKINGS - the black is structure, not decoration. On a white cat against a light
  desktop the dark blocks are the only thing holding the silhouette together, so where
  they sit changes readability, not just looks.

  ACCENT - the eyes and nose are the entire hue budget. On a ginger cat eye colour is a
  detail; here it IS the colour identity.

Builds on build_cat's geometry and only reassigns materials / adds marking blocks, so
nothing structural changes between variants.
"""
import bpy, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cat as BC
from catlib import PARTS, material, box

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bw")

FUR   = "#F2EEE6"
SHADE = "#D6CEC0"
INK   = "#2B2B33"
SOFT  = "#3E3E48"

# Eye accents. The nose shifts with each so the two warm/cool notes agree instead of
# fighting - a pink nose under amber eyes reads as two unrelated decisions.
ACCENTS = {
    "ice blue":   ("#4E93C4", "#E0899C"),
    "amber":      ("#D9A24B", "#C98A80"),
    "jade":       ("#6FA88A", "#D08E9A"),
    "pale gold":  ("#C8B36A", "#CE8F92"),
}


def recolor(names, mat):
    for n in names:
        ob = PARTS.get(n)
        if ob:
            ob.data.materials.clear()
            ob.data.materials.append(mat)


TOES = ["ToeFL", "ToeFR", "ToeBL", "ToeBR"]
TAIL = ["Tail1", "Tail2", "Tail3"]
TIPS = ["EarTipL", "EarTipR"]


def markings(kind, m_fur, m_ink, m_soft):
    """Each variant is a different answer to 'how much black, and where'."""
    if kind == "points":
        return                      # as built: tail, ear tips, toes
    if kind == "socks_off":
        recolor(TOES, m_fur)        # minimal - tail and ear tips only
    elif kind == "boots":
        # black up the whole lower leg, not just the foot
        for n, y in (("LegFL", -0.28), ("LegFR", -0.28), ("LegBL", 0.32), ("LegBR", 0.32)):
            x = -0.18 if n.endswith("L") and "F" in n else (0.18 if "F" in n else
                (-0.19 if n.endswith("L") else 0.19))
            box(n + "Boot", x, y, BC.LEG_H * 0.34, 0.26, 0.26, BC.LEG_H * 0.68, m_soft)
    elif kind == "patch":
        # asymmetric eye patch + one black ear. Asymmetry is what turns a generic
        # white cat into a specific one you'd recognise.
        recolor(["EarL", "EarTipL"], m_ink)
        box("Patch", -BC.CHEEK_X - 0.015, BC.HEAD_Y - 0.13, BC.HEAD_Z + 0.09,
            0.04, 0.30, 0.26, m_ink)
    elif kind == "cap":
        # black cap over the skull, white face below - reads as a mask
        recolor(["EarL", "EarR"], m_ink)
        box("Cap", 0, BC.HEAD_Y + 0.02, BC.HEAD_Z + BC.HEAD_S / 2 - 0.07,
            BC.HEAD_S + 0.01, BC.HEAD_S - 0.02, 0.16, m_ink)
    elif kind == "saddle":
        recolor(["Haunch"], m_soft)
        box("Saddle", 0, 0.05, BC.BODY_Z + BC.BODY_H / 2 - 0.05,
            BC.BODY_W + 0.01, BC.BODY_LEN * 0.72, 0.12, m_ink)


def build(kind, accent):
    eye, nose = ACCENTS[accent]
    BC.FUR_BASE, BC.FUR_SHADE, BC.INK, BC.INK_SOFT = FUR, SHADE, INK, SOFT
    BC.EYE_BLUE, BC.NOSE_PINK = eye, nose
    BC.EAR_PINK = nose
    BC.wipe()
    BC.build_model()
    markings(kind, material("Fur", FUR, rough=0.55), material("Ink", INK, rough=0.5),
             material("Toe", SOFT, rough=0.5))
    arm = BC.build_armature()
    BC.sprite_stage()
    return arm


def shot(arm, path, side):
    BC.face(arm, side=side)
    BC.show(BC.CHEEK_DECALS, side); BC.show(BC.FRONT_DECALS, not side)
    BC.render_to(path)


MARKINGS = ("points", "socks_off", "boots", "patch", "cap", "saddle")


def main():
    """Full matrix. The two axes interact - a warm eye reads differently against
    heavy black than against a nearly-unmarked white cat - so rendering them
    separately and imagining the combination doesn't work."""
    os.makedirs(OUT, exist_ok=True)
    for kind in MARKINGS:
        for accent in ACCENTS:
            a = accent.replace(" ", "_")
            arm = build(kind, accent)
            shot(arm, os.path.join(OUT, f"{kind}__{a}__side.png"), True)
            shot(arm, os.path.join(OUT, f"{kind}__{a}__front.png"), False)


if __name__ == "__main__":
    main()
