#!/bin/bash
# build_dmg.sh - Script to package the macOS Webcam Air Trackpad into a .dmg installer with custom icon and instructions

set -e

echo "=== Preparing Build Environment ==="
# Ensure venv is active
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[-] Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Ensure PyInstaller is installed
echo "=== Installing PyInstaller ==="
pip install pyinstaller

# Generate the app icon if not already present
if [ ! -f "icon.icns" ]; then
    echo "[*] icon.icns not found. Running icon compiler..."
    python3 create_icon.py
fi

# Clean old builds
echo "=== Cleaning previous build artifacts ==="
rm -rf build dist *.spec

# Build .app bundle
echo "=== Compiling with PyInstaller ==="
# We add --icon="icon.icns" to assign a custom visual icon.
# We add --add-data "gui.html:." to bundle our settings layout template.
pyinstaller --windowed \
            --name="AirTrackpad" \
            --clean \
            --icon="icon.icns" \
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

# Create a clean Instructions text file inside the DMG directory
cat << 'EOF' > "$DMG_TEMP_DIR/Instructions.txt"
==================================================
        macOS Air Trackpad Installation Guide
==================================================

Thank you for downloading Air Trackpad! Follow these simple steps to install and start using the app.

1. INSTALLATION
   Drag the "AirTrackpad" application icon into the "Applications" folder.

2. SYSTEM PERMISSIONS (Accessibility)
   Since this application simulates mouse controls, clicks, and desktop shortcuts, macOS requires Accessibility permissions:
   
   - Open System Settings ( menu -> System Settings).
   - Go to "Privacy & Security" -> "Accessibility".
   - Turn the switch next to "AirTrackpad" to ON.
   - (If not visible, click the "+" button and select "AirTrackpad" from your Applications folder).
   
3. CAMERA PERMISSION
   On launching the app and clicking "Start Tracking", macOS will request Camera access. Select "OK" to allow tracking.

4. QUICK GESTURE GUIDE
   - Move Cursor: Extend index finger.
   - Left Click / Drag: Pinch index and thumb.
   - Right Click: Pinch middle and thumb.
   - Scroll: Extend index and middle side-by-side; move hand vertically.
   - Switch Desktop Space: Swipe 3 fingers rapidly left/right.
   - Mission Control: Swipe 3 fingers rapidly up.
   - Pause Tracking: Show open palm (5 fingers extended).

==================================================
Project Details & Support:
https://github.com/nikhil21111/Mouse-controller
==================================================
EOF

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
