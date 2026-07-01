# tracking_engine.py - Background gesture tracking process

import cv2
import sys
import time
import os

import config
import utils
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from coordinate_mapper import CoordinateMapper
from mouse_controller import OSController

def run_tracking():
    # Programmatic Accessibility Check
    if not utils.is_accessibility_enabled():
        print("[-] ERROR: Accessibility permission not granted.", flush=True)
        sys.exit(1)

    os_controller = OSController()
    
    try:
        screen_w, screen_h = os_controller.get_screen_size()
        print(f"[+] Screen Size Detected: {screen_w}x{screen_h}", flush=True)
    except Exception as e:
        screen_w, screen_h = 1920, 1080
        
    mapper = CoordinateMapper(screen_w, screen_h)
    tracker = HandTracker()
    recognizer = GestureRecognizer()
    
    cap = cv2.VideoCapture(config.CAMERA_ID)
    if not cap.isOpened():
        print("[-] ERROR: Cannot open webcam.", flush=True)
        sys.exit(1)
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    
    print("[+] Camera feed started.", flush=True)
    
    frame_idx = 0
    consecutive_missing_frames = 0
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                time.sleep(0.01)
                continue
                
            frame_idx += 1
            if frame_idx % config.FRAME_SKIP_COUNT == 0:
                frame = cv2.flip(frame, 1)
                frame = tracker.find_hands(frame, draw=False)
                landmarks = tracker.get_landmarks(0)
                
                gesture = "Loss of Tracking"
                if landmarks:
                    consecutive_missing_frames = 0
                    gesture, wrist = recognizer.process_frame(landmarks)
                    
                    # Print active pose to stdout so the UI parent process can read it
                    print(f"POSE:{gesture}", flush=True)
                    
                    if gesture == "Move":
                        screen_x, screen_y = mapper.map_coordinates(landmarks[8].x, landmarks[8].y)
                        os_controller.move_to(screen_x, screen_y)
                        os_controller.reset_scroll()
                        
                    elif gesture == "Pinch_Active":
                        if config.PINCH_ENABLED:
                            screen_x, screen_y = mapper.map_coordinates(landmarks[8].x, landmarks[8].y)
                            os_controller.drag_to(screen_x, screen_y)
                        os_controller.reset_scroll()
                        
                    elif gesture == "Right_Click":
                        if config.PINCH_ENABLED:
                            os_controller.right_click()
                        os_controller.reset_scroll()
                        recognizer.active_gesture = "Move"
                        
                    elif gesture == "Scroll":
                        if config.SCROLL_ENABLED:
                            os_controller.scroll(landmarks[8].y, config.SCROLL_SPEED_MULTIPLIER)
                            
                    elif gesture == "Swipe_Left":
                        if config.SWIPE_ENABLED:
                            os_controller.trigger_shortcut(config.SHORTCUT_SPACE_LEFT)
                        recognizer.active_gesture = "Idle"
                        
                    elif gesture == "Swipe_Right":
                        if config.SWIPE_ENABLED:
                            os_controller.trigger_shortcut(config.SHORTCUT_SPACE_RIGHT)
                        recognizer.active_gesture = "Idle"
                        
                    elif gesture == "Swipe_Up":
                        if config.SWIPE_ENABLED:
                            os_controller.trigger_shortcut(config.SHORTCUT_MISSION_CONTROL)
                        recognizer.active_gesture = "Idle"
                        
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
                        print("POSE:Loss of Tracking", flush=True)
                        
            time.sleep(0.005)
            
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[+] Tracking loop exited cleanly.", flush=True)

if __name__ == '__main__':
    run_tracking()
