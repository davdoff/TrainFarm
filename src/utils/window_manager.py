#!/usr/bin/env python3
"""
Window Manager Module
Handles game window detection and coordinate conversion for windowed/half-screen mode.
"""

import pyautogui
from typing import Optional, Tuple
import platform


class WindowManager:
    """Manages game window coordinates and conversions."""

    def __init__(self, use_window_mode: bool = False, window_title: Optional[str] = None):
        """
        Initialize window manager.

        Args:
            use_window_mode: If True, use window-relative coordinates. If False, use full screen.
            window_title: Title of the game window to find (e.g., "TrainStation" or part of it)
        """
        self.use_window_mode = use_window_mode
        self.window_title = window_title
        self.window_x = 0
        self.window_y = 0
        self.window_width = 0
        self.window_height = 0

        if use_window_mode:
            self._detect_window()
        else:
            # Full screen mode
            screen_width, screen_height = pyautogui.size()
            self.window_width = screen_width
            self.window_height = screen_height

    def _detect_window(self):
        """Detect game window position and size."""
        if platform.system() == 'Darwin':  # macOS
            self._detect_window_macos()
        elif platform.system() == 'Windows':
            self._detect_window_windows()
        else:  # Linux
            self._detect_window_linux()

    def _detect_window_macos(self):
        """Detect window on macOS using AppleScript."""
        try:
            import subprocess

            if self.window_title:
                # Find window by title
                script = f'''
                tell application "System Events"
                    set appList to every process whose name contains "{self.window_title}"
                    if (count of appList) > 0 then
                        set targetApp to item 1 of appList
                        tell targetApp
                            set windowList to every window
                            if (count of windowList) > 0 then
                                set targetWindow to item 1 of windowList
                                set windowPosition to position of targetWindow
                                set windowSize to size of targetWindow
                                return {{item 1 of windowPosition, item 2 of windowPosition, item 1 of windowSize, item 2 of windowSize}}
                            end if
                        end tell
                    end if
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    # Parse output: "x, y, width, height"
                    parts = result.stdout.strip().split(', ')
                    if len(parts) == 4:
                        self.window_x = int(parts[0])
                        self.window_y = int(parts[1])
                        self.window_width = int(parts[2])
                        self.window_height = int(parts[3])
                        print(f"✅ Window detected: ({self.window_x}, {self.window_y}) {self.window_width}x{self.window_height}")
                        return

            # Fallback: Use left half of screen
            print("⚠️  Could not detect window, using left half of screen")
            self._use_left_half_screen()

        except Exception as e:
            print(f"⚠️  Error detecting window: {e}")
            self._use_left_half_screen()

    def _detect_window_windows(self):
        """Detect window on Windows."""
        try:
            import win32gui

            if self.window_title:
                hwnd = win32gui.FindWindow(None, self.window_title)
                if hwnd:
                    rect = win32gui.GetWindowRect(hwnd)
                    self.window_x = rect[0]
                    self.window_y = rect[1]
                    self.window_width = rect[2] - rect[0]
                    self.window_height = rect[3] - rect[1]
                    print(f"✅ Window detected: ({self.window_x}, {self.window_y}) {self.window_width}x{self.window_height}")
                    return

            # Fallback: Use left half of screen
            print("⚠️  Could not detect window, using left half of screen")
            self._use_left_half_screen()

        except ImportError:
            print("⚠️  pywin32 not installed, using left half of screen")
            self._use_left_half_screen()
        except Exception as e:
            print(f"⚠️  Error detecting window: {e}")
            self._use_left_half_screen()

    def _detect_window_linux(self):
        """Detect window on Linux."""
        # For Linux, fallback to left half for now
        print("⚠️  Linux window detection not implemented, using left half of screen")
        self._use_left_half_screen()

    def _use_left_half_screen(self):
        """Use left half of screen as window."""
        screen_width, screen_height = pyautogui.size()
        self.window_x = 0
        self.window_y = 0
        self.window_width = screen_width // 2
        self.window_height = screen_height

    def set_manual_window(self, x: int, y: int, width: int, height: int):
        """
        Manually set window position and size.

        Args:
            x, y: Top-left corner of GAME AREA (not browser window)
            width, height: Game area dimensions
        """
        self.window_x = x
        self.window_y = y
        self.window_width = width
        self.window_height = height
        self.use_window_mode = True
        print(f"✅ Manual window set: ({x}, {y}) {width}x{height}")

    def set_browser_game_area(self, browser_top_offset: int = 0, browser_side_offset: int = 0):
        """
        Adjust for browser chrome when playing a browser game.
        Call this AFTER detecting/setting the window to trim browser UI elements.

        Args:
            browser_top_offset: Pixels to trim from top (address bar, tabs, bookmarks)
            browser_side_offset: Pixels to trim from sides (scrollbars, margins)
        """
        self.window_y += browser_top_offset
        self.window_height -= browser_top_offset

        if browser_side_offset > 0:
            self.window_x += browser_side_offset
            self.window_width -= (browser_side_offset * 2)

        print(f"✅ Browser chrome adjusted: top={browser_top_offset}px, sides={browser_side_offset}px")
        print(f"   Game area: ({self.window_x}, {self.window_y}) {self.window_width}x{self.window_height}")

    def to_screen_coords(self, rel_x: float, rel_y: float) -> Tuple[int, int]:
        """
        Convert window-relative percentage coordinates to screen coordinates.

        Args:
            rel_x: X position as percentage of window width (0.0 to 1.0)
            rel_y: Y position as percentage of window height (0.0 to 1.0)

        Returns:
            (screen_x, screen_y): Absolute screen coordinates
        """
        screen_x = int(self.window_x + (rel_x * self.window_width))
        screen_y = int(self.window_y + (rel_y * self.window_height))
        return (screen_x, screen_y)

    def to_relative_coords(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convert screen coordinates to window-relative percentages.

        Args:
            screen_x, screen_y: Absolute screen coordinates

        Returns:
            (rel_x, rel_y): Position as percentage of window (0.0 to 1.0)
        """
        rel_x = (screen_x - self.window_x) / self.window_width
        rel_y = (screen_y - self.window_y) / self.window_height
        return (rel_x, rel_y)

    def capture_window(self):
        """
        Capture screenshot of the game window only.

        Returns:
            PIL Image of the window
        """
        return pyautogui.screenshot(region=(
            self.window_x,
            self.window_y,
            self.window_width,
            self.window_height
        ))

    def capture_region(self, rel_x: float, rel_y: float, rel_width: float, rel_height: float):
        """
        Capture a region within the window using relative coordinates.

        Args:
            rel_x, rel_y: Top-left corner as percentage of window (0.0 to 1.0)
            rel_width, rel_height: Size as percentage of window (0.0 to 1.0)

        Returns:
            PIL Image of the region
        """
        screen_x = int(self.window_x + (rel_x * self.window_width))
        screen_y = int(self.window_y + (rel_y * self.window_height))
        width = int(rel_width * self.window_width)
        height = int(rel_height * self.window_height)

        return pyautogui.screenshot(region=(screen_x, screen_y, width, height))

    def click(self, rel_x: float, rel_y: float, delay: float = 0.5):
        """
        Click at window-relative coordinates.

        Args:
            rel_x, rel_y: Position as percentage of window (0.0 to 1.0)
            delay: Delay before click
        """
        screen_x, screen_y = self.to_screen_coords(rel_x, rel_y)
        pyautogui.click(screen_x, screen_y)
        if delay > 0:
            import time
            time.sleep(delay)

    def get_window_info(self) -> dict:
        """Get window information."""
        return {
            'x': self.window_x,
            'y': self.window_y,
            'width': self.window_width,
            'height': self.window_height,
            'use_window_mode': self.use_window_mode
        }


def test_window_manager():
    """Test window manager."""
    print("=" * 60)
    print("Window Manager Test")
    print("=" * 60)
    print()
    print("Choose mode:")
    print("1. Full screen mode")
    print("2. Window mode (detect by title)")
    print("3. Window mode (left half of screen)")
    print("4. Manual window mode")
    print()

    choice = input("Enter choice (1-4): ").strip()

    if choice == "1":
        wm = WindowManager(use_window_mode=False)
    elif choice == "2":
        title = input("Enter window title (or part of it): ").strip()
        wm = WindowManager(use_window_mode=True, window_title=title)
    elif choice == "3":
        wm = WindowManager(use_window_mode=True)
    elif choice == "4":
        x = int(input("Window X: "))
        y = int(input("Window Y: "))
        width = int(input("Window width: "))
        height = int(input("Window height: "))
        wm = WindowManager(use_window_mode=True)
        wm.set_manual_window(x, y, width, height)
    else:
        print("Invalid choice")
        return

    print("\n" + "=" * 60)
    print("Window Info:")
    print("=" * 60)
    info = wm.get_window_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Coordinate Conversion Examples:")
    print("=" * 60)

    # Test some relative coordinates
    test_coords = [
        (0.0, 0.0, "Top-left"),
        (0.5, 0.5, "Center"),
        (1.0, 1.0, "Bottom-right"),
        (0.25, 0.25, "Quarter point"),
    ]

    for rel_x, rel_y, label in test_coords:
        screen_x, screen_y = wm.to_screen_coords(rel_x, rel_y)
        print(f"{label}: ({rel_x:.2f}, {rel_y:.2f}) → screen ({screen_x}, {screen_y})")


if __name__ == "__main__":
    test_window_manager()
