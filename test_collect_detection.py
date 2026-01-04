#!/usr/bin/env python3
"""
Test Collect Button Detection
Helps debug why collect buttons aren't being found.
"""

import time
import cv2
import numpy as np
import pyautogui
from template_matcher import find_template_on_screen, find_all_matches
from pathlib import Path

def test_collect_button_detection():
    """Test finding collect buttons with different thresholds."""
    print("="*60)
    print("Collect Button Detection Test")
    print("="*60)

    print("\nMake sure collect buttons are visible on screen")
    print("(Click a task to show trains/collect buttons)")
    input("Press ENTER when ready...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Test both templates
    templates = {
        "Task Context": "Templates/CollectButtonTask.png",
        "Operator Context": "Templates/CollectButtonOperator.png"
    }

    # Test with different thresholds
    thresholds = [0.9, 0.8, 0.7, 0.6, 0.5]

    for template_name, template_path in templates.items():
        print(f"\n=== Testing {template_name} Template ===")
        print(f"Template: {template_path}")

            for threshold in thresholds:
                print(f"  Threshold {threshold}:")
                matches = find_all_matches(template_path, threshold=threshold)
                if matches:
                    print(f"    ✓ Found {len(matches)} match(es)")
                    for i, match in enumerate(matches[:3]):  # Show first 3
                        print(f"      {i+1}. ({match['x']}, {match['y']}) - {match['confidence']:.2%} confidence")
                else:
                    print(f"    ✗ No matches found")

    # Take a screenshot for manual inspection
    print("\n=== Saving Screenshot with Visualizations ===")
    screenshot = pyautogui.screenshot()
    screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Test both templates and visualize
    Path("visualizeTries").mkdir(exist_ok=True)

    for template_name, template_path in templates.items():
        print(f"\nTesting {template_name}:")
        template = cv2.imread(template_path)
        if template is not None:
            template_h, template_w = template.shape[:2]
            print(f"  Template size: {template_w}x{template_h}")

            # Try matching and visualize
            result = cv2.matchTemplate(screenshot_np, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            print(f"  Best match confidence: {max_val:.2%}")
            print(f"  Best match location: {max_loc}")

            if max_val >= 0.5:
                # Draw rectangle at best match
                top_left = max_loc
                bottom_right = (top_left[0] + template_w, top_left[1] + template_h)
                # Use different colors for different templates
                color = (0, 255, 0) if "Task" in template_name else (255, 0, 255)
                cv2.rectangle(screenshot_np, top_left, bottom_right, color, 3)
                cv2.putText(screenshot_np, f"{template_name}: {max_val:.2%}",
                           (top_left[0], top_left[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Save visualization
    save_path = "visualizeTries/collect_button_debug.png"
    cv2.imwrite(save_path, screenshot_np)
    print(f"\nVisualization saved: {save_path}")
    print("Check this image to see if the templates match")
    print("Green = Task Context, Magenta = Operator Context")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_collect_button_detection()
