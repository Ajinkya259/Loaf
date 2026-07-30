#!/bin/bash
# Build EVERY sprite from source, then regenerate previews.
#
# Exists because the standing and sitting builds are separate scripts and drifted
# apart twice: once the standing cat kept rabbit ears after only the sit was fixed,
# and once the sit was deleted entirely by a clean that only re-ran the stander.
# Run this, never one script on its own.
set -euo pipefail
cd "$(dirname "$0")/.."
B=/Applications/Blender.app/Contents/MacOS/Blender

# EVERY POSE AT EVERY WEIGHT. Fatness applies to all of them - if she slimmed down
# whenever she sat, the signal would only work in some poses and be worthless.
for W in lean normal chonk; do
    echo "--- $W ---"
    for SCRIPT in build_cat build_cat_sit build_cat_sit_side build_cat_sleep; do
        LOAF_WEIGHT=$W "$B" -b -P "blender/$SCRIPT.py" 2>&1 | grep -E "Error" || true
    done
done
blender/make_previews.sh
echo "--- sprites ---"; ls Sources/Loaf/Resources/sprites/*/ | head -40
