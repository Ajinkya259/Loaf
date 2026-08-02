#!/bin/bash
# Package Loaf into a runnable Loaf.app, and a drag-install Loaf.dmg.
#
#   tools/package.sh          # build app + dmg into dist/
#   tools/package.sh app      # just the .app
#   make app  /  make dist
#
# Signing: if a "Developer ID Application" identity is in the keychain, the app is
# signed with it. Otherwise it falls back to ad-hoc signing - runs locally, but on
# another Mac the first launch is right-click > Open (or:
# xattr -dr com.apple.quarantine Loaf.app). No notarization step: that needs an
# Apple Developer Program membership and a stored notarytool credential profile,
# neither of which exists here yet. Override the identity with LOAF_SIGN_ID.
#
# Adapted from ref/lil-cleo/tools/package.sh, which already solved this for a
# shipped desktop pet - same structure, Loaf's own icon and bundle ID.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="Loaf"
VERSION="${LOAF_VERSION:-0.3.0}"
BUNDLE_ID="com.ajinkya.loaf"
DIST="dist"
APP="$DIST/$APP_NAME.app"
BIN=".build/release/$APP_NAME"
RES_BUNDLE=".build/release/${APP_NAME}_${APP_NAME}.bundle"
# Front-facing, not profile: CLAUDE.md's own rule is "profile is for locomotion,
# front is for personality," and an app icon is exactly a personality moment.
ICON_SPRITE="Sources/Loaf/Resources/sprites/normal/front_idle.png"
WHAT="${1:-all}"

echo "▸ Release build"
swift build -c release

echo "▸ Assembling $APP"
rm -rf "$DIST"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/$APP_NAME"
cp -R "$RES_BUNDLE" "$APP/Contents/Resources/"

echo "▸ App icon (from $ICON_SPRITE)"
ICONSET="$(mktemp -d)/AppIcon.iconset"
mkdir -p "$ICONSET"
# A soft cream-to-peach glow behind her - the same coat/underside family from
# CLAUDE.md §4, not a new colourway invented for the icon. NEAREST resampling on
# the sprite itself keeps her voxel edges hard instead of blurring them.
python3 - "$ICON_SPRITE" "$ICONSET/master.png" <<'PY'
import sys
from PIL import Image, ImageDraw
sprite_path, out = sys.argv[1], sys.argv[2]
S = 1024
bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(bg)
top, bot = (0xFB, 0xF6, 0xEE), (0xF3, 0xC5, 0x91)
for y in range(S):
    t = y / S
    d.line([(0, y), (S, y)], fill=(int(top[0] + (bot[0] - top[0]) * t),
                                   int(top[1] + (bot[1] - top[1]) * t),
                                   int(top[2] + (bot[2] - top[2]) * t), 255))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S, S], radius=int(S * 0.225), fill=255)
bg.putalpha(mask)
sprite = Image.open(sprite_path).convert("RGBA")
scale = (S * 0.62) / max(sprite.size)
sprite = sprite.resize((int(sprite.width * scale), int(sprite.height * scale)), Image.NEAREST)
bg.alpha_composite(sprite, ((S - sprite.width) // 2, int(S * 0.22)))
bg.save(out)
PY
for s in 16 32 64 128 256 512 1024; do
    sips -z $s $s "$ICONSET/master.png" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
done
# @2x variants iconutil expects
cp "$ICONSET/icon_32x32.png"     "$ICONSET/icon_16x16@2x.png"
cp "$ICONSET/icon_64x64.png"     "$ICONSET/icon_32x32@2x.png"
cp "$ICONSET/icon_256x256.png"   "$ICONSET/icon_128x128@2x.png"
cp "$ICONSET/icon_512x512.png"   "$ICONSET/icon_256x256@2x.png"
cp "$ICONSET/icon_1024x1024.png" "$ICONSET/icon_512x512@2x.png"
rm -f "$ICONSET/icon_64x64.png" "$ICONSET/icon_1024x1024.png" "$ICONSET/master.png"
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"

echo "▸ Info.plist"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>$APP_NAME</string>
    <key>CFBundleDisplayName</key><string>$APP_NAME</string>
    <key>CFBundleExecutable</key><string>$APP_NAME</string>
    <key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
    <key>CFBundleShortVersionString</key><string>$VERSION</string>
    <key>CFBundleVersion</key><string>$VERSION</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleIconFile</key><string>AppIcon</string>
    <key>LSMinimumSystemVersion</key><string>14.0</string>
    <!-- Accessory app, no dock icon - main.swift also sets this at runtime via
         setActivationPolicy(.accessory), which is what matters for `swift run`,
         but a packaged .app should declare it here too so there's no dock-icon
         flash before the code gets a chance to run. -->
    <key>LSUIElement</key><true/>
    <key>NSHighResolutionCapable</key><true/>
    <!-- Keep this in sync with the root Info.plist, which is the one embedded
         into the swift run/swift build dev binary (see Package.swift's
         linkerSettings) - the packaged .app gets its own separate copy here
         rather than reusing that file directly. -->
    <key>NSRemindersFullAccessUsageDescription</key>
    <string>Loaf reads how many reminders are still open so her body can reflect how much work is queued.</string>
</dict>
</plist>
PLIST

SIGN_ID="${LOAF_SIGN_ID:-$(security find-identity -v -p codesigning 2>/dev/null \
    | awk -F'"' '/Developer ID Application/ {print $2; exit}')}"
if [ -n "$SIGN_ID" ]; then
    echo "▸ Code sign ($SIGN_ID)"
    codesign --force --options runtime --timestamp --sign "$SIGN_ID" "$APP"
else
    echo "▸ Ad-hoc code sign (no Developer ID Application identity in keychain)"
    codesign --force --deep --sign - "$APP"
fi
echo "✓ Built $APP"

if [ "$WHAT" = "app" ]; then exit 0; fi

echo "▸ Building DMG"
STAGE="$DIST/dmg"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DIST/$APP_NAME.dmg" >/dev/null
rm -rf "$STAGE"
echo "✓ Built $DIST/$APP_NAME.dmg"

if [ -n "$SIGN_ID" ]; then
    codesign --force --timestamp --sign "$SIGN_ID" "$DIST/$APP_NAME.dmg"
fi
