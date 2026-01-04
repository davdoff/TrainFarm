#!/usr/bin/env python3
"""
Coordinate Diagnosis Tool
Checks if coordinates are being calculated correctly.
"""

import time
import pyautogui
import cv2
import numpy as np
from template_matcher import find_template_on_screen
from pathlib import Path


def get_screen_info():
    """Get screen resolution and mouse info."""
    print("="*60)
    print("Screen Information")
    print("="*60)

    # Get screen size
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size: {screen_width} x {screen_height}")

    # Get current mouse position
    mouse_x, mouse_y = pyautogui.position()
    print(f"Current mouse position: ({mouse_x}, {mouse_y})")

    # Take a screenshot and check its size
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_height, screenshot_width = screenshot_np.shape[:2]
    print(f"Screenshot size: {screenshot_width} x {screenshot_height}")

    # Check if they match
    if screen_width != screenshot_width or screen_height != screenshot_height:
        print("\n⚠️  WARNING: Screen size != Screenshot size!")
        print("   This means you have display scaling enabled.")
        print(f"   Scale factor: {screenshot_width/screen_width:.2f}x")
        return screenshot_width / screen_width
    else:
        print("\n✅ Screen size matches screenshot size (no scaling)")
        return 1.0


def test_manual_click_coordinates():
    """Test clicking at a manually specified location."""
    print("\n" + "="*60)
    print("Manual Coordinate Test")
    print("="*60)
    print("\nThis will show you where PyAutoGUI thinks it's clicking.")
    print("We'll move the mouse WITHOUT clicking so you can see.")

    input("\nPress ENTER to continue...")

    # Test a few coordinates
    test_coords = [
        (100, 100, "Top-left area"),
        (500, 300, "Middle-left area"),
        (pyautogui.size()[0]//2, pyautogui.size()[1]//2, "Center of screen"),
    ]

    for x, y, description in test_coords:
        print(f"\nMoving mouse to ({x}, {y}) - {description}")
        print("Watch where your mouse goes...")
        time.sleep(2)

        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(1)

        actual_x, actual_y = pyautogui.position()
        print(f"Mouse should be at: ({x}, {y})")
        print(f"Mouse actually at:  ({actual_x}, {actual_y})")

        if abs(actual_x - x) > 5 or abs(actual_y - y) > 5:
            print("⚠️  Coordinates don't match!")


def test_template_matching_coordinates():
    """Test coordinates from template matching."""
    print("\n" + "="*60)
    print("Template Matching Coordinate Test")
    print("="*60)
    print("\nMake sure Task button is visible on screen.")

    input("Press ENTER to start...")

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    template_path = "Templates/task.png"

    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        return

    print(f"\nSearching for Task button...")
    match = find_template_on_screen(template_path, threshold=0.7)

    if match:
        print(f"✅ Found at ({match['x']}, {match['y']})")
        print(f"   Top-left: {match['top_left']}")
        print(f"   Bottom-right: {match['bottom_right']}")
        print(f"   Size: {match['width']}x{match['height']}")

        # Show where we're going to move the mouse
        print(f"\nWe will now move the mouse to ({match['x']}, {match['y']})")
        print("WITHOUT clicking, so you can see where it goes.")
        print("The mouse should move to the CENTER of the Task button.")

        input("\nPress ENTER to move mouse...")

        print("Moving mouse in 2 seconds...")
        time.sleep(2)

        pyautogui.moveTo(match['x'], match['y'], duration=0.5)

        print("\n❓ Questions:")
        print("   1. Did the mouse move to the Task button?")
        print("   2. Is it in the center of the button?")
        print("   3. Or is it somewhere else entirely?")

        # Create a visual debug image
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Draw crosshair at the matched coordinates
        cv2.line(screenshot, (match['x']-20, match['y']), (match['x']+20, match['y']), (0, 255, 0), 2)
        cv2.line(screenshot, (match['x'], match['y']-20), (match['x'], match['y']+20), (0, 255, 0), 2)

        # Draw rectangle around found area
        cv2.rectangle(screenshot, match['top_left'], match['bottom_right'], (0, 0, 255), 3)

        # Save debug image
        Path("visualizeTries").mkdir(exist_ok=True)
        cv2.imwrite("visualizeTries/coordinate_debug.png", screenshot)

        print("\n📸 Debug image saved: visualizeTries/coordinate_debug.png")
        print("   - Green crosshair = where we're trying to click")
        print("   - Red rectangle = where we found the button")

    else:
        print("❌ Task button not found")


def main():
    print("\n" + "="*60)
    print("Coordinate Diagnosis Tool")
    print("="*60)
    print("\nThis tool will help figure out why clicks are in the wrong place.\n")

    # Get screen info
    scale_factor = get_screen_info()

    if scale_factor != 1.0:
        print("\n" + "="*60)
        print("⚠️  SCALING DETECTED!")
        print("="*60)
        print(f"\nYour display is scaled by {scale_factor:.2f}x")
        print("\nThis is common on:")
        print("  - Retina displays (Macs)")
        print("  - High-DPI monitors")
        print("  - Windows with display scaling enabled")
        print("\nThis might be causing coordinate issues.")

    # Test manual coordinates
    if input("\nTest manual mouse movements? (y/n): ").lower() == 'y':
        test_manual_click_coordinates()

    # Test template matching coordinates
    if input("\nTest template matching coordinates? (y/n): ").lower() == 'y':
        test_template_matching_coordinates()

    print("\n" + "="*60)
    print("Diagnosis Complete")
    print("="*60)
    print("\nBased on the results:")
    print("  - If mouse moves to wrong places → Display scaling issue")
    print("  - If mouse goes to bottom of screen → Coordinate calculation problem")
    print("  - Check visualizeTries/coordinate_debug.png to see what was found")
    print("="*60)


if __name__ == "__main__":
    main()
