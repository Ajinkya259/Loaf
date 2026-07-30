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

for f in sprites/*.png; do
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
