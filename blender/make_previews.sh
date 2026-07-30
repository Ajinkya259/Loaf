#!/bin/bash
# Composite every transparent sprite render over flat mid-grey, into previews/.
#
# Sprites have to ship with alpha, but a white cat on alpha is invisible in every
# viewer that composites over white - which is all of them. Reviewing the raw PNGs
# means reviewing a blank rectangle. Run this after any build and look at previews/
# instead.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p previews

# Blender renders straight into the Swift package - there is no copy step.
SPRITES=../Sources/Loaf/Resources/sprites

for f in "$SPRITES"/*.png; do
    [ -f "$f" ] || continue
    magick "$f" -background '#33333B' -alpha remove -alpha off "previews/$(basename "$f")"
    echo "previews/$(basename "$f")"
done

# Contact sheet: all four angles side by side, so a recolour or proportion change can
# be judged across every view at once instead of one render at a time.
magick previews/side_idle.png previews/front_idle.png \
       previews/sit.png \
       -background '#33333B' -gravity south +append previews/contact_sheet.png
echo "previews/contact_sheet.png"

# AT DISPLAY SIZE. The app draws her at 160x128, a 4x downscale from the 640x512
# render, and detail that reads fine at full size can vanish completely there. A
# profile sit was judged good on the big previews and was an unrecognisable blob on
# screen - its tail failed to clear the back line, which only matters once the fine
# detail is gone and the silhouette is all that is left.
#
# JUDGE HER HERE, NOT ON THE FULL-SIZE PREVIEWS.
for f in "$SPRITES"/*.png; do
    [ -f "$f" ] || continue
    magick "$f" -background '#33333B' -alpha remove -alpha off \
           -resize 160x128 -scale 200% "previews/small_$(basename "$f")"
done
magick previews/small_side_idle.png previews/small_walk3.png \
       previews/small_sit_side.png previews/small_sit.png previews/small_front_idle.png \
       -background '#33333B' -gravity south +append previews/contact_small.png
echo "previews/contact_small.png   <- judge her here"
