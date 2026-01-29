#!/usr/bin/env python3
"""
Diagnostic tool to test if template matching is working correctly.
This will help identify if the issue is with the algorithm, scale factor, or templates.
"""

import cv2
import numpy as np
import pyautogui
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detectors.template_matcher import (
    find_template_on_screen,
    get_scale_factor,
    find_all_matches
)


def test_self_matching():
    """
    Test 1: Take a screenshot, crop a piece, and try to match it back.
    This should ALWAYS work if the algorithm is correct.
    """
    import time

    print("="*60)
    print("TEST 1: Self-Matching Test")
    print("="*60)
    print("Taking a screenshot in 3 seconds...")
    print("Switch to your game window now!\n")

    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    print("Capturing screenshot...\n")

    # Take full screenshot
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()
    scale_factor = get_scale_factor()

    print(f"Screen size (logical): {screen_width}x{screen_height}")
    print(f"Screenshot size (physical): {screenshot_bgr.shape[1]}x{screenshot_bgr.shape[0]}")
    print(f"Scale factor: {scale_factor}")

    # Crop a piece from center of screen (in screenshot coordinates)
    center_x = screenshot_bgr.shape[1] // 2
    center_y = screenshot_bgr.shape[0] // 2
    crop_size = 100

    template_crop = screenshot_bgr[
        center_y - crop_size:center_y + crop_size,
        center_x - crop_size:center_x + crop_size
    ]

    # Save the cropped piece as a template
    template_path = "test_template_self.png"
    cv2.imwrite(template_path, template_crop)
    print(f"\n✓ Saved test template: {template_path}")
    print(f"  Template size: {template_crop.shape[1]}x{template_crop.shape[0]}")

    # Now try to find it using the SAME screenshot (not a new one)
    print("\nAttempting to match template...")

    # Load the template we just saved
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    # Perform template matching on the SAME screenshot
    result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if match confidence is above threshold
    threshold = 0.95
    if max_val >= threshold:
        # Calculate coordinates
        template_height, template_width = template.shape[:2]
        top_left = max_loc
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        center_x = top_left[0] + template_width // 2
        center_y = top_left[1] + template_height // 2

        # Convert to PyAutoGUI coordinate space
        match = {
            'x': int(center_x / scale_factor),
            'y': int(center_y / scale_factor),
            'confidence': max_val
        }
    else:
        match = None

    if match:
        print("\n✓✓✓ SUCCESS! Algorithm is working correctly!")
        print(f"  Found at: ({match['x']}, {match['y']})")
        print(f"  Confidence: {match['confidence']:.4f}")
        print(f"  Expected center: ({screen_width//2}, {screen_height//2})")

        # Check if position is close to expected
        expected_x = screen_width // 2
        expected_y = screen_height // 2
        error_x = abs(match['x'] - expected_x)
        error_y = abs(match['y'] - expected_y)

        if error_x < 5 and error_y < 5:
            print("  ✓ Position matches expected location!")
        else:
            print(f"  ⚠ Position error: {error_x}px horizontal, {error_y}px vertical")
    else:
        print("\n✗✗✗ FAILURE! Self-matching failed - algorithm has issues!")
        print("This indicates a problem with:")
        print("  - Scale factor calculation")
        print("  - Screenshot/template format mismatch")
        print("  - OpenCV template matching implementation")

    return match is not None


def test_existing_template(template_path):
    """
    Test 2: Try to match an existing template with detailed diagnostics.
    """
    print("\n" + "="*60)
    print("TEST 2: Existing Template Matching")
    print("="*60)
    print(f"Template: {template_path}\n")

    if not Path(template_path).exists():
        print(f"✗ Template file not found: {template_path}")
        return False

    # Load template
    template = cv2.imread(template_path)
    if template is None:
        print(f"✗ Failed to load template")
        return False

    print(f"Template loaded:")
    print(f"  Size: {template.shape[1]}x{template.shape[0]}")
    print(f"  Channels: {template.shape[2]}")
    print(f"  Data type: {template.dtype}")

    # Take screenshot
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    print(f"\nScreenshot captured:")
    print(f"  Size: {screenshot_bgr.shape[1]}x{screenshot_bgr.shape[0]}")
    print(f"  Channels: {screenshot_bgr.shape[2]}")
    print(f"  Data type: {screenshot_bgr.dtype}")

    # Perform template matching with different thresholds
    print("\nTrying different thresholds...")

    thresholds = [0.95, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

    for threshold in thresholds:
        match = find_template_on_screen(template_path, threshold=threshold)

        if match:
            print(f"  ✓ Match found at threshold {threshold}")
            print(f"    Position: ({match['x']}, {match['y']})")
            print(f"    Confidence: {match['confidence']:.4f}")

            # Visualize
            vis_screenshot = screenshot_bgr.copy()
            scale_factor = get_scale_factor()
            x1 = int(match['top_left'][0] * scale_factor)
            y1 = int(match['top_left'][1] * scale_factor)
            x2 = int(match['bottom_right'][0] * scale_factor)
            y2 = int(match['bottom_right'][1] * scale_factor)

            cv2.rectangle(vis_screenshot, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.imwrite("diagnostic_match_visualization.png", vis_screenshot)
            print(f"    Saved visualization: diagnostic_match_visualization.png")

            return True
        else:
            # Get the actual max confidence even if below threshold
            result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            print(f"  ✗ No match at threshold {threshold} (max confidence: {max_val:.4f})")

    print("\n✗ No match found at any threshold")
    print(f"Best confidence score was: {max_val:.4f}")

    if max_val < 0.3:
        print("\n⚠ Very low confidence suggests:")
        print("  - Template was captured from different resolution")
        print("  - Template doesn't exist on current screen")
        print("  - Template has different scaling/DPI")

    return False


def test_scale_factor_calculation():
    """
    Test 3: Verify scale factor is calculated correctly.
    """
    print("\n" + "="*60)
    print("TEST 3: Scale Factor Verification")
    print("="*60)

    # Get PyAutoGUI screen size
    screen_width, screen_height = pyautogui.size()

    # Get screenshot size
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    ss_height, ss_width = screenshot_np.shape[:2]

    # Calculate scale factor
    scale_factor = get_scale_factor()

    print(f"Logical screen size: {screen_width}x{screen_height}")
    print(f"Physical screenshot size: {ss_width}x{ss_height}")
    print(f"Calculated scale factor: {scale_factor}")
    print(f"Expected scale factor: {ss_width / screen_width}")

    # Check if they match
    expected_scale = ss_width / screen_width
    if abs(scale_factor - expected_scale) < 0.01:
        print("\n✓ Scale factor calculation is correct")
        return True
    else:
        print("\n✗ Scale factor calculation mismatch!")
        print("This could cause coordinate conversion errors")
        return False


def test_template_formats():
    """
    Test 4: Check if template has transparency or format issues.
    """
    print("\n" + "="*60)
    print("TEST 4: Template Format Check")
    print("="*60)

    # Check all Freebie templates
    template_dir = Path("Templates/ui")
    freebie_templates = list(template_dir.glob("*[Ff]reebie*.png"))

    for template_path in freebie_templates:
        print(f"\nChecking: {template_path.name}")

        # Load with imread
        img = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)

        if img is None:
            print(f"  ✗ Failed to load")
            continue

        print(f"  Size: {img.shape[1]}x{img.shape[0]}")
        print(f"  Channels: {img.shape[2] if len(img.shape) == 3 else 1}")

        # Check for alpha channel
        if len(img.shape) == 3 and img.shape[2] == 4:
            print(f"  ⚠ Has alpha channel (transparency)")
            print(f"    Template matching expects 3 channels (BGR)")
            print(f"    Alpha channel might cause issues")

            # Check if alpha is fully opaque
            alpha = img[:, :, 3]
            if np.all(alpha == 255):
                print(f"    ✓ Alpha is fully opaque (should be okay)")
            else:
                print(f"    ⚠ Has transparent pixels")
                print(f"      Min alpha: {alpha.min()}, Max alpha: {alpha.max()}")


def main():
    """Run all diagnostic tests."""
    print("Template Matching Diagnostic Tool")
    print("="*60)
    print()

    # Test 1: Self-matching
    test1_passed = test_self_matching()

    # Test 3: Scale factor
    test3_passed = test_scale_factor_calculation()

    # Test 4: Template formats
    test_template_formats()

    # Test 2: Existing template (if self-matching worked)
    if test1_passed:
        print("\n" + "="*60)
        print("Self-matching test passed! Now testing your templates...")
        print("="*60)

        template_dir = Path("Templates/ui")
        freebie_templates = list(template_dir.glob("*[Ff]reebie*.png"))

        if freebie_templates:
            print(f"\nFound {len(freebie_templates)} Freebie template(s)")
            print("Switch to your game window to test matching...")

            import time
            time.sleep(3)

            for template in freebie_templates:
                test_existing_template(str(template))
        else:
            print("\n⚠ No Freebie templates found to test")
    else:
        print("\n" + "="*60)
        print("⚠ Self-matching test FAILED!")
        print("There is a fundamental issue with the template matching algorithm.")
        print("Check the scale factor calculation and coordinate conversion.")
        print("="*60)

    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    print(f"Self-matching test: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"Scale factor test: {'✓ PASS' if test3_passed else '✗ FAIL'}")

    if not test1_passed:
        print("\n⚠ CRITICAL: Basic algorithm is not working!")
        print("Fix the template_matcher.py implementation first.")
    elif test3_passed:
        print("\n✓ Algorithm is working correctly!")
        print("The issue is likely with your template images:")
        print("  - Template doesn't match what's currently on screen")
        print("  - Template was captured at different resolution/DPI")
        print("  - Template needs to be recaptured from current game state")


if __name__ == "__main__":
    main()
