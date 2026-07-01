# utils.py - Utility helpers and macOS permission diagnostics

import os
import sys
import ctypes

def is_macos():
    """Returns True if the current operating system is macOS."""
    return sys.platform == 'darwin'

def is_accessibility_enabled():
    """
    Checks if the application / parent process has macOS Accessibility permissions.
    Uses the system ApplicationServices framework.
    """
    if not is_macos():
        return True  # Bypass checks on non-macOS systems for local dev safety
        
    try:
        # Load the ApplicationServices framework dynamically
        app_services = ctypes.CDLL(
            '/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices'
        )
        # AXIsProcessTrusted returns a boolean (1 if trusted, 0 if not)
        return bool(app_services.AXIsProcessTrusted())
    except Exception as e:
        print(f"[-] Programmatic accessibility check failed: {e}", file=sys.stderr)
        return False

def print_permission_warning():
    """Prints a clear instructions banner on how to grant necessary permissions."""
    print("=" * 70, file=sys.stderr)
    print("[-] ACCESS DENIED: macOS Accessibility Permissions Required", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("To allow mouse control, this terminal/app must be granted Accessibility access:", file=sys.stderr)
    print("  1. Open System Settings -> Privacy & Security -> Accessibility.", file=sys.stderr)
    print("  2. Click the '+' button under the list.", file=sys.stderr)
    print("  3. Find and add your Terminal application (e.g., Terminal, iTerm2, or VSCode).", file=sys.stderr)
    print("  4. Toggle the switch to enable access.", file=sys.stderr)
    print("  5. Restart this script.", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
