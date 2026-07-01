#!/bin/bash
# run.sh - Run wrapper for macOS Webcam Air Trackpad

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[-] Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Run the python app
python3 main.py
