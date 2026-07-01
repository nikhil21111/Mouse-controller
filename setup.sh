#!/bin/bash
# setup.sh - Environment and dependency setup for macOS Webcam Air Trackpad

set -e

echo "=== System Architecture Detection ==="
ARCH=$(uname -m)
echo "Detected CPU Architecture: $ARCH"

# Determine Homebrew path
if [ "$ARCH" = "arm64" ]; then
    BREW_PREFIX="/opt/homebrew"
else
    BREW_PREFIX="/usr/local"
fi
echo "Using Homebrew Prefix: $BREW_PREFIX"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed. Please install Python 3.10 or 3.11."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python Version: $PY_VERSION"

# Warn if Python version is not 3.10 or 3.11
if [ "$PY_VERSION" != "3.10" ] && [ "$PY_VERSION" != "3.11" ]; then
    echo "WARNING: Pinned environment is Python 3.10 or 3.11. Current is $PY_VERSION."
    echo "MediaPipe installation may fail or require compilation on older/newer versions."
fi

# Set up virtual environment
echo "=== Creating Virtual Environment ==="
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "=== Upgrading Package Installer ==="
pip install --upgrade pip

# Install dependencies
echo "=== Installing Dependencies ==="
# MediaPipe, OpenCV, pynput, and PyObjC (for Accessibility API checks)
pip install opencv-python mediapipe pynput pyobjc-core pyobjc-framework-ApplicationServices

echo "=== Setup Completed Successfully ==="
echo "To run the application, execute: source venv/bin/activate && python main.py"
