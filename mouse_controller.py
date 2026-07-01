# mouse_controller.py - OS Mouse and Keyboard controls via pynput

from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
import time

class OSController:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        # State tracker for click dragging
        self.is_left_pressed = False
        
        # Last position tracker for scrolling delta
        self.prev_scroll_y = None

    def get_screen_size(self):
        """Returns the screen size of the primary monitor using Quartz (PyObjC)."""
        try:
            from Quartz import CGDisplayBounds, CGMainDisplayID
            bounds = CGDisplayBounds(CGMainDisplayID())
            return int(bounds.size.width), int(bounds.size.height)
        except ImportError:
            # Fallback if pyobjc is not loaded yet (e.g. startup pre-checks)
            import tkinter as tk
            root = tk.Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return width, height

    def move_to(self, x, y):
        """Moves cursor absolutely to screen coordinates."""
        # Ensure we release left press if moving without pinch (fail-safe)
        if self.is_left_pressed:
            self.release_left()
        self.mouse.position = (x, y)

    def drag_to(self, x, y):
        """Moves cursor and handles dragging if left press is active."""
        if not self.is_left_pressed:
            self.press_left()
        self.mouse.position = (x, y)

    def press_left(self):
        """Presses and holds the left mouse button."""
        if not self.is_left_pressed:
            self.mouse.press(Button.left)
            self.is_left_pressed = True

    def release_left(self):
        """Releases the left mouse button."""
        if self.is_left_pressed:
            self.mouse.release(Button.left)
            self.is_left_pressed = False

    def right_click(self):
        """Triggers a single right-click."""
        # Release left click before right clicking
        if self.is_left_pressed:
            self.release_left()
        self.mouse.click(Button.right, 1)

    def scroll(self, current_y, speed_multiplier):
        """Scrolls vertically based on vertical displacement of scroll fingers."""
        if self.is_left_pressed:
            self.release_left()
            
        if self.prev_scroll_y is None:
            self.prev_scroll_y = current_y
            return
            
        # Delta calculation (Mac screen coords: Y increases downwards)
        dy = current_y - self.prev_scroll_y
        self.prev_scroll_y = current_y
        
        # Scroll action: positive scroll_y scrolls UP, negative scrolls DOWN
        # dy > 0 means hand moved down, which corresponds to scrolling down (so scroll amount should be negative)
        scroll_amount = -int(round(dy * speed_multiplier))
        
        if scroll_amount != 0:
            self.mouse.scroll(0, scroll_amount)

    def reset_scroll(self):
        """Resets scroll displacement tracking."""
        self.prev_scroll_y = None

    def trigger_shortcut(self, shortcut_keys):
        """
        Simulates pressing a combination of modifier and navigation keys.
        Example shortcut_keys: ['ctrl', 'right'] or ['ctrl', 'up']
        """
        # Map key strings to pynput Key objects
        key_mapping = {
            "ctrl": Key.ctrl,
            "cmd": Key.cmd,
            "shift": Key.shift,
            "alt": Key.alt,
            "left": Key.left,
            "right": Key.right,
            "up": Key.up,
            "down": Key.down
        }
        
        pressed_keys = []
        try:
            # Press all keys in sequence
            for k in shortcut_keys:
                key_obj = key_mapping.get(k.lower(), k)
                self.keyboard.press(key_obj)
                pressed_keys.append(key_obj)
                time.sleep(0.02) # Short delay to let OS process
                
            # Release keys in reverse order
            for key_obj in reversed(pressed_keys):
                self.keyboard.release(key_obj)
                
        except Exception as e:
            print(f"[-] Failed to execute shortcut {shortcut_keys}: {e}")
            # Ensure keys are released on error
            for key_obj in pressed_keys:
                try:
                    self.keyboard.release(key_obj)
                except:
                    pass
