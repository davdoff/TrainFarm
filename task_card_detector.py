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


class TaskCardDetector:
    """Detects and analyzes task cards."""

    def __init__(self):
        self.green_checkmark_template = None  # You can add this if you want
        self.screen_width, self.screen_height = pyautogui.size()

        # Get scale factor for Retina displays
        self.scale_factor = self._get_scale_factor()
        print(f"Display scale factor: {self.scale_factor}")

    def _get_scale_factor(self):
        """Calculate scale factor for Retina/HiDPI displays."""
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_height, screenshot_width = screenshot_np.shape[:2]

        scale_x = screenshot_width / self.screen_width
        scale_y = screenshot_height / self.screen_height

        return (scale_x + scale_y) / 2

    def find_task_cards(self) -> List[Tuple[int, int, int, int]]:
        """
        Find all task card regions on screen using fixed grid positions.

        Returns:
            List of (x, y, width, height) for each task card found
        """
        cards = []

        # Task cards appear in a horizontal row
        # Import settings from centralized config file
        from detection_config import (CARD_WIDTH, CARD_HEIGHT, CARD_START_X,
                                      CARD_START_Y, CARD_SPACING)

        card_width = CARD_WIDTH
        card_height = CARD_HEIGHT
        start_x = CARD_START_X
        start_y = CARD_START_Y
        spacing = CARD_SPACING

        # Check for up to 5 task positions
        for i in range(5):
            x = start_x + (i * spacing)
            y = start_y

            # Make sure we're not going off screen
            if x + card_width > self.screen_width:
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

    def is_task_available(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Determine if a task card is available (not completing).

        Args:
            x, y, width, height: Task card region

        Returns:
            True if task is available, False if completing
        """
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

    def find_first_available_task(self) -> Optional[Tuple[int, int]]:
        """
        Find the first available task card and return click coordinates.

        Returns:
            (x, y) coordinates to click, or None if no available task
        """
        print("\n=== Detecting Task Cards ===")

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
                print(f"  ⏱️  Card {i} is COMPLETING")

        print("\n❌ No available tasks found")
        return None

    def visualize_detection(self, save_path: str = "task_cards_debug.png"):
        """
        Create visualization showing detected task cards.
        """
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        cards = self.find_task_cards()

        for i, (x, y, w, h) in enumerate(cards, 1):
            # Draw rectangle around card
            is_available = self.is_task_available(x, y, w, h)
            color = (0, 255, 0) if is_available else (0, 0, 255)  # Green if available, Red if completing

            # Scale coordinates for drawing on screenshot
            sx = int(x * self.scale_factor)
            sy = int(y * self.scale_factor)
            sw = int(w * self.scale_factor)
            sh = int(h * self.scale_factor)

            cv2.rectangle(screenshot, (sx, sy), (sx + sw, sy + sh), color, 3)

            # Draw click position
            if is_available:
                click_x, click_y = self.get_click_position(x, y, w, h)
                scx = int(click_x * self.scale_factor)
                scy = int(click_y * self.scale_factor)
                cv2.circle(screenshot, (scx, scy), 10, (255, 255, 0), -1)
                cv2.putText(screenshot, f"CLICK", (scx - 30, scy - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Label
            label = "AVAILABLE" if is_available else "COMPLETING"
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
