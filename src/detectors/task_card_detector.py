#!/usr/bin/env python3
"""
Task Card Detector
Detects individual task cards and determines if they're available.
"""

import cv2
import numpy as np
import pyautogui
from typing import List, Tuple, Optional
from pathlib import Path

from src.config.detection_config import (
    USE_DYNAMIC_CARD_DETECTION,
    CARD_WIDTH,
    CARD_HEIGHT,
    CARD_START_X,
    CARD_START_Y,
    CARD_SPACING
)


class TaskCardDetector:
    """Detects and analyzes task cards."""

    def __init__(self, window_manager=None):
        """
        Initialize task card detector.

        Args:
            window_manager: WindowManager instance for coordinate conversion (optional)
        """
        self.window_manager = window_manager
        self.green_checkmark_template = None  # You can add this if you want
        self.locked_task_template = "Templates/tasks/LockedTaskIcon.png"

        if window_manager:
            self.window_width = window_manager.window_width
            self.window_height = window_manager.window_height
        else:
            self.window_width, self.window_height = pyautogui.size()

        # Get scale factor for Retina displays
        self.scale_factor = self._get_scale_factor()
        print(f"Display scale factor: {self.scale_factor}")

    def _get_scale_factor(self):
        """Calculate scale factor for Retina/HiDPI displays."""
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_height, screenshot_width = screenshot_np.shape[:2]

        scale_x = screenshot_width / self.window_width
        scale_y = screenshot_height / self.window_height

        return (scale_x + scale_y) / 2

    def find_task_cards_by_rectangle_detection(self) -> List[Tuple[int, int, int, int]]:
        """
        Dynamically detect task cards by finding large rectangles in the screenshot.
        More robust for scrolling scenarios.

        Returns:
            List of (x, y, width, height) for each task card found (in absolute screen coordinates)
        """
        # Take screenshot
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get expected card dimensions (in logical pixels)
        expected_width = int(CARD_WIDTH * self.window_width)
        expected_height = int(CARD_HEIGHT * self.window_height)

        # Get scale factor
        scale_factor = self._get_scale_factor()

        # Scale expected dimensions to screenshot space
        expected_width_scaled = int(expected_width * scale_factor)
        expected_height_scaled = int(expected_height * scale_factor)

        # Find rectangles that match card size (within 20% tolerance)
        detected_cards = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Check if size matches expected card dimensions (within tolerance)
            width_match = 0.8 <= w / expected_width_scaled <= 1.2
            height_match = 0.8 <= h / expected_height_scaled <= 1.2

            # Check aspect ratio is reasonable (cards are taller than wide)
            aspect_ratio = h / w if w > 0 else 0
            aspect_ratio_ok = 1.5 <= aspect_ratio <= 2.5

            if width_match and height_match and aspect_ratio_ok:
                # Convert back to logical pixel space
                x_logical = int(x / scale_factor)
                y_logical = int(y / scale_factor)

                detected_cards.append({
                    'x': x_logical,
                    'y': y_logical,
                    'width': expected_width,  # Use expected width (hardcoded)
                    'height': expected_height,  # Use expected height (hardcoded)
                    'confidence': min(w / expected_width_scaled, h / expected_height_scaled)
                })

        # Sort by X position (left to right)
        detected_cards.sort(key=lambda c: c['x'])

        # Remove duplicates (cards detected multiple times)
        filtered_cards = []
        for card in detected_cards:
            # Check if this card is too close to an already added card
            is_duplicate = False
            for existing in filtered_cards:
                x_diff = abs(card['x'] - existing['x'])
                if x_diff < expected_width * 0.3:  # Within 30% of card width
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered_cards.append(card)

        # Convert to tuples
        cards = [(c['x'], c['y'], c['width'], c['height']) for c in filtered_cards]

        print(f"Detected {len(cards)} task cards by rectangle detection")
        return cards

    def find_task_cards(self) -> List[Tuple[int, int, int, int]]:
        """
        Find all task card regions.
        Uses dynamic detection or fixed positions based on config.

        Returns:
            List of (x, y, width, height) for each task card found (in absolute screen coordinates)
        """
        cards = []

        # Choose detection method based on config
        if USE_DYNAMIC_CARD_DETECTION:
            # Try dynamic rectangle detection
            cards = self.find_task_cards_by_rectangle_detection()

            if cards and len(cards) >= 1:
                print(f"✓ Using {len(cards)} dynamically detected cards")
                return cards

            # Fallback to fixed positions if detection fails
            print("⚠️  Dynamic detection failed, falling back to fixed positions")
        else:
            print("Using fixed position detection (dynamic detection disabled)")

        # Fixed position detection (fallback or if dynamic disabled)
        cards = []

        # Task cards appear in a horizontal row
        # Convert window-relative percentages to absolute pixels
        card_width = int(CARD_WIDTH * self.window_width)
        card_height = int(CARD_HEIGHT * self.window_height)
        start_x = int(CARD_START_X * self.window_width)
        start_y = int(CARD_START_Y * self.window_height)
        spacing = int(CARD_SPACING * self.window_width)

        # Add window offset if using window mode
        if self.window_manager:
            start_x += self.window_manager.window_x
            start_y += self.window_manager.window_y

        # Check for up to 5 task positions
        for i in range(5):
            x = start_x + (i * spacing)
            y = start_y

            # Make sure we're not going off window bounds
            if self.window_manager:
                max_x = self.window_manager.window_x + self.window_manager.window_width
                if x + card_width > max_x:
                    break
            else:
                if x + card_width > self.window_width:
                    break

            cards.append((x, y, card_width, card_height))

        print(f"Using {len(cards)} estimated task card positions")
        return cards

    def has_green_checkmark(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Check if a task card has a green checkmark (available).

        Args:
            x, y, width, height: Task card region

        Returns:
            True if green checkmark found, False otherwise
        """
        # Capture the card region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Convert to HSV
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

        # Green color range for checkmark
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])

        # Create mask for green
        green_mask = cv2.inRange(hsv, lower_green, upper_green)

        # Count green pixels
        green_pixels = cv2.countNonZero(green_mask)
        total_pixels = width * height

        green_percentage = green_pixels / total_pixels

        # If more than 1% green (checkmark is present)
        if green_percentage > 0.01:
            print(f"    ✓ Green checkmark detected ({green_percentage:.2%} green)")
            return True

        return False

    def has_black_text(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Check if task card has black text (material amounts).

        Args:
            x, y, width, height: Task card region

        Returns:
            True if black text found in material area
        """
        # Look in the upper-middle area of card where materials appear
        material_y = y + height // 4
        material_height = height // 3

        # Capture the material region
        screenshot = pyautogui.screenshot(region=(x, material_y, width, material_height))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        # Black text detection (values close to 0)
        black_mask = cv2.inRange(gray, 0, 50)

        black_pixels = cv2.countNonZero(black_mask)
        total_pixels = width * material_height

        black_percentage = black_pixels / total_pixels

        # If more than 2% black pixels (text is present)
        if black_percentage > 0.02:
            print(f"    ✓ Black text detected ({black_percentage:.2%} black)")
            return True

        return False

    def is_task_locked(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Check if a task card has the locked symbol in the middle.

        Args:
            x, y, width, height: Task card region

        Returns:
            True if locked symbol found, False otherwise
        """
        from src.detectors.template_matcher import find_template_on_screen
        from pathlib import Path

        # Check if locked template exists
        if not Path(self.locked_task_template).exists():
            return False

        # Capture the card region (middle area where lock symbol appears)
        # Focus on center of card
        center_x = x + width // 4
        center_y = y + height // 4
        center_width = width // 2
        center_height = height // 2

        # Capture center region
        screenshot = pyautogui.screenshot(region=(center_x, center_y, center_width, center_height))
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Try to find locked symbol using template matching on the center region
        # We'll use a temporary save and load approach
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, screenshot_bgr)

        # Load template
        template = cv2.imread(self.locked_task_template)
        if template is None:
            return False

        # Load screenshot
        img = cv2.imread(tmp_path)

        # Template matching
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Clean up temp file
        import os
        os.unlink(tmp_path)

        # Threshold for locked symbol (lower since it's a distinctive symbol)
        if max_val >= 0.6:
            print(f"    🔒 LOCKED symbol detected (confidence: {max_val:.2%})")
            return True

        return False

    def is_task_available(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Determine if a task card is available (not completing or locked).

        Args:
            x, y, width, height: Task card region

        Returns:
            True if task is available, False if completing or locked
        """
        # First check if task is locked (highest priority - skip if locked)
        if self.is_task_locked(x, y, width, height):
            return False

        # Check for green checkmark (strong indicator)
        if self.has_green_checkmark(x, y, width, height):
            return True

        # Check for black text (material amounts)
        if self.has_black_text(x, y, width, height):
            return True

        # If neither found, probably completing (has large timer)
        return False

    def get_click_position(self, x: int, y: int, width: int, height: int) -> Tuple[int, int]:
        """
        Get the position to click on a task card.
        Clicks on the whitish surface next to materials.

        Args:
            x, y, width, height: Task card region

        Returns:
            (x, y) coordinates to click
        """
        # Click in the upper-middle area, slightly right of center
        # This is typically the whitish surface next to materials
        click_x = x + width // 2 + 50  # Slightly right of center
        click_y = y + height // 3       # Upper third of card

        return (click_x, click_y)

    def scroll_tasks_left(self, scroll_amount: int = 400):
        """
        Scroll/drag the task list to the left to reveal tasks on the right.

        Args:
            scroll_amount: Number of pixels to scroll left
        """
        print("\n=== Scrolling Tasks Left ===")
        print(f"Dragging task list {scroll_amount}px to reveal more tasks...")

        # Get the middle of the task card area
        # Calculate drag start position (center of task area)
        if self.window_manager:
            start_x = self.window_manager.window_x + int(self.window_width * 0.5)
            start_y = self.window_manager.window_y + int(self.window_height * CARD_START_Y) + int(self.window_height * CARD_HEIGHT * 0.5)
        else:
            start_x = int(self.window_width * 0.5)
            start_y = int(self.window_height * CARD_START_Y) + int(self.window_height * CARD_HEIGHT * 0.5)

        # Drag from center to the left (to reveal tasks on the right)
        end_x = start_x - scroll_amount

        print(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {start_y})")

        # Perform the drag
        pyautogui.moveTo(start_x, start_y)
        import time
        time.sleep(0.2)
        pyautogui.drag(-scroll_amount, 0, duration=0.5)
        time.sleep(0.5)  # Wait for scroll to settle

        print("✅ Scroll complete")

    def find_first_available_task(self, max_scrolls: int = 3) -> Optional[Tuple[int, int]]:
        """
        Find the first available task card and return click coordinates.
        If no tasks found, scroll left to reveal more tasks.

        Args:
            max_scrolls: Maximum number of times to scroll if no tasks found

        Returns:
            (x, y) coordinates to click, or None if no available task
        """
        print("\n=== Detecting Task Cards ===")

        scrolls_performed = 0

        while scrolls_performed <= max_scrolls:
            # Find all task cards
            cards = self.find_task_cards()

            if not cards:
                print("❌ No task cards detected")
                return None

            print(f"Found {len(cards)} task card(s)")

            # Check each card from left to right
            for i, (x, y, w, h) in enumerate(cards, 1):
                print(f"\nChecking card {i}: region ({x}, {y}, {w}x{h})")

                if self.is_task_available(x, y, w, h):
                    print(f"  ✅ Card {i} is AVAILABLE!")

                    # Get click position
                    click_x, click_y = self.get_click_position(x, y, w, h)
                    print(f"  Click position: ({click_x}, {click_y})")

                    return (click_x, click_y)
                else:
                    print(f"  ⏱️  Card {i} is COMPLETING or LOCKED")

            # No available tasks found in current view
            if scrolls_performed < max_scrolls:
                print(f"\n⚠️  No available tasks in current view (scroll {scrolls_performed + 1}/{max_scrolls})")
                self.scroll_tasks_left(scroll_amount=400)
                scrolls_performed += 1
                print(f"Checking tasks again after scroll...")
            else:
                break

        print(f"\n❌ No available tasks found after {scrolls_performed} scroll(s)")
        return None

    def visualize_detection(self, save_path: str = "task_cards_debug.png"):
        """
        Create visualization showing detected task cards.
        Shows locked tasks in orange, completing in red, available in green.
        """
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        cards = self.find_task_cards()

        for i, (x, y, w, h) in enumerate(cards, 1):
            # Check task state
            is_locked = self.is_task_locked(x, y, w, h)
            is_available = self.is_task_available(x, y, w, h)

            # Determine color and label
            if is_locked:
                color = (0, 165, 255)  # Orange for locked
                label = "LOCKED"
            elif is_available:
                color = (0, 255, 0)  # Green for available
                label = "AVAILABLE"
            else:
                color = (0, 0, 255)  # Red for completing
                label = "COMPLETING"

            # Scale coordinates for drawing on screenshot
            sx = int(x * self.scale_factor)
            sy = int(y * self.scale_factor)
            sw = int(w * self.scale_factor)
            sh = int(h * self.scale_factor)

            cv2.rectangle(screenshot, (sx, sy), (sx + sw, sy + sh), color, 3)

            # Draw click position only for available tasks
            if is_available and not is_locked:
                click_x, click_y = self.get_click_position(x, y, w, h)
                scx = int(click_x * self.scale_factor)
                scy = int(click_y * self.scale_factor)
                cv2.circle(screenshot, (scx, scy), 10, (255, 255, 0), -1)
                cv2.putText(screenshot, f"CLICK", (scx - 30, scy - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Label
            cv2.putText(screenshot, f"{i}: {label}", (sx, sy - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        Path("visualizeTries").mkdir(exist_ok=True)
        full_path = f"visualizeTries/{save_path}"
        cv2.imwrite(full_path, screenshot)
        print(f"\nVisualization saved: {full_path}")


def test_task_card_detector():
    """Test the task card detector."""
    print("="*60)
    print("Task Card Detector Test")
    print("="*60)

    input("\nOpen task menu, then press ENTER...")

    import time
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    detector = TaskCardDetector()

    # Find first available
    coords = detector.find_first_available_task()

    if coords:
        print(f"\n✅ SUCCESS: Found available task at {coords}")
    else:
        print(f"\n❌ FAILED: No available task found")

    # Create visualization
    detector.visualize_detection()

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    test_task_card_detector()
