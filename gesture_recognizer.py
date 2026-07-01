# gesture_recognizer.py - Gesture recognition state machine and validation

import time
import math
import config

class GestureRecognizer:
    def __init__(self):
        # Validation queue: list of raw gestures detected in recent frames
        self.validation_history = []
        self.active_gesture = "Idle"
        
        # Swipe velocity tracking
        # Stores tuples of (timestamp, x_pos, y_pos) of the wrist/hand centroid
        self.position_history = []
        self.last_swipe_time = 0.0

    def calculate_distance(self, pt1, pt2):
        """Calculates Euclidean distance between two 3D landmarks."""
        return math.sqrt(
            (pt1.x - pt2.x) ** 2 +
            (pt1.y - pt2.y) ** 2 +
            (pt1.z - pt2.z) ** 2
        )

    def get_extended_fingers(self, landmarks):
        """
        Heuristically determines which fingers are extended.
        Returns a list of 5 booleans [Thumb, Index, Middle, Ring, Pinky].
        """
        extended = [False] * 5
        
        # Landmarks indexes:
        # Wrist: 0
        # Thumb: 1-4 (MCP, PIP, DIP, Tip)
        # Index: 5-8
        # Middle: 9-12
        # Ring: 13-16
        # Pinky: 17-20
        
        # 1. Index finger (Tip 8 above Joint 6)
        extended[1] = landmarks[8].y < landmarks[6].y
        
        # 2. Middle finger (Tip 12 above Joint 10)
        extended[2] = landmarks[12].y < landmarks[10].y
        
        # 3. Ring finger (Tip 16 above Joint 14)
        extended[3] = landmarks[16].y < landmarks[14].y
        
        # 4. Pinky finger (Tip 20 above Joint 18)
        extended[4] = landmarks[20].y < landmarks[18].y
        
        # 5. Thumb (Tip 4 horizontal distance to Joint 2/5, depending on hand left/right)
        # For simplicity, we check if Tip 4 is far enough from Joint 2 or Knuckle 5
        # We can also compare tip 4 to DIP 3 distance or check horizontal orientation.
        thumb_index_knuckle_dist = abs(landmarks[4].x - landmarks[5].x)
        extended[0] = thumb_index_knuckle_dist > 0.07
        
        return extended

    def update_position_history(self, wrist_landmark):
        """Appends hand wrist coordinate to history and trims old items."""
        now = time.time()
        self.position_history.append((now, wrist_landmark.x, wrist_landmark.y))
        # Keep last 10 frames (approx 300ms)
        if len(self.position_history) > 10:
            self.position_history.pop(0)

    def check_swipes(self, extended_fingers):
        """
        Analyzes position history for rapid displacement (swipe gesture)
        when 3 fingers (Index, Middle, Ring) are extended.
        
        Returns:
            "Swipe_Left", "Swipe_Right", "Swipe_Up", or None
        """
        # Ensure we are in 3-finger state (Index, Middle, Ring extended, Pinky/Thumb optional/closed)
        if not (extended_fingers[1] and extended_fingers[2] and extended_fingers[3] and not extended_fingers[4]):
            return None
            
        now = time.time()
        if now - self.last_swipe_time < config.SWIPE_COOLDOWN:
            return None
            
        if len(self.position_history) < 4:
            return None
            
        # Compare current position to older buffered position (e.g. 3 frames ago)
        current = self.position_history[-1]
        older = self.position_history[-4]
        
        dt = current[0] - older[0]
        if dt <= 0:
            return None
            
        dx = current[1] - older[1]
        dy = current[2] - older[2]
        
        # Frame coordinates are horizontally mirrored, so:
        # dx > 0 means moving right in camera coordinates, which is left in mirrored screen space.
        # dx < 0 means moving left in camera coordinates, which is right in mirrored screen space.
        
        # Velocity values (displacement / time)
        vx = dx / dt
        vy = dy / dt
        
        # We also check absolute magnitude threshold
        mag_x = abs(dx)
        mag_y = abs(dy)
        
        # Horizontal swipe detection
        if mag_x > config.SWIPE_VELOCITY_THRESHOLD and mag_x > mag_y:
            self.last_swipe_time = now
            if dx > 0:
                return "Swipe_Left"
            else:
                return "Swipe_Right"
                
        # Vertical swipe detection (moving hand UP in frame = lower Y value)
        elif mag_y > config.SWIPE_VELOCITY_THRESHOLD and mag_y > mag_x:
            if dy < -config.SWIPE_VELOCITY_THRESHOLD: # Hand moving rapidly up
                self.last_swipe_time = now
                return "Swipe_Up"
                
        return None

    def recognize_frame_gesture(self, landmarks):
        """
        Determines the raw gesture candidate in a single frame.
        """
        extended = self.get_extended_fingers(landmarks)
        
        # Calculate key pinch distances
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        
        pinch_index_dist = self.calculate_distance(thumb_tip, index_tip)
        pinch_middle_dist = self.calculate_distance(thumb_tip, middle_tip)
        
        # 1. Safety Pause: Open Palm (All fingers extended, palm still)
        if all(extended):
            return "Pause"
            
        # 2. Check Swipes (Index, Middle, Ring extended)
        swipe = self.check_swipes(extended)
        if swipe:
            return swipe
            
        # 3. Two-Finger Scroll: Index + Middle extended close together
        if extended[1] and extended[2] and not extended[3] and not extended[4]:
            idx_mid_dist = self.calculate_distance(index_tip, middle_tip)
            if idx_mid_dist < config.SCROLL_CLOSE_THRESHOLD:
                return "Scroll"
                
        # 4. Clicks & Clicks/Drag
        # Thumb & Middle pinch = Right Click
        if pinch_middle_dist < config.PINCH_THRESHOLD:
            return "Right_Click"
            
        # Thumb & Index pinch = Left Click / Drag (handled by timeline hold)
        if pinch_index_dist < config.PINCH_THRESHOLD:
            return "Pinch_Active"
            
        # 5. Cursor movement (only index finger extended)
        if extended[1] and not extended[2] and not extended[3] and not extended[4]:
            return "Move"
            
        return "Idle"

    def process_frame(self, landmarks):
        """
        Processes hand landmarks, updates history, runs debouncing state machine.
        Returns:
            (validated_gesture, wrist_coordinate)
        """
        wrist = landmarks[0]
        self.update_position_history(wrist)
        
        # Get gesture candidate for this frame
        raw_gesture = self.recognize_frame_gesture(landmarks)
        
        # Feed validation queue
        self.validation_history.append(raw_gesture)
        if len(self.validation_history) > config.GESTURE_VALIDATION_FRAMES:
            self.validation_history.pop(0)
            
        # Validation Rule: All items in queue must match raw_gesture to lock state change
        if len(self.validation_history) == config.GESTURE_VALIDATION_FRAMES:
            first_val = self.validation_history[0]
            if all(g == first_val for g in self.validation_history):
                self.active_gesture = first_val
                
        return self.active_gesture, wrist
        
    def reset(self):
        """Resets histories (called on loss of tracking)."""
        self.validation_history.clear()
        self.position_history.clear()
        self.active_gesture = "Idle"
