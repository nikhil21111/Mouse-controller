# main.py - Main application loop and gesture manager

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

def main():
    print("=== macOS Webcam Air Trackpad Startup ===")
    
    # 1. Programmatic Accessibility Permission Check
    if not utils.is_accessibility_enabled():
        utils.print_permission_warning()
        # Non-blocking check for local developer environment, but alert and exit on macOS
        if utils.is_macos():
            sys.exit(1)
            
    # 2. Setup core controllers
    os_controller = OSController()
    
    # Get active screen dimensions
    try:
        screen_w, screen_h = os_controller.get_screen_size()
        print(f"[+] Screen Size Detected: {screen_w}x{screen_h}")
    except Exception as e:
        print(f"[-] Failed to get screen size: {e}. Defaulting to 1920x1080.")
        screen_w, screen_h = 1920, 1080
        
    mapper = CoordinateMapper(screen_w, screen_h)
    tracker = HandTracker()
    recognizer = GestureRecognizer()
    
    # Initialize camera capture
    cap = cv2.VideoCapture(config.CAMERA_ID)
    if not cap.isOpened():
        print("[-] ERROR: Cannot open webcam. Check AVFoundation/Camera Permissions.")
        sys.exit(1)
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    
    print("[+] Camera feed started. Press 'q' in the camera window to quit.")
    
    # FPS and performance stats
    fps_time = time.time()
    fps_count = 0
    fps_display = 0
    frame_idx = 0
    
    # Tracking loss counter
    consecutive_missing_frames = 0
    
    while True:
        success, frame = cap.read()
        if not success:
            print("[-] Warning: Empty frame received.")
            continue
            
        frame_idx += 1
        
        # Performance skip: only process every Nth frame
        if frame_idx % config.FRAME_SKIP_COUNT == 0:
            # Mirror frame horizontally for intuitive self-viewing
            frame = cv2.flip(frame, 1)
            
            # Run MediaPipe tracking
            frame = tracker.find_hands(frame, draw=True)
            landmarks = tracker.get_landmarks(0)
            
            if landmarks:
                consecutive_missing_frames = 0
                
                # Run gesture state machine
                gesture, wrist = recognizer.process_frame(landmarks)
                
                # Execute actions based on validated gesture state
                if gesture == "Move":
                    index_tip = landmarks[8]
                    # Map coordinates (coordinate mapper handles the mirroring inside)
                    # We pass unmirrored norm_x to mapper, which handles 1.0 - norm_x
                    screen_x, screen_y = mapper.map_coordinates(landmarks[8].x, landmarks[8].y)
                    os_controller.move_to(screen_x, screen_y)
                    os_controller.reset_scroll()
                    
                elif gesture == "Pinch_Active":
                    index_tip = landmarks[8]
                    screen_x, screen_y = mapper.map_coordinates(landmarks[8].x, landmarks[8].y)
                    os_controller.drag_to(screen_x, screen_y)
                    os_controller.reset_scroll()
                    
                elif gesture == "Right_Click":
                    os_controller.right_click()
                    os_controller.reset_scroll()
                    # Transition immediately to move to prevent continuous clicking
                    recognizer.active_gesture = "Move"
                    
                elif gesture == "Scroll":
                    index_tip = landmarks[8]
                    # Map coordinates vertically
                    os_controller.scroll(index_tip.y, config.SCROLL_SPEED_MULTIPLIER)
                    
                elif gesture == "Swipe_Left":
                    print("[*] Action: Swipe Left -> Switching Space Right")
                    os_controller.trigger_shortcut(config.SHORTCUT_SPACE_LEFT)
                    # Force cooldown by resetting state
                    recognizer.active_gesture = "Idle"
                    
                elif gesture == "Swipe_Right":
                    print("[*] Action: Swipe Right -> Switching Space Left")
                    os_controller.trigger_shortcut(config.SHORTCUT_SPACE_RIGHT)
                    recognizer.active_gesture = "Idle"
                    
                elif gesture == "Swipe_Up":
                    print("[*] Action: Swipe Up -> Opening Mission Control")
                    os_controller.trigger_shortcut(config.SHORTCUT_MISSION_CONTROL)
                    recognizer.active_gesture = "Idle"
                    
                elif gesture == "Pause":
                    os_controller.release_left()
                    os_controller.reset_scroll()
                    mapper.reset()
                    
                elif gesture == "Idle":
                    os_controller.release_left()
                    os_controller.reset_scroll()
                    mapper.reset()
            else:
                consecutive_missing_frames += 1
                gesture = "Loss of Tracking"
                if consecutive_missing_frames >= config.LOSS_OF_TRACKING_FRAMES:
                    # Reset all trackers on tracking loss
                    recognizer.reset()
                    mapper.reset()
                    os_controller.reset_scroll()
                    os_controller.release_left()
            
            # --- Draw Sleek HUD Elements (Premium aesthetics on opencv window) ---
            # Banner Background
            cv2.rectangle(frame, (10, 10), (280, 120), (30, 30, 30), cv2.FILLED)
            cv2.rectangle(frame, (10, 10), (280, 120), (100, 100, 100), 1)
            
            # Text HUD Content
            color_map = {
                "Move": (0, 255, 0),        # Neon green
                "Pinch_Active": (0, 165, 255), # Orange/Neon
                "Right_Click": (255, 0, 255),   # Magenta
                "Scroll": (255, 255, 0),     # Cyan
                "Pause": (0, 0, 255),        # Red
                "Swipe_Left": (255, 128, 0),
                "Swipe_Right": (255, 128, 0),
                "Swipe_Up": (255, 128, 0),
                "Idle": (150, 150, 150),
                "Loss of Tracking": (80, 80, 80)
            }
            
            txt_color = color_map.get(gesture, (255, 255, 255))
            
            cv2.putText(frame, "AIR TRACKPAD ACTIVE", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"State: {gesture}", (20, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, txt_color, 2, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {fps_display}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)
            cv2.putText(frame, "Accessibility: APPROVED", (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
                        
            # Show output frame in a window
            cv2.imshow("macOS Air Trackpad Feed", frame)
            
        # FPS Calculation
        fps_count += 1
        curr_time = time.time()
        if curr_time - fps_time >= 1.0:
            fps_display = fps_count
            fps_count = 0
            fps_time = curr_time
            
        # Break loop with 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Cleanup
    print("[*] Releasing resources and shutting down...")
    os_controller.release_left()
    cap.release()
    cv2.destroyAllWindows()
    tracker.close()
    print("[+] Shutdown complete.")

if __name__ == "__main__":
    main()
