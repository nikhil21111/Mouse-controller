#!/bin/bash
# build_dmg.sh - Script to package the macOS Webcam Air Trackpad into a .dmg installer

set -e

echo "=== Preparing Build Environment ==="
# Ensure venv is active
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[-] Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Install PyInstaller
echo "=== Installing PyInstaller ==="
pip install pyinstaller

# Clean old builds
echo "=== Cleaning previous build artifacts ==="
rm -rf build dist *.spec

# Build .app bundle
echo "=== Compiling with PyInstaller ==="
# We use --windowed (or --noconsole) to run as a macOS windowed GUI app.
# We collect all data files belonging to mediapipe since it relies on task graphs and binaries.
pyinstaller --windowed \
            --name="AirTrackpad" \
            --clean \
            --add-data "gui.html:." \
            --collect-all mediapipe \
            main.py

echo "=== Creating DMG Installer ==="
# Locate the generated .app bundle
APP_PATH="dist/AirTrackpad.app"

if [ ! -d "$APP_PATH" ]; then
    echo "[-] ERROR: AirTrackpad.app was not created by PyInstaller."
    exit 1
fi

# Create a temporary folder for dmg source
DMG_TEMP_DIR="dist/dmg_temp"
rm -rf "$DMG_TEMP_DIR"
mkdir -p "$DMG_TEMP_DIR"

# Copy the app to the temp directory
cp -R "$APP_PATH" "$DMG_TEMP_DIR/"

# Create a symlink to Applications directory inside the DMG for drag-and-drop installer experience
ln -s /Applications "$DMG_TEMP_DIR/Applications"

# Output DMG path
DMG_PATH="dist/AirTrackpad.dmg"
rm -f "$DMG_PATH"

# Build the DMG using macOS native hdiutil
echo "[+] Creating DMG file via hdiutil..."
hdiutil create -volname "AirTrackpad Installer" \
               -srcfolder "$DMG_TEMP_DIR" \
               -ov \
               -format UDZO \
               "$DMG_PATH"

# Clean up temp folder
rm -rf "$DMG_TEMP_DIR"

echo "=== Build Complete! ==="
echo "[+] Your installer is ready at: $DMG_PATH"
