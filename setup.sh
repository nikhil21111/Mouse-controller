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

# Determine python executable (prefer Python 3.11 or 3.10 for stable MediaPipe solutions)
if [ -x "/Users/nikhil/.local/bin/python3.11" ]; then
    PYTHON_EXE="/Users/nikhil/.local/bin/python3.11"
elif command -v python3.11 &> /dev/null; then
    PYTHON_EXE="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_EXE="python3.10"
else
    PYTHON_EXE="python3"
fi

echo "Selected Python Interpreter: $PYTHON_EXE"
PY_VERSION=$($PYTHON_EXE -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python Version: $PY_VERSION"

# Set up virtual environment
echo "=== Creating Virtual Environment ==="
rm -rf venv # Clear old venv to ensure clean packages
$PYTHON_EXE -m venv venv
source venv/bin/activate

# Upgrade pip
echo "=== Upgrading Package Installer ==="
pip install --upgrade pip

# Install dependencies
echo "=== Installing Dependencies ==="
if [ "$PY_VERSION" = "3.14" ]; then
    # Fallback if we must run on 3.14, but solutions will not be found in newer MediaPipe.
    # So we force python 3.11/3.10.
    echo "WARNING: Running on Python 3.14. Solutions API may be missing."
    pip install opencv-python mediapipe pynput pyobjc-core pyobjc-framework-ApplicationServices
else
    # Install mediapipe 0.10.14 or similar which has solutions built-in
    pip install opencv-python mediapipe==0.10.14 pynput pyobjc-core pyobjc-framework-ApplicationServices
fi

echo "=== Setup Completed Successfully ==="
echo "To run the application, execute: ./run.sh"
