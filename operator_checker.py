#!/usr/bin/env python3
"""
Operator Availability Checker
Checks if operators/trains are available before starting tasks.
"""

import cv2
import numpy as np
import pyautogui
import re
from typing import Optional, Tuple
from template_matcher import find_template_on_screen

# Try to import pytesseract for OCR
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️  pytesseract not installed - timer reading will be limited")
    print("   Install with: pip install pytesseract")


class OperatorChecker:
    """Checks operator availability and task status."""

    def __init__(self):
        self.operator_template = "Templates/OperatorsOcupied.png"
        self.completing_template = "Templates/TaskCompleting.png"
        self.en_route_template = "Templates/BottomTaskEnRoute.png"
        self.available_trains_template = "Templates/BottomTaskAvailableTrains.png"

    def find_operator_display(self) -> Optional[Tuple[int, int]]:
        """
        Find the operator occupied display on screen.

        Returns:
            (x, y) coordinates of the operator display, or None if not found
        """
        match = find_template_on_screen(self.operator_template, threshold=0.7)
        if match:
            return (match['x'], match['y'])
        return None

    def read_operator_count(self) -> Optional[Tuple[int, int]]:
        """
        Read the operator count (e.g., "2/3" means 2 occupied out of 3 total).
        Uses simple image processing to extract the numbers.

        Returns:
            (occupied, total) tuple, or None if can't read
        """
        coords = self.find_operator_display()
        if not coords:
            print("Could not find operator display")
            return None

        x, y = coords

        # Capture region around the operator display
        # Adjust width/height based on your UI
        region_width = 80
        region_height = 40
        region_x = x - region_width // 2
        region_y = y - region_height // 2

        # Ensure we don't go out of bounds
        region_x = max(0, region_x)
        region_y = max(0, region_y)

        # Capture the region
        screenshot = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Save debug image
        from pathlib import Path
        Path("visualizeTries").mkdir(exist_ok=True)
        cv2.imwrite("visualizeTries/operator_region.png", region)

        # Try to extract text using simple pattern matching
        # For now, we'll use a heuristic approach
        # You can add pytesseract OCR here if needed

        print("Operator display found, but OCR not implemented")
        print("Check visualizeTries/operator_region.png to see what was captured")

        # TODO: Implement OCR or pattern matching
        # For now, return None (manual implementation needed)
        return None

    def read_next_operator_timer(self) -> Optional[int]:
        """
        Read the timer showing when the next operator will be available.
        Looks for patterns like "5m 30s", "17m", "2h 15m", etc.

        Returns:
            Time in seconds until next operator available, or None if can't read
        """
        # Find the operator button
        from ui_config import UIConfig
        config = UIConfig()

        # Try to find operator button position
        # The button should be near the task button
        task_coords = config.get_coordinates("task_button")
        if not task_coords:
            print("⚠️  Can't find operator button position")
            return None

        # Operator button is above the task button
        operator_x = task_coords[0]
        operator_y = task_coords[1] - 60  # Adjust based on your UI

        # Capture region around operator button
        region_width = 120
        region_height = 60
        region_x = operator_x - region_width // 2
        region_y = operator_y - region_height // 2

        # Ensure we don't go out of bounds
        region_x = max(0, region_x)
        region_y = max(0, region_y)

        screenshot = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Save debug image
        from pathlib import Path
        Path("visualizeTries").mkdir(exist_ok=True)
        cv2.imwrite("visualizeTries/operator_timer.png", region)

        # Preprocess for OCR
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        # Threshold to get white text
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        if HAS_OCR:
            # Use pytesseract to read text
            text = pytesseract.image_to_string(binary, config='--psm 7')
            text = text.strip()
            print(f"OCR detected: '{text}'")

            # Parse timer patterns: "5m 30s", "17m", "2h 15m", etc.
            seconds = self._parse_timer_text(text)
            if seconds:
                return seconds

        print("⚠️  Could not read operator timer")
        print(f"   Check visualizeTries/operator_timer.png")
        return None

    def _parse_timer_text(self, text: str) -> Optional[int]:
        """
        Parse timer text like "5m 30s", "17m", "2h 15m" into seconds.

        Args:
            text: Timer text to parse

        Returns:
            Time in seconds, or None if can't parse
        """
        total_seconds = 0

        # Look for hours (e.g., "2h")
        hours_match = re.search(r'(\d+)\s*h', text, re.IGNORECASE)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        # Look for minutes (e.g., "15m")
        minutes_match = re.search(r'(\d+)\s*m', text, re.IGNORECASE)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        # Look for seconds (e.g., "30s")
        seconds_match = re.search(r'(\d+)\s*s', text, re.IGNORECASE)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        if total_seconds > 0:
            return total_seconds

        return None

    def has_available_operators(self) -> bool:
        """
        Check if there are available operators (not all occupied).

        Returns:
            True if operators are available, False if all occupied or can't determine
        """
        operator_count = self.read_operator_count()

        if operator_count is None:
            # Can't read count - for now, assume operators are available
            # You might want to change this behavior
            print("⚠️  Can't read operator count, assuming available")
            return True

        occupied, total = operator_count

        if occupied >= total:
            print(f"❌ All operators occupied ({occupied}/{total})")
            return False
        else:
            print(f"✅ Operators available ({occupied}/{total})")
            return True

    def get_available_operator_count(self) -> int:
        """
        Get the number of available (not occupied) operators.

        Returns:
            Number of available operators, or 1 if can't determine
        """
        operator_count = self.read_operator_count()

        if operator_count is None:
            # Can't read count - assume 1 operator available
            print("⚠️  Can't read operator count, assuming 1 available")
            return 1

        occupied, total = operator_count
        available = total - occupied

        print(f"Available operators: {available}/{total}")
        return available

    def is_task_completing(self, task_x: int, task_y: int) -> bool:
        """
        Check if a specific task is already in progress (showing timer).

        Args:
            task_x, task_y: Approximate coordinates of the task

        Returns:
            True if task is completing (has timer), False otherwise
        """
        # Look for the TaskCompleting icon near the task position
        # Search in a region around the task

        # Capture region around the task
        search_width = 200
        search_height = 100
        region_x = task_x - search_width // 2
        region_y = task_y - search_height // 2

        region_x = max(0, region_x)
        region_y = max(0, region_y)

        # Take screenshot of the region
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Load completing template
        completing_template = cv2.imread(self.completing_template)
        if completing_template is None:
            print(f"Warning: Could not load {self.completing_template}")
            return False

        # Get template dimensions
        template_h, template_w = completing_template.shape[:2]

        # Extract the search region from screenshot
        screen_h, screen_w = screenshot.shape[:2]
        region_x2 = min(region_x + search_width, screen_w)
        region_y2 = min(region_y + search_height, screen_h)

        search_region = screenshot[region_y:region_y2, region_x:region_x2]

        # Check if region is large enough
        if search_region.shape[0] < template_h or search_region.shape[1] < template_w:
            return False

        # Template matching
        result = cv2.matchTemplate(search_region, completing_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        threshold = 0.7
        if max_val >= threshold:
            print(f"  ⏱️  Task is already completing (timer detected)")
            return True

        return False

    def find_next_available_task(self, max_tasks: int = 5) -> Optional[Tuple[int, int]]:
        """
        Find the next task that is NOT completing.
        Uses "Available trains" vs "EN ROUTE" detection.

        Args:
            max_tasks: Maximum number of task positions to check

        Returns:
            (x, y) coordinates of next available task, or None
        """
        # Get the Task button position as reference
        task_button_match = find_template_on_screen("Templates/task.png", threshold=0.7)

        if not task_button_match:
            print("Could not find Task button reference")
            return None

        task_button_x = task_button_match['x']
        task_button_y = task_button_match['y']

        print("\n=== Scanning for Available Tasks ===")

        # Find all "EN ROUTE" markers (completing tasks)
        en_route_matches = find_all_matches(self.en_route_template, threshold=0.8)

        # Find all "Available trains" markers (available tasks)
        available_matches = find_all_matches(self.available_trains_template, threshold=0.75)

        print(f"Found {len(en_route_matches)} EN ROUTE task(s)")
        print(f"Found {len(available_matches)} Available task(s)")

        if not available_matches:
            print("❌ No available tasks found")
            return None

        # Get the leftmost available task (first one)
        leftmost_available = min(available_matches, key=lambda m: m['x'])

        available_x = leftmost_available['x']
        available_y = leftmost_available['y']

        # The task click position is above the "Available trains" text
        # Estimate: same X, but Y is about 300px higher (middle of task card)
        task_x = available_x
        task_y = available_y - 300

        print(f"✅ Found available task!")
        print(f"   'Available trains' at ({available_x}, {available_y})")
        print(f"   Estimated task position: ({task_x}, {task_y})")

        return (task_x, task_y)


def test_operator_checker():
    """Test the operator checker."""
    print("="*60)
    print("Operator Checker Test")
    print("="*60)

    checker = OperatorChecker()

    print("\n1. Make sure the operator display is visible")
    input("Press ENTER when ready...")

    import time
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Test finding operator display
    coords = checker.find_operator_display()
    if coords:
        print(f"✅ Found operator display at {coords}")
    else:
        print("❌ Could not find operator display")

    # Test checking availability
    print("\n" + "="*60)
    available = checker.has_available_operators()
    print(f"Operators available: {available}")

    print("\n" + "="*60)
    print("Test complete!")


if __name__ == "__main__":
    test_operator_checker()
