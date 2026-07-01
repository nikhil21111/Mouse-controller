# coordinate_mapper.py - Screen coordinate mapping and EMA smoothing

import numpy as np
import config

class CoordinateMapper:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Virtual trackpad box in normalized camera space [x_min, x_max, y_min, y_max]
        # Prevents users from having to stretch their arms to hit the screen edges
        self.active_box = [0.25, 0.75, 0.25, 0.75]
        
        # Coordinates history for smoothing
        self.smooth_x = None
        self.smooth_y = None
        
        # Last raw position (for displacement calculation if relative movement is preferred)
        self.prev_raw_x = None
        self.prev_raw_y = None

    def map_coordinates(self, norm_x, norm_y):
        """
        Maps normalized camera coordinates (0.0 to 1.0) to screen coordinates
        applying a virtual trackpad bounding box and EMA smoothing.
        
        Returns:
            (screen_x, screen_y) - smoothed integer screen coordinates
        """
        # Horizontal mirror mapping: webcam feed is mirrored, so we invert X
        x_mapped = 1.0 - norm_x
        y_mapped = norm_y
        
        # 1. Scale coordinates within the active virtual trackpad bounding box
        x_min, x_max, y_min, y_max = self.active_box
        
        # Normalize inside the virtual box and clamp between 0 and 1
        x_scaled = (x_mapped - x_min) / (x_max - x_min)
        y_scaled = (y_mapped - y_min) / (y_max - y_min)
        
        x_scaled = np.clip(x_scaled, 0.0, 1.0)
        y_scaled = np.clip(y_scaled, 0.0, 1.0)
        
        # Convert to screen target coordinates
        target_x = x_scaled * self.screen_width
        target_y = y_scaled * self.screen_height
        
        # 2. Smooth target using Exponential Moving Average (EMA) to remove jitter
        if self.smooth_x is None or self.smooth_y is None:
            self.smooth_x = target_x
            self.smooth_y = target_y
        else:
            alpha = config.EMA_ALPHA
            self.smooth_x = (alpha * target_x) + ((1 - alpha) * self.smooth_x)
            self.smooth_y = (alpha * target_y) + ((1 - alpha) * self.smooth_y)
            
        return int(round(self.smooth_x)), int(round(self.smooth_y))

    def reset(self):
        """Resets coordinate smoothing state (called on loss of tracking)."""
        self.smooth_x = None
        self.smooth_y = None
        self.prev_raw_x = None
        self.prev_raw_y = None
