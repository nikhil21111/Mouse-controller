# hand_tracker.py - MediaPipe Hand Tracking wrapper

import cv2
import mediapipe as mp
import config

class HandTracker:
    def __init__(self, mode=False, max_hands=1, model_complexity=1,
                 detection_con=config.MIN_DETECTION_CONFIDENCE,
                 tracking_con=config.MIN_TRACKING_CONFIDENCE):
        """Initializes the MediaPipe Hands module."""
        self.mode = mode
        self.max_hands = max_hands
        self.model_complexity = model_complexity
        self.detection_con = detection_con
        self.tracking_con = tracking_con

        # MediaPipe Solutions setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.tracking_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Style definition for skeletal lines (minimalistic premium gray/neon)
        self.hand_conn_style = self.mp_draw.DrawingSpec(
            color=(0, 255, 0), thickness=2, circle_radius=2
        )
        self.hand_joint_style = self.mp_draw.DrawingSpec(
            color=(100, 100, 100), thickness=1, circle_radius=1
        )
        
        self.results = None

    def find_hands(self, img, draw=True):
        """
        Processes BGR image and finds hand landmarks.
        Draws landmarks on the image if draw is True.
        """
        # Convert BGR image to RGB for MediaPipe processing
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    img, 
                    hand_lms, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.hand_joint_style,
                    self.hand_conn_style
                )
        return img

    def get_landmarks(self, hand_idx=0):
        """
        Returns landmarks for the selected hand index as a list of landmarks objects.
        Landmark coordinates x, y, z are normalized between 0.0 and 1.0.
        """
        if self.results and self.results.multi_hand_landmarks:
            if hand_idx < len(self.results.multi_hand_landmarks):
                return self.results.multi_hand_landmarks[hand_idx].landmark
        return None
        
    def close(self):
        """Closes Hand Tracking resources."""
        self.hands.close()
