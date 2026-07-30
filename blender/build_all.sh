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
"$B" -b -P blender/build_cat.py     2>&1 | grep -E "RENDERED|Error" || true
"$B" -b -P blender/build_cat_sit.py 2>&1 | grep -E "RENDERED|Error" || true
"$B" -b -P blender/build_cat_sit_side.py 2>&1 | grep -E "RENDERED|Error" || true
"$B" -b -P blender/build_cat_loaf.py 2>&1 | grep -E "RENDERED|Error" || true
blender/make_previews.sh
echo "--- sprites ---"; ls Sources/Loaf/Resources/sprites/
