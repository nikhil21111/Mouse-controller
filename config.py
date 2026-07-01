# config.py - Configuration parameters for macOS Webcam Air Trackpad

# Camera settings
CAMERA_ID = 0          # Default built-in or external webcam
FRAME_WIDTH = 640      # Target capture width (640x480 standardizes load)
FRAME_HEIGHT = 480     # Target capture height

# Multi-threading and frame skip
# On older systems, we process every Nth frame to reduce CPU load
FRAME_SKIP_COUNT = 1   # 1 = process every frame, 2 = process every second frame

# MediaPipe Hand Tracker settings
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7

# Coordinate smoothing and sensitivity
MOUSE_SENSITIVITY = 2.5       # Multiplier for coordinate displacement
EMA_ALPHA = 0.25              # Exponential Moving Average weight (0 < alpha <= 1). Lower = smoother, higher = faster

# Gesture Thresholds (relative distances in normalized hand space)
PINCH_THRESHOLD = 0.04        # Distance between thumb and finger tips for click
SCROLL_CLOSE_THRESHOLD = 0.05 # Max distance between index & middle tips for scrolling
SCROLL_SPEED_MULTIPLIER = 2.0  # Speed factor for scrolling inputs

# Swipe movement thresholds (for 3-finger space switching)
SWIPE_VELOCITY_THRESHOLD = 0.07 # Min displacement between consecutive buffered updates
SWIPE_COOLDOWN = 1.0           # Seconds to wait before another swipe triggers

# Validation buffer settings
GESTURE_VALIDATION_FRAMES = 3  # A gesture state must persist for this many frames
LOSS_OF_TRACKING_FRAMES = 5    # Reset tracking if hand is missing for this many frames

# Active Keyboard Binds for Gestures
SHORTCUT_SPACE_LEFT = ["ctrl", "right"]
SHORTCUT_SPACE_RIGHT = ["ctrl", "left"]
SHORTCUT_MISSION_CONTROL = ["ctrl", "up"]

# Gesture Enablement Toggles
PINCH_ENABLED = True
SCROLL_ENABLED = True
SWIPE_ENABLED = True

