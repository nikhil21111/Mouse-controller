# main.py - Main application loop and web GUI manager

import cv2
import sys
import time
import os
import threading
import webview

import config
import utils
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from coordinate_mapper import CoordinateMapper
from mouse_controller import OSController

class WebUI_API:
    def __init__(self):
        self.tracking_active = False
        self.tracker_thread = None
        self.window = None

    def start_tracking(self):
        if not self.tracking_active:
            self.tracking_active = True
            self.tracker_thread = threading.Thread(target=self._run_tracking_loop)
            self.tracker_thread.daemon = True
            self.tracker_thread.start()
            print("[+] Tracking engine started in background.")

    def stop_tracking(self):
        if self.tracking_active:
            self.tracking_active = False
            if self.tracker_thread:
                self.tracker_thread.join(timeout=1.5)
            print("[+] Tracking engine stopped.")

    def update_settings(self, options):
        # Update sensitivity parameters in config module
        config.MOUSE_SENSITIVITY = float(options.get('speed', 2.5))
        config.EMA_ALPHA = float(options.get('smoothing', 0.25))
        config.FRAME_SKIP_COUNT = int(options.get('skip_count', 2))
        
        config.PINCH_ENABLED = bool(options.get('pinch_enabled', True))
        config.SCROLL_ENABLED = bool(options.get('scroll_enabled', True))
        config.SWIPE_ENABLED = bool(options.get('swipe_enabled', True))
        
        print(f"[+] Config updated: Speed={config.MOUSE_SENSITIVITY}, Smooth={config.EMA_ALPHA}, FrameSkip={config.FRAME_SKIP_COUNT}, Pinch={config.PINCH_ENABLED}, Scroll={config.SCROLL_ENABLED}, Swipe={config.SWIPE_ENABLED}")

    def _run_tracking_loop(self):
        # Accessibility check inside tracking loop (before requesting webcam/input simulation)
        if not utils.is_accessibility_enabled():
            utils.print_permission_warning()
            if utils.is_macos():
                self.tracking_active = False
                if self.window:
                    self.window.evaluate_js("alert('Accessibility permission not granted! Please enable Accessibility for your Terminal app.')")
                return

        os_controller = OSController()
        
        try:
            screen_w, screen_h = os_controller.get_screen_size()
            print(f"[+] Tracking engine screen resolution: {screen_w}x{screen_h}")
        except Exception as e:
            screen_w, screen_h = 1920, 1080
            
        mapper = CoordinateMapper(screen_w, screen_h)
        tracker = HandTracker()
        recognizer = GestureRecognizer()
        
        cap = cv2.VideoCapture(config.CAMERA_ID)
        if not cap.isOpened():
            print("[-] ERROR: Cannot open webcam. Check Camera/AVFoundation permissions.")
            self.tracking_active = False
            if self.window:
                self.window.evaluate_js("alert('Cannot open webcam. Check AVFoundation permissions.')")
            return
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        
        frame_idx = 0
        consecutive_missing_frames = 0
        
        while self.tracking_active:
            success, frame = cap.read()
            if not success:
                time.sleep(0.01)
                continue
                
            frame_idx += 1
            if frame_idx % config.FRAME_SKIP_COUNT == 0:
                frame = cv2.flip(frame, 1)
                frame = tracker.find_hands(frame, draw=False)  # Run MediaPipe hand tracking (no window render)
                landmarks = tracker.get_landmarks(0)
                
                gesture = "Loss of Tracking"
                if landmarks:
                    consecutive_missing_frames = 0
                    gesture, wrist = recognizer.process_frame(landmarks)
                    
                    # Process Move
                    if gesture == "Move":
                        screen_x, screen_y = mapper.map_coordinates(landmarks[8].x, landmarks[8].y)
                        os_controller.move_to(screen_x, screen_y)
                        os_controller.reset_scroll()
                    
                    # Process Pinch / Left Drag (if enabled)
                    elif gesture == "Pinch_Active":
                        if config.PINCH_ENABLED:
                            screen_x, screen_y = mapper.map_coordinates(landmarks[8].x, landmarks[8].y)
                            os_controller.drag_to(screen_x, screen_y)
                        os_controller.reset_scroll()
                        
                    # Process Right Click (if enabled)
                    elif gesture == "Right_Click":
                        if config.PINCH_ENABLED:
                            os_controller.right_click()
                        os_controller.reset_scroll()
                        recognizer.active_gesture = "Move"
                        
                    # Process Scroll (if enabled)
                    elif gesture == "Scroll":
                        if config.SCROLL_ENABLED:
                            os_controller.scroll(landmarks[8].y, config.SCROLL_SPEED_MULTIPLIER)
                            
                    # Process Space switching (if enabled)
                    elif gesture == "Swipe_Left":
                        if config.SWIPE_ENABLED:
                            print("[*] Action: Swipe Left -> Space Switch")
                            os_controller.trigger_shortcut(config.SHORTCUT_SPACE_LEFT)
                        recognizer.active_gesture = "Idle"
                    elif gesture == "Swipe_Right":
                        if config.SWIPE_ENABLED:
                            print("[*] Action: Swipe Right -> Space Switch")
                            os_controller.trigger_shortcut(config.SHORTCUT_SPACE_RIGHT)
                        recognizer.active_gesture = "Idle"
                    elif gesture == "Swipe_Up":
                        if config.SWIPE_ENABLED:
                            print("[*] Action: Swipe Up -> Mission Control")
                            os_controller.trigger_shortcut(config.SHORTCUT_MISSION_CONTROL)
                        recognizer.active_gesture = "Idle"
                        
                    # Reset triggers
                    elif gesture == "Pause" or gesture == "Idle":
                        os_controller.release_left()
                        os_controller.reset_scroll()
                        mapper.reset()
                else:
                    consecutive_missing_frames += 1
                    if consecutive_missing_frames >= config.LOSS_OF_TRACKING_FRAMES:
                        recognizer.reset()
                        mapper.reset()
                        os_controller.reset_scroll()
                        os_controller.release_left()
                
                # Update Web UI active pose status in real-time
                if self.window:
                    self.window.evaluate_js(f"updatePose('{gesture}')")
            
            # Short sleep to prevent CPU hogging
            time.sleep(0.005)
            
        cap.release()
        cv2.destroyAllWindows()
        print("[+] Tracking loop exited cleanly.")

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

if __name__ == '__main__':
    main()
