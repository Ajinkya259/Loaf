"""Face study: markings, mouth, eye shape, eye colour.

    /Applications/Blender.app/Contents/MacOS/Blender -b -P blender/explore_face.py

The face carries almost all of her character and has had the least attention. It also
has an outright omission: she currently has NO MOUTH. The nose sits on a pale muzzle
patch and nothing else happens below it.

Four independent axes, rendered as strips rather than as a matrix, because each one is
judged on its own and a 5x4x4x8 grid would be 640 images nobody reads:

  MARKING  - what the pale/dark shapes on the face do
  MOUTH    - the missing feature
  EYE SHAPE- the same block at different proportions reads as a different animal
  EYE HUE  - the only real colour on her

Everything renders front-on and gets cropped to the head, since that is how a face is
actually judged.
"""
import bpy, os, sys, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_cat as BC
import explore_style as ES
from catlib import PARTS, material, box

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face")

# Russet: the best-scoring colourway from the contrast audit, so the face is judged
# against a coat that already works rather than against a broken one.
A, B, C = "#B5512F", "#F0E4D4", "#2A1E1C"
NOSE    = "#C97A80"
EYE_DEF = "#F0D97E"


def drop(*names):
    for n in names:
        ob = PARTS.pop(n, None)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)


def eye_detail(kind, hue):
    """Internal structure inside the eye block.

    A flat block of colour is what makes an eye read as painted on. Real pixel-art eyes
    carry an iris, a pupil and a catchlight, and the catchlight - one near-white pixel
    offset from centre - is the single element that makes an eye look wet and alive.

    The vertical SLIT is the cat-specific one. No other common pet has it, so it does
    more species work per block than anything else on the face.
    """
    if kind == "flat":
        return
    y = BC.FACE_Y - 0.045          # sits proud of the eye block, which is at -0.02
    dark  = material("Pup", "#1C1A20", rough=1.0)
    white = material("Glint", "#FBFCFE", rough=1.0)
    sy = BC.HEAD_Z + 0.09
    for sx in (-1, 1):
        cx = sx * 0.17
        if kind == "catchlight":
            box(f"Gl{sx}", cx - 0.045, y, sy + 0.025, 0.05, 0.05, 0.04, white)
        elif kind == "round":
            box(f"Pu{sx}", cx, y, sy, 0.07, 0.05, 0.07, dark)
        elif kind == "slit":
            box(f"Pu{sx}", cx, y, sy, 0.035, 0.05, 0.11, dark)
        elif kind == "slit_glint":
            box(f"Pu{sx}", cx, y, sy, 0.035, 0.05, 0.11, dark)
            box(f"Gl{sx}", cx - 0.055, y - 0.02, sy + 0.025, 0.045, 0.05, 0.035, white)
        elif kind == "round_glint":
            box(f"Pu{sx}", cx, y, sy, 0.07, 0.05, 0.07, dark)
            box(f"Gl{sx}", cx - 0.055, y - 0.02, sy + 0.025, 0.045, 0.05, 0.035, white)
        elif kind == "white_centre":
            box(f"Pu{sx}", cx, y, sy, 0.07, 0.05, 0.07, white)

    # --- white-eye family: the eye BLOCK goes white and the colour moves inward -----
    # This is the cartoon/sprite convention rather than the feline one - a white
    # sclera reads as a drawn character, a coloured sclera reads as an animal.
    if kind.startswith("weye"):
        for sx in (-1, 1):
            ob = PARTS.get("EyeL" if sx < 0 else "EyeR")
            if ob:
                ob.data.materials.clear(); ob.data.materials.append(white)
            cx = sx * 0.17
            if kind == "weye_round":
                box(f"Pu{sx}", cx, y, sy, 0.07, 0.05, 0.075, dark)
            elif kind == "weye_slit":
                box(f"Pu{sx}", cx, y, sy, 0.04, 0.05, 0.105, dark)
            elif kind == "weye_iris":
                iris = material("Iris", hue, rough=1.0)
                box(f"Ir{sx}", cx, y, sy, 0.085, 0.05, 0.105, iris)
                box(f"Pu{sx}", cx, y - 0.02, sy, 0.04, 0.05, 0.105, dark)

    # --- forehead dot: a marking BETWEEN the eyes, not inside them ------------------
    if kind == "dot_between":
        box("Dot", 0, BC.FACE_Y - 0.03, BC.HEAD_Z + 0.10, 0.075, 0.05, 0.075, white)
    elif kind == "dot_above":
        box("Dot", 0, BC.FACE_Y - 0.03, BC.HEAD_Z + 0.215, 0.075, 0.05, 0.075, white)


def eyes(shape, hue):
    """Rebuild both eye sets at a given proportion. Same block, different aspect -
    and the aspect alone swings her between alert, sleepy and startled."""
    drop("EyeL", "EyeR", "EyeSideL", "EyeSideR")
    m = material("EyeM", hue, rough=1.0)
    w, h, z = {
        "wide":   (0.18, 0.11,  0.09),   # current: broad horizontal slabs
        "round":  (0.13, 0.14,  0.09),   # taller than wide - kittenish, more startled
        "sleepy": (0.18, 0.05,  0.07),   # slits, permanently half-closed
        "big":    (0.21, 0.16,  0.08),   # oversized - the cutest and the least feline
    }[shape]
    for sx, sfx in ((-1, "L"), (1, "R")):
        box("Eye" + sfx, sx * 0.17, BC.FACE_Y - 0.02, BC.HEAD_Z + z, w, 0.05, h, m)
        box("EyeSide" + sfx, sx * (BC.CHEEK_X + 0.02), BC.HEAD_Y - 0.15,
            BC.HEAD_Z + z, 0.05, w, h, m)


def mouth(kind):
    if kind == "none":
        return
    dark = material("MouthM", C, rough=1.0)
    y = BC.MUZZLE_Y - 0.055
    if kind == "line":                      # single flat line under the nose
        box("Mouth", 0, y, BC.HEAD_Z - 0.20, 0.09, 0.05, 0.04, dark)
    elif kind == "w":                       # the classic cat "w" - two angled halves
        for sx in (-1, 1):
            box(f"Mouth{sx}", sx * 0.055, y, BC.HEAD_Z - 0.19, 0.07, 0.05, 0.04, dark)
            box(f"MouthD{sx}", sx * 0.09, y, BC.HEAD_Z - 0.215, 0.05, 0.05, 0.04, dark)
    elif kind == "smile":                   # wider, one step down at the corners
        box("Mouth", 0, y, BC.HEAD_Z - 0.185, 0.07, 0.05, 0.04, dark)
        for sx in (-1, 1):
            box(f"MouthC{sx}", sx * 0.075, y, BC.HEAD_Z - 0.215, 0.06, 0.05, 0.04, dark)


def marking(kind):
    pale = material("PaleM", B, rough=1.0)
    dark = material("DarkM", C, rough=1.0)
    fy = BC.FACE_Y - 0.018
    if kind == "plain":
        return
    if kind == "blaze":
        # pale stripe up the bridge of the nose - extremely common on real cats and
        # the cheapest way to make a face look like a specific individual
        box("Blaze", 0, fy, BC.HEAD_Z + 0.02, 0.10, 0.05, 0.34, pale)
    elif kind == "mask":
        # dark around the eyes: reads as a colourpoint or a little bandit
        for sx in (-1, 1):
            box(f"Mask{sx}", sx * 0.17, fy, BC.HEAD_Z + 0.09, 0.26, 0.05, 0.19, dark)
    elif kind == "cheeks":
        for sx in (-1, 1):
            box(f"Cheek{sx}", sx * 0.19, fy, BC.HEAD_Z - 0.13, 0.20, 0.05, 0.20, pale)
    elif kind == "brows":
        # two small pale dots above the eyes. Cats have them; on a blocky face they
        # read as eyebrows and give her an opinion.
        for sx in (-1, 1):
            box(f"Brow{sx}", sx * 0.17, fy, BC.HEAD_Z + 0.235, 0.08, 0.05, 0.06, pale)
    elif kind == "wide_muzzle":
        drop("Muzzle")
        box("Muzzle", 0, BC.MUZZLE_Y, BC.HEAD_Z - 0.16, 0.40, 0.10, 0.26, pale)


EARS = {
    "tips":    dict(ear="A", tip="C", inner=True),    # current
    "full":    dict(ear="C", tip="C", inner=True),    # whole ear dark
    "pale":    dict(ear="B", tip="C", inner=True),    # pale ear, dark tip
    "clean":   dict(ear="A", tip="A", inner=False),   # no dark, no pink
}


def ears(kind):
    spec = EARS[kind]
    mats = {"A": material("A", A, rough=1.0), "B": material("B", B, rough=1.0),
            "C": material("C", C, rough=1.0)}
    for names, slot in ((("EarL", "EarR"), spec["ear"]),
                        (("EarTipL", "EarTipR"), spec["tip"])):
        for n in names:
            ob = PARTS.get(n)
            if ob:
                ob.data.materials.clear(); ob.data.materials.append(mats[slot])
    if not spec["inner"]:
        drop("InEarL", "InEarR")


# Face colourways: muzzle patch / nose / inner ear / mouth. The nose is checked
# against the muzzle it sits on, not against the coat - a nose is only ever seen on
# top of the patch, so that is the contrast that decides whether it reads.
FACE_COLOURS = {
    # Highest contrast available on the face: a near-white patch with a true-black
    # nose and mouth. Pulls the eye straight to the centre of the head, which is
    # where you want it, and works on every coat because it borrows nothing from it.
    "white + black":   ("#FBF8F4", "#1E1A1C", "#E8DCD8", "#1E1A1C"),
    "cream + pink":    ("#F0E4D4", "#D9808E", "#E0A0AC", "#2A1E1C"),
    "cream + charcoal":("#F0E4D4", "#33292C", "#C08890", "#2A1E1C"),
    "cream + brick":   ("#F0E4D4", "#B5563F", "#D0918A", "#2A1E1C"),
    "warm peach":      ("#F2C9A8", "#C96B78", "#E0A098", "#33221E"),
    "bright white":    ("#FBF6F0", "#E08898", "#EFB4BC", "#2A1E1C"),
    "mauve":           ("#E4DCE0", "#9C8290", "#C4A8B4", "#2A2028"),
    "gold muzzle":     ("#E8CFA0", "#C97A80", "#DDAA9E", "#332420"),
    "no patch":        ("#B5512F", "#6B2E22", "#C97A6E", "#2A1E1C"),
}


def face_colour(key):
    mz, nz, ie, mo = FACE_COLOURS[key]
    # InEar deliberately NOT included: it is an ear, and changing it here made every
    # muzzle selection look like it was editing the ears instead of the face.
    for names, hexv in ((("Muzzle",), mz), (("Nose",), nz)):
        m = material("FC" + hexv, hexv, rough=1.0)
        for n in names:
            ob = PARTS.get(n)
            if ob:
                ob.data.materials.clear(); ob.data.materials.append(m)
    for n in list(PARTS):
        if n.startswith("Mouth"):
            m = material("MO" + mo, mo, rough=1.0)
            PARTS[n].data.materials.clear(); PARTS[n].data.materials.append(m)


def build(mark="plain", mth="none", eshape="wide", ehue=EYE_DEF, ear="tips", fc=None,
          coat=None, edetail="flat"):
    a, b, c = coat if coat else (A, B, C)
    globals().update(A=a, B=b, C=c)
    BC.FUR_BASE, BC.FUR_SHADE, BC.INK, BC.INK_SOFT = a, b, c, c
    BC.EYE_BLUE, BC.NOSE_PINK, BC.EAR_PINK = ehue, NOSE, NOSE
    BC.wipe()
    BC.build_model()
    eyes(eshape, ehue)
    eye_detail(edetail, ehue)
    marking(mark)
    mouth(mth)
    ears(ear)
    if fc:
        face_colour(fc)
    arm = BC.build_armature()
    ES.flat_stage()
    BC.face(arm, side=False)
    BC.show(BC.CHEEK_DECALS, False)
    for n in ("EyeL", "EyeR"):
        if n in PARTS:
            PARTS[n].hide_render = False
    return arm


def main():
    os.makedirs(OUT, exist_ok=True)
    for k in ("plain", "blaze", "mask", "cheeks", "brows", "wide_muzzle"):
        build(mark=k, mth="w")
        BC.render_to(os.path.join(OUT, f"mark_{k}.png"))
    for k in ("none", "line", "w", "smile"):
        build(mth=k)
        BC.render_to(os.path.join(OUT, f"mouth_{k}.png"))
    for k in ("wide", "round", "sleepy", "big"):
        build(eshape=k, mth="w")
        BC.render_to(os.path.join(OUT, f"eye_{k}.png"))
    for name, hue in (("gold", "#F0D97E"), ("jade", "#7FB069"), ("ice", "#7FC4E8"),
                      ("lime", "#C9E85C"), ("copper", "#E8944A"), ("violet", "#B49BE0"),
                      ("rose", "#E8909C"), ("silver", "#DCE4EC")):
        build(ehue=hue, mth="w")
        BC.render_to(os.path.join(OUT, f"hue_{name}.png"))
    for k in EARS:
        build(ear=k, mth="w")
        BC.render_to(os.path.join(OUT, f"ear_{k}.png"))
    for k in FACE_COLOURS:
        build(mth="w", fc=k)
        BC.render_to(os.path.join(OUT, f"fc_{k.replace(' ', '_').replace('+','and')}.png"))


COATS = {
    "ginger":   ("#E8944A", "#F6F1E7", "#2B2B33", "#3D6E4A"),
    "marmalade":("#D2733A", "#EFE7D8", "#241E1E", "#E8C86B"),
    "russet":   ("#B5512F", "#F0E4D4", "#2A1E1C", "#F0D97E"),
    "chocolate":("#8B6248", "#E8DCC8", "#2A211C", "#8FC46B"),
    "smoke":    ("#8E97A3", "#F0F0F2", "#22262C", "#C9E85C"),
    "midnight": ("#2E3138", "#C6CDD6", "#14161A", "#E8C44B"),
    "cocoa":    ("#4A3A32", "#E4D6C0", "#1E1814", "#8FC46B"),
    "forest":   ("#34453B", "#DDE6DC", "#171F1A", "#E8A24B"),
    "rustsky":  ("#B5512F", "#C9D6DF", "#1E1A1C", "#F0D97E"),
    "honey":    ("#B57A22", "#CBD6DE", "#23262B", "#7FC4E8"),
    "berry":    ("#5A6BA8", "#DCE0EE", "#1C1E2E", "#E8B54A"),
    "rose":     ("#C4506A", "#F7E6E4", "#2A1A20", "#A8D96B"),
}
FACE_SET = ["white + black", "cream + charcoal", "cream + brick", "warm peach",
            "gold muzzle", "mauve"]


EYE_SET = {
    # Eye colour is deliberately NOT tied to the coat: locking it is what keeps her one
    # character across twelve colourways instead of twelve different cats.
    "gold flat":   ("#F0D97E", "flat"),
    "gold slit":   ("#F0D97E", "slit_glint"),
    "white iris":  ("#F0D97E", "weye_iris"),
    "ice slit":    ("#7FC4E8", "slit_glint"),
}


FACE_SET6 = ["white + black", "cream + charcoal", "cream + brick", "warm peach",
             "gold muzzle"]
COATS6 = ["ginger", "russet", "chocolate", "smoke", "midnight", "berry"]


def eye_matrix():
    """eyes x muzzle x coat. Both selectors have to compose, or picking one silently
    resets the other - which is exactly the bug this replaces."""
    os.makedirs(OUT, exist_ok=True)
    for cname in COATS6:
        a, b, c, _ = COATS[cname]
        for ename, (hue, det) in EYE_SET.items():
            for f in FACE_SET6:
                build(mth="w", fc=f, ehue=hue, edetail=det, coat=(a, b, c))
                tag = f.replace(" ", "_").replace("+", "and")
                BC.render_to(os.path.join(
                    OUT, f"fb_{cname}__{ename.replace(' ','_')}__{tag}.png"))


def matrix():
    """Face colourway x coat, front view. Face is judged front-on, so the side view
    is left to the coat chooser rather than doubling this."""
    os.makedirs(OUT, exist_ok=True)
    for cname, (a, b, c, eye) in COATS.items():
        for f in FACE_SET:
            build(mth="w", fc=f, ehue=eye, coat=(a, b, c))
            tag = f.replace(" ", "_").replace("+", "and")
            BC.render_to(os.path.join(OUT, f"fx_{cname}__{tag}.png"))


EYE_DETAIL = ("slit_glint", "weye_round", "weye_slit", "weye_iris",
              "dot_between", "dot_above")


def detail_strip():
    os.makedirs(OUT, exist_ok=True)
    for k in EYE_DETAIL:
        build(mth="w", fc="white + black", edetail=k)
        BC.render_to(os.path.join(OUT, f"ed_{k}.png"))


if __name__ == "__main__":
    eye_matrix()
