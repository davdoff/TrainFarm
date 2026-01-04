#!/usr/bin/env python3
"""
Operator Count Detection Test
Detects the operator button and reads the operator count (x/y format).
"""

import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️ pytesseract not installed - operator count will not be read")


def find_template(template_path, screenshot, threshold=0.8):
    """Find template in screenshot using template matching."""
    template = cv2.imread(template_path)
    if template is None:
        return None

    # Get template dimensions
    th, tw = template.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        # Return center point
        center_x = max_loc[0] + tw // 2
        center_y = max_loc[1] + th // 2
        return {
            'x': center_x,
            'y': center_y,
            'confidence': max_val,
            'top_left': max_loc,
            'width': tw,
            'height': th
        }

    return None


def _ocr_operator_count(roi):
    """Use OCR to read operator count text (x/y format)."""
    if not HAS_OCR:
        return None

    try:
        # Upscale the ROI for better OCR
        scale = 3
        height, width = roi.shape[:2]

        if width < 5 or height < 5:
            return None

        enlarged = cv2.resize(roi, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC)

        # Convert to grayscale
        gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

        # Try multiple thresholding methods
        results = []

        # Method 1: OTSU
        _, binary1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        text1 = pytesseract.image_to_string(binary1, config='--psm 7 -c tessedit_char_whitelist=0123456789/')
        text1_clean = text1.strip()
        if '/' in text1_clean:
            results.append(text1_clean)

        # Method 2: Adaptive threshold
        binary2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        text2 = pytesseract.image_to_string(binary2, config='--psm 7 -c tessedit_char_whitelist=0123456789/')
        text2_clean = text2.strip()
        if '/' in text2_clean:
            results.append(text2_clean)

        # Method 3: Simple threshold
        _, binary3 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        text3 = pytesseract.image_to_string(binary3, config='--psm 7 -c tessedit_char_whitelist=0123456789/')
        text3_clean = text3.strip()
        if '/' in text3_clean:
            results.append(text3_clean)

        # Save debug images
        Path("visualizeTries/operator_ocr_debug").mkdir(parents=True, exist_ok=True)
        cv2.imwrite("visualizeTries/operator_ocr_debug/roi_original.png", enlarged)
        cv2.imwrite("visualizeTries/operator_ocr_debug/roi_otsu.png", binary1)
        cv2.imwrite("visualizeTries/operator_ocr_debug/roi_adaptive.png", binary2)
        cv2.imwrite("visualizeTries/operator_ocr_debug/roi_simple.png", binary3)

        # Return most common result
        if results:
            result = max(set(results), key=results.count)
            print(f"    OCR results: {results}, using: {result}")

            # Parse x/y
            try:
                parts = result.split('/')
                if len(parts) == 2:
                    in_use = int(''.join(filter(str.isdigit, parts[0])))
                    total = int(''.join(filter(str.isdigit, parts[1])))
                    return {'in_use': in_use, 'total': total, 'raw': result}
            except:
                pass

        print(f"    OCR failed to parse operator count")
        return None
    except Exception as e:
        print(f"    OCR error: {e}")
        return None


def test_operator_detection():
    """Test operator button detection and operator count reading."""
    print("="*60)
    print("Operator Count Detection Test")
    print("="*60)
    print("\nThis will help you:")
    print("1. Detect the operator button location")
    print("2. Calibrate the operator count text detection zone")
    print("\nMake sure the game is visible on screen.")

    input("\nPress ENTER to detect operator button (before clicking it)...")

    print("\nCountdown:")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Step 1: Detect operator button (before clicking)
    print("\n=== Step 1: Detecting Operator Button ===")
    screenshot = pyautogui.screenshot()
    screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    operator_icon = find_template("Templates/OperatorIcon.png", screenshot_np, threshold=0.7)

    if not operator_icon:
        print("❌ Operator button not found!")
        print("   Make sure Templates/OperatorIcon.png matches the operator button on screen")
        return

    print(f"✓ Found operator button at ({operator_icon['x']}, {operator_icon['y']})")
    print(f"  Confidence: {operator_icon['confidence']:.2f}")

    # Get scale factor for display
    from template_matcher import get_scale_factor
    scale_factor = get_scale_factor()

    # Draw detection on screenshot
    sx = int(operator_icon['x'] * scale_factor)
    sy = int(operator_icon['y'] * scale_factor)
    sw = int(operator_icon['width'] * scale_factor)
    sh = int(operator_icon['height'] * scale_factor)
    top_left_x = int(operator_icon['top_left'][0] * scale_factor)
    top_left_y = int(operator_icon['top_left'][1] * scale_factor)

    # Draw operator icon box
    cv2.rectangle(screenshot_np, (top_left_x, top_left_y),
                 (top_left_x + sw, top_left_y + sh), (0, 255, 0), 2)
    cv2.circle(screenshot_np, (sx, sy), 5, (0, 255, 0), -1)
    cv2.putText(screenshot_np, "Operator Button", (sx + 10, sy - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save visualization
    Path("visualizeTries").mkdir(exist_ok=True)
    cv2.imwrite("visualizeTries/operator_button_detection.png", screenshot_np)
    print(f"\n💾 Visualization saved: visualizeTries/operator_button_detection.png")

    # Click the operator button
    print(f"\n=== Clicking Operator Button ===")
    pyautogui.click(operator_icon['x'], operator_icon['y'])
    print(f"✓ Clicked operator button at ({operator_icon['x']}, {operator_icon['y']})")

    print("\nWaiting for operator panel to open...")
    time.sleep(2)  # Wait for panel to open

    # Step 2: Detect operator icon after clicking (to find text next to it)
    print("\n=== Step 2: Detecting Operator Count Text ===")
    screenshot2 = pyautogui.screenshot()
    screenshot2_np = cv2.cvtColor(np.array(screenshot2), cv2.COLOR_RGB2BGR)

    operator_icon_clicked = find_template("Templates/OperatorIconAfterClickingOperatroButton.png",
                                         screenshot2_np, threshold=0.7)

    if not operator_icon_clicked:
        print("❌ Operator icon not found after clicking!")
        print("   Make sure Templates/OperatorIconAfterClickingOperatroButton.png matches the icon in the panel")
        return

    print(f"✓ Found operator icon in panel at ({operator_icon_clicked['x']}, {operator_icon_clicked['y']})")
    print(f"  Confidence: {operator_icon_clicked['confidence']:.2f}")

    # Import detection zone settings
    from detection_config import (OPERATOR_COUNT_OFFSET_X, OPERATOR_COUNT_ZONE_WIDTH,
                                  OPERATOR_COUNT_OFFSET_Y, OPERATOR_COUNT_ZONE_HEIGHT)

    # Get screen size
    screen_width, screen_height = pyautogui.size()

    # Calculate text detection zone (to the right of the icon)
    zone_left = operator_icon_clicked['x'] + int(screen_width * OPERATOR_COUNT_OFFSET_X)
    zone_top = operator_icon_clicked['y'] - int(screen_height * OPERATOR_COUNT_ZONE_HEIGHT / 2) + int(screen_height * OPERATOR_COUNT_OFFSET_Y)
    zone_width = int(screen_width * OPERATOR_COUNT_ZONE_WIDTH)
    zone_height = int(screen_height * OPERATOR_COUNT_ZONE_HEIGHT)

    print(f"\nText detection zone:")
    print(f"  Left: {zone_left}, Top: {zone_top}")
    print(f"  Width: {zone_width}, Height: {zone_height}")

    # Extract ROI for text
    roi = screenshot2_np[zone_top:zone_top+zone_height, zone_left:zone_left+zone_width]

    # Try to read operator count
    operator_count = _ocr_operator_count(roi)

    if operator_count:
        print(f"\n✓ Operator count detected: {operator_count['in_use']}/{operator_count['total']}")
        print(f"  In use: {operator_count['in_use']}")
        print(f"  Total: {operator_count['total']}")
        print(f"  Available: {operator_count['total'] - operator_count['in_use']}")
    else:
        print(f"\n❌ Failed to read operator count text")
        print(f"  Check visualizeTries/operator_ocr_debug/ for debug images")

    # Draw visualization for clicked state
    sx2 = int(operator_icon_clicked['x'] * scale_factor)
    sy2 = int(operator_icon_clicked['y'] * scale_factor)
    sw2 = int(operator_icon_clicked['width'] * scale_factor)
    sh2 = int(operator_icon_clicked['height'] * scale_factor)
    top_left_x2 = int(operator_icon_clicked['top_left'][0] * scale_factor)
    top_left_y2 = int(operator_icon_clicked['top_left'][1] * scale_factor)

    # Draw operator icon box (green)
    cv2.rectangle(screenshot2_np, (top_left_x2, top_left_y2),
                 (top_left_x2 + sw2, top_left_y2 + sh2), (0, 255, 0), 2)
    cv2.circle(screenshot2_np, (sx2, sy2), 5, (0, 255, 0), -1)
    cv2.putText(screenshot2_np, "Operator Icon", (sx2 + 10, sy2 - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw text detection zone (orange)
    zone_left_s = int(zone_left * scale_factor)
    zone_top_s = int(zone_top * scale_factor)
    zone_width_s = int(zone_width * scale_factor)
    zone_height_s = int(zone_height * scale_factor)

    cv2.rectangle(screenshot2_np, (zone_left_s, zone_top_s),
                 (zone_left_s + zone_width_s, zone_top_s + zone_height_s),
                 (0, 165, 255), 2)

    if operator_count:
        label = f"{operator_count['in_use']}/{operator_count['total']}"
        cv2.putText(screenshot2_np, label, (zone_left_s + 5, zone_top_s - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

    # Save visualization
    cv2.imwrite("visualizeTries/operator_count_detection.png", screenshot2_np)
    print(f"\n💾 Visualization saved: visualizeTries/operator_count_detection.png")

    print("\n" + "="*60)
    print("Legend:")
    print("  Green box = Operator icon")
    print("  Orange box = Text detection zone (operator count)")
    print("="*60)
    print("\nTo adjust the text detection zone:")
    print("1. Open detection_config.py")
    print("2. Adjust OPERATOR_COUNT_* settings:")
    print("   - OPERATOR_COUNT_OFFSET_X: Horizontal distance from icon to text")
    print("   - OPERATOR_COUNT_ZONE_WIDTH: Width of text detection area")
    print("   - OPERATOR_COUNT_OFFSET_Y: Vertical offset from icon center")
    print("   - OPERATOR_COUNT_ZONE_HEIGHT: Height of text detection area")
    print("3. Re-run this script to verify")
    print("="*60)


if __name__ == "__main__":
    test_operator_detection()
