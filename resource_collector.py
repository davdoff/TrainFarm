#!/usr/bin/env python3
"""
Resource Collection Module
Detects when operators have resources ready and collects them.
"""

import cv2
import numpy as np
import pyautogui
import time
from typing import Optional, Tuple
from template_matcher import find_template_on_screen, find_all_matches


class ResourceCollector:
    """Handles resource collection from operators."""

    def __init__(self):
        self.operator_template = "Templates/OperatorsOcupied.png"
        self.operator_yellow_template = "Templates/CanCollectOperatorButton.png"
        self.collect_button_operator_template = "Templates/CollectButtonOperator.png"
        self.collect_button_task_template = "Templates/CollectButtonTask.png"

    def is_operator_button_yellow(self) -> bool:
        """
        Check if the operator button is yellow (has resources ready).
        Uses template matching instead of color detection.

        Returns:
            True if yellow button found, False otherwise
        """
        # Try to find the yellow operator button template
        match = find_template_on_screen(self.operator_yellow_template, threshold=0.7)

        if match:
            print(f"  🟡 Operator button is YELLOW (resources ready!)")
            print(f"     Found at ({match['x']}, {match['y']}) with {match['confidence']:.2%} confidence")
            return True
        else:
            print(f"  🔵 Operator button is BLUE/normal (no resources)")
            return False

    def find_operator_button(self, yellow_only: bool = False) -> Optional[Tuple[int, int]]:
        """
        Find the operator button on screen.

        Args:
            yellow_only: If True, only find yellow (ready) button

        Returns:
            (x, y) coordinates of operator button, or None if not found
        """
        if yellow_only:
            # Look for yellow button only
            match = find_template_on_screen(self.operator_yellow_template, threshold=0.7)
            if match:
                print(f"Found YELLOW operator button at ({match['x']}, {match['y']})")
                return (match['x'], match['y'])
        else:
            # Try yellow first, then blue
            match = find_template_on_screen(self.operator_yellow_template, threshold=0.7)
            if match:
                print(f"Found YELLOW operator button at ({match['x']}, {match['y']})")
                return (match['x'], match['y'])

            match = find_template_on_screen(self.operator_template, threshold=0.7)
            if match:
                print(f"Found BLUE operator button at ({match['x']}, {match['y']})")
                return (match['x'], match['y'])

        print("Could not find operator button")
        return None

    def check_and_collect_resources(self) -> bool:
        """
        Check if operator button is yellow and collect resources if needed.

        Returns:
            True if resources were collected, False otherwise
        """
        print("\n=== Checking for Resources to Collect ===")

        # Check if yellow button exists (resources ready)
        if not self.is_operator_button_yellow():
            print("No resources ready to collect")
            return False

        print("🟡 Resources are ready! Collecting...")

        # Find the yellow operator button
        operator_coords = self.find_operator_button(yellow_only=True)
        if not operator_coords:
            print("Error: Yellow button detected but can't find coordinates")
            return False

        x, y = operator_coords

        # Click operator button to open collection dialog
        print("Clicking yellow operator button...")
        pyautogui.click(x, y)
        time.sleep(1.5)  # Wait for dialog to open

        # Click collect buttons until there are no more
        collected_count = 0
        max_attempts = 10  # Safety limit

        for attempt in range(max_attempts):
            print(f"Looking for Collect button (attempt {attempt + 1}/{max_attempts})...")

            # Try to find a collect button
            collect_button = self.find_collect_button()

            if collect_button:
                collect_x, collect_y = collect_button
                print(f"  Found Collect button at ({collect_x}, {collect_y})")
                print(f"  Clicking...")

                pyautogui.click(collect_x, collect_y)
                collected_count += 1
                time.sleep(0.5)  # Wait a bit between collections
            else:
                print("  No more Collect buttons found")
                break

        if collected_count > 0:
            print(f"✅ Collected {collected_count} resource(s)")

            # Close the dialog (press ESC or click X)
            print("Closing collection dialog...")
            pyautogui.press('esc')
            time.sleep(0.5)

            return True
        else:
            print("⚠️  No Collect buttons found (might need template)")
            pyautogui.press('esc')  # Close dialog anyway
            return False

    def find_collect_button(self, context: str = "operator") -> Optional[Tuple[int, int]]:
        """
        Find a Collect button on screen using template matching.

        Args:
            context: Either "operator" (from operator dialog) or "task" (from task trains view)

        Returns:
            (x, y) coordinates of Collect button, or None if not found
        """
        # Choose the correct template based on context
        if context == "task":
            template = self.collect_button_task_template
            context_name = "task"
        else:
            template = self.collect_button_operator_template
            context_name = "operator"

        # Try with lower threshold for better detection
        match = find_template_on_screen(template, threshold=0.6)
        if match:
            print(f"Found Collect button ({context_name}) at ({match['x']}, {match['y']}) with {match['confidence']:.2%} confidence")
            return (match['x'], match['y'])

        print(f"No Collect button ({context_name}) found (tried threshold 0.6)")
        return None

    def visualize_operator_color(self, save_path: str = "operator_color_debug.png"):
        """
        Create a visualization showing the operator button color detection.
        Useful for debugging yellow detection.
        """
        operator_coords = self.find_operator_button()
        if not operator_coords:
            print("Cannot visualize - operator button not found")
            return

        x, y = operator_coords

        # Take full screenshot
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Draw rectangle around operator button
        width, height = 100, 50
        top_left = (x - width // 2, y - height // 2)
        bottom_right = (x + width // 2, y + height // 2)

        # Color depends on whether it's yellow
        is_yellow = self.is_operator_button_yellow(x, y)
        color = (0, 255, 255) if is_yellow else (255, 0, 0)  # Yellow if yellow, Blue if not

        cv2.rectangle(screenshot, top_left, bottom_right, color, 3)

        # Add text
        text = "YELLOW - COLLECT!" if is_yellow else "BLUE - Normal"
        cv2.putText(screenshot, text, (x - 50, y - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Save
        from pathlib import Path
        Path("visualizeTries").mkdir(exist_ok=True)
        save_path = f"visualizeTries/{save_path}"
        cv2.imwrite(save_path, screenshot)
        print(f"Visualization saved: {save_path}")


def test_resource_collector():
    """Test the resource collector."""
    print("="*60)
    print("Resource Collector Test")
    print("="*60)

    collector = ResourceCollector()

    print("\nMake sure the game is visible")
    input("Press ENTER when ready...")

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Test finding operator button
    coords = collector.find_operator_button()

    if coords:
        print(f"\n✅ Found operator button at {coords}")

        # Check if yellow
        is_yellow = collector.is_operator_button_yellow()

        if is_yellow:
            print("\n🟡 Button is YELLOW - resources ready!")
            print("\nWould you like to test collection? (y/n)")
            if input().lower() == 'y':
                collector.check_and_collect_resources()
        else:
            print("\n🔵 Button is BLUE - no resources ready")

    else:
        print("\n❌ Could not find operator button")

    print("\n" + "="*60)
    print("Test complete!")


if __name__ == "__main__":
    test_resource_collector()
