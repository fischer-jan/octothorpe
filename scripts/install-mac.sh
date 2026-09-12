#!/usr/bin/env bash
# Build the SwiftUI Octothorpe.app (the octothorpe GUI) and copy it for Spotlight / Launchpad,
# plus a CLI shim. The app shells out to the project venv.
# Re-run after moving the repo.
#
#   bash scripts/install-mac.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLI_BIN="$ROOT/.venv/bin/octothorpe"

if [[ ! -x "$CLI_BIN" ]]; then
  echo "✗ Missing $CLI_BIN" >&2
  echo "  Create the venv first:" >&2
  echo "    python3.12 -m venv .venv && source .venv/bin/activate && pip install -e \".[dev,ocr]\"" >&2
  exit 1
fi

SUPPORT="$HOME/Library/Application Support/Octothorpe"
mkdir -p "$SUPPORT"
printf '%s\n' "$ROOT" > "$SUPPORT/project_root.txt"

echo "▸ Building SwiftUI app"
cd "$ROOT/MacApp"
xcodebuild \
  -project Octothorpe.xcodeproj \
  -scheme Octothorpe \
  -configuration Release \
  -derivedDataPath ./DerivedData \
  build

APP_SRC="$ROOT/MacApp/DerivedData/Build/Products/Release/Octothorpe.app"
if [[ ! -d "$APP_SRC" ]]; then
  echo "✗ Build did not produce $APP_SRC" >&2
  exit 1
fi

if [[ -w /Applications ]]; then
  APPS="/Applications"
else
  APPS="$HOME/Applications"
  mkdir -p "$APPS"
fi
APP="$APPS/Octothorpe.app"
rm -rf "$APPS/Octothorpe.app"   # the app was called Octothorpe before 2026-09-12

echo "▸ Installing bundle → $APP"
rm -rf "$APP"
ditto "$APP_SRC" "$APP"

chmod -R go-w "$APP"

if command -v codesign >/dev/null 2>&1; then
  codesign --force --sign - --identifier de.janfischer.octothorpe "$APP" || true
fi

touch "$APP"
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
[[ -x "$LSREGISTER" ]] && "$LSREGISTER" -f "$APP" || true
command -v mdimport >/dev/null 2>&1 && mdimport "$APP" || true

BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sfn "$CLI_BIN" "$BIN_DIR/octothorpe"
cat > "$BIN_DIR/octothorpe-gui" <<LAUNCH
#!/bin/bash
exec open -a "$APP"
LAUNCH
chmod 755 "$BIN_DIR/octothorpe-gui"

echo "✓ Octothorpe installed → $APP"
echo "  Launch: open -a Octothorpe   or Spotlight: Octothorpe"
echo "  CLI:    $BIN_DIR/octothorpe  (ensure ~/.local/bin is on PATH)"
echo "  Re-run this script if you move the project folder."
