# main.py - Main application loop and web GUI manager

import sys
import os
import subprocess
import threading
import time
import webview

import config
import utils

class WebUI_API:
    def __init__(self):
        self.tracking_active = False
        self.process = None
        self.reader_thread = None
        self.window = None

    def start_tracking(self):
        if not self.tracking_active:
            self.tracking_active = True
            
            # Resolve the correct launch command based on build mode
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, '--engine']
            else:
                cmd = [sys.executable, 'main.py', '--engine']
                
            print(f"[+] Launching tracking subprocess: {cmd}")
            try:
                # Start tracking loop in a separate isolated subprocess
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1
                )
                
                # Start background thread to read gesture updates from stdout
                self.reader_thread = threading.Thread(target=self._read_subprocess_stdout)
                self.reader_thread.daemon = True
                self.reader_thread.start()
                print("[+] Subprocess launched and output reader started.")
            except Exception as e:
                print(f"[-] Failed to launch tracking engine: {e}")
                self.tracking_active = False

    def stop_tracking(self):
        if self.tracking_active:
            self.tracking_active = False
            if self.process:
                print("[*] Terminating tracking subprocess...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=1.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.process = None
            print("[+] Subprocess terminated.")

    def update_settings(self, options):
        # Update settings parameters in config module
        config.MOUSE_SENSITIVITY = float(options.get('speed', 2.5))
        config.EMA_ALPHA = float(options.get('smoothing', 0.25))
        config.FRAME_SKIP_COUNT = int(options.get('skip_count', 2))
        
        config.PINCH_ENABLED = bool(options.get('pinch_enabled', True))
        config.SCROLL_ENABLED = bool(options.get('scroll_enabled', True))
        config.SWIPE_ENABLED = bool(options.get('swipe_enabled', True))
        
        print(f"[+] UI updated config settings: Speed={config.MOUSE_SENSITIVITY}, Smooth={config.EMA_ALPHA}")
        
        # If tracking process is active, restart it so it picks up the updated configuration values!
        if self.tracking_active:
            print("[*] Restarting tracking process to apply updated options...")
            self.stop_tracking()
            # Brief delay to allow release of camera
            time.sleep(0.3)
            self.start_tracking()

    def _read_subprocess_stdout(self):
        while self.tracking_active and self.process:
            line = self.process.stdout.readline()
            if not line:
                break
            line_str = line.decode('utf-8').strip()
            if line_str.startswith('POSE:'):
                gesture = line_str.split(':', 1)[1]
                if self.window:
                    self.window.evaluate_js(f"updatePose('{gesture}')")
            else:
                # Log any startup prints or warnings from the tracking subprocess
                print(f"[Engine] {line_str}")

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    print("=== macOS Webcam Air Trackpad Startup ===")
    
    # Check macOS Accessibility status first
    if not utils.is_accessibility_enabled():
        utils.print_permission_warning()
        
    api = WebUI_API()
    
    gui_path = get_resource_path('gui.html')
    print(f"[+] Loading UI template from: {gui_path}")
    
    # Create pywebview window loading our local HTML dashboard
    window = webview.create_window(
        title='Air Trackpad Configuration & Calibration',
        url=gui_path,
        js_api=api,
        width=800,
        height=540,
        resizable=False,
        background_color='#0b0c10'
    )
    
    api.window = window
    
    # Run the pywebview GUI on the main thread
    webview.start()
    
    # Ensure subprocess is terminated if GUI window is closed
    api.stop_tracking()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--engine':
        # Execute tracking subprocess loop directly
        import tracking_engine
        tracking_engine.run_tracking()
    else:
        # Run Web GUI application
        main()
