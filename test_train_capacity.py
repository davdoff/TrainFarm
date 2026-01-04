#!/usr/bin/env python3
"""
Train Capacity Detection Test - Calibrate zone for reading train capacity numbers.
This helps you detect how much material each train can carry.
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
    print("⚠️ pytesseract not installed - number values will not be read")


def _ocr_number(roi, debug_index=0):
    """Use OCR to read number from text region."""
    if not HAS_OCR:
        return None

    try:
        # Upscale the ROI for better OCR (3x larger)
        scale = 3
        height, width = roi.shape[:2]

        # Skip if ROI is too small
        if width < 5 or height < 5:
            return None

        enlarged = cv2.resize(roi, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC)

        # Convert to grayscale
        gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

        # Try multiple thresholding methods
        results = []
        texts = []

        # Method 1: OTSU
        _, binary1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        text1 = pytesseract.image_to_string(binary1, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        texts.append(f"OTSU:{text1.strip()}")
        digits1 = ''.join(filter(str.isdigit, text1))
        if digits1:
            results.append(int(digits1))

        # Method 2: Adaptive threshold
        binary2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        text2 = pytesseract.image_to_string(binary2, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        texts.append(f"ADAPT:{text2.strip()}")
        digits2 = ''.join(filter(str.isdigit, text2))
        if digits2:
            results.append(int(digits2))

        # Method 3: Simple threshold
        _, binary3 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        text3 = pytesseract.image_to_string(binary3, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        texts.append(f"SIMPLE:{text3.strip()}")
        digits3 = ''.join(filter(str.isdigit, text3))
        if digits3:
            results.append(int(digits3))

        # Save debug images
        Path("visualizeTries/train_ocr_debug").mkdir(parents=True, exist_ok=True)
        cv2.imwrite(f"visualizeTries/train_ocr_debug/roi_{debug_index}_original.png", enlarged)
        cv2.imwrite(f"visualizeTries/train_ocr_debug/roi_{debug_index}_otsu.png", binary1)
        cv2.imwrite(f"visualizeTries/train_ocr_debug/roi_{debug_index}_adaptive.png", binary2)
        cv2.imwrite(f"visualizeTries/train_ocr_debug/roi_{debug_index}_simple.png", binary3)

        # Return most common result, or first valid one
        if results:
            result = max(set(results), key=results.count)
            print(f"    OCR #{debug_index}: SUCCESS={result} (results={results}, raw={texts})")
            return result
        print(f"    OCR #{debug_index}: FAILED (no digits found, raw={texts})")
        return None
    except Exception as e:
        print(f"    OCR #{debug_index}: Error - {e}")
        return None


def find_train_capacity_in_zone(zone_left, zone_top, zone_width, zone_height, train_slot_index):
    """
    Find train capacity number in a specific zone.

    Args:
        zone_left, zone_top: Top-left corner of zone (absolute pixels)
        zone_width, zone_height: Size of zone (pixels)
        train_slot_index: Which train slot (0-3)

    Returns:
        dict with 'x', 'y', 'value', 'slot' or None if not found
    """
    # Capture the train capacity region
    screenshot = pyautogui.screenshot(region=(
        zone_left,
        zone_top,
        zone_width,
        zone_height
    ))
    region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

    # Import text detection settings
    from detection_config import BLACK_TEXT_MAX

    # Detect black text (train capacity numbers are usually black)
    black_mask = cv2.inRange(gray, 0, BLACK_TEXT_MAX)

    # Find contours of text regions
    contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Import number size settings
    from detection_config import (NUMBER_MIN_WIDTH, NUMBER_MAX_WIDTH,
                                 NUMBER_MIN_HEIGHT, NUMBER_MAX_HEIGHT)

    # Get bounding boxes for all valid contours
    valid_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Filter by height (individual digits should have reasonable height)
        if h < NUMBER_MIN_HEIGHT or h > NUMBER_MAX_HEIGHT:
            continue
        valid_boxes.append([x, y, w, h])

    if not valid_boxes:
        return [], region, (zone_left, zone_top, zone_width, zone_height)

    # Sort boxes left to right
    valid_boxes.sort(key=lambda b: b[0])

    # Merge nearby boxes that are on the same line (likely same number)
    merged_boxes = []
    current_box = valid_boxes[0]

    for next_box in valid_boxes[1:]:
        curr_x, curr_y, curr_w, curr_h = current_box
        next_x, next_y, next_w, next_h = next_box

        # Check if boxes are on the same horizontal line (within 5 pixels)
        y_diff = abs(curr_y - next_y)
        # Check if boxes are close horizontally (gap less than average width)
        x_gap = next_x - (curr_x + curr_w)
        avg_width = (curr_w + next_w) / 2

        if y_diff < 5 and x_gap < avg_width * 1.5:
            # Merge boxes - extend current box to include next box
            new_x = curr_x
            new_y = min(curr_y, next_y)
            new_w = (next_x + next_w) - curr_x
            new_h = max(curr_h, next_h)
            current_box = [new_x, new_y, new_w, new_h]
        else:
            # Boxes are separate - save current and start new
            merged_boxes.append(current_box)
            current_box = next_box

    # Don't forget the last box
    merged_boxes.append(current_box)

    # Now process merged boxes - should only find one number per train slot
    for idx, (x, y, w, h) in enumerate(merged_boxes):
        # Filter by final width (merged number should be reasonable size)
        if w < NUMBER_MIN_WIDTH or w > NUMBER_MAX_WIDTH * 3:  # Allow up to 3x width for multi-digit
            continue

        # Calculate center of number
        center_x = x + w // 2
        center_y = y + h // 2

        # Convert to absolute screen coordinates
        abs_x = zone_left + center_x
        abs_y = zone_top + center_y

        # Extract ROI for OCR (with small padding)
        padding = 2
        roi_x = max(0, x - padding)
        roi_y = max(0, y - padding)
        roi_w = min(region.shape[1] - roi_x, w + 2 * padding)
        roi_h = min(region.shape[0] - roi_y, h + 2 * padding)
        text_roi = region[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        # OCR to read the number
        number_value = _ocr_number(text_roi, debug_index=train_slot_index)

        # Return the first (and ideally only) number found in this zone
        return {
            'x': abs_x,
            'y': abs_y,
            'value': number_value,
            'slot': train_slot_index
        }

    # No number found in this zone
    return None


def find_all_train_capacities():
    """
    Find train capacity numbers for all 4 train slots.

    Returns:
        List of train capacity dicts, list of all zone rectangles for visualization
    """
    # Import detection zone settings from centralized config
    from detection_config import (TRAIN_CAPACITY_ZONE_TOP, TRAIN_CAPACITY_ZONE_BOTTOM,
                                  TRAIN_CAPACITY_ZONE_LEFT, TRAIN_CAPACITY_ZONE_RIGHT,
                                  TRAIN_CAPACITY_GAP)

    # Get screen size
    screen_width, screen_height = pyautogui.size()

    # Calculate zone dimensions (same for all slots)
    zone_top = int(screen_height * TRAIN_CAPACITY_ZONE_TOP)
    zone_bottom = int(screen_height * TRAIN_CAPACITY_ZONE_BOTTOM)
    zone_height = zone_bottom - zone_top

    first_zone_left = int(screen_width * TRAIN_CAPACITY_ZONE_LEFT)
    first_zone_right = int(screen_width * TRAIN_CAPACITY_ZONE_RIGHT)
    zone_width = first_zone_right - first_zone_left

    gap_pixels = int(screen_width * TRAIN_CAPACITY_GAP)

    # Detect capacity for all 4 train slots
    all_capacities = []
    all_zones = []

    for slot_idx in range(4):
        # Calculate left edge for this slot (offset by gap * slot_index)
        zone_left = first_zone_left + (gap_pixels * slot_idx)
        zone_right = zone_left + zone_width

        # Store zone for visualization
        all_zones.append((zone_left, zone_top, zone_width, zone_height))

        print(f"  Checking Train {slot_idx + 1} zone: left={zone_left}, top={zone_top}, width={zone_width}, height={zone_height}")

        # Detect number in this slot
        capacity = find_train_capacity_in_zone(zone_left, zone_top, zone_width, zone_height, slot_idx)

        if capacity and capacity.get('value') is not None:
            all_capacities.append(capacity)
            print(f"    ✓ Found capacity: {capacity['value']}")
        else:
            print(f"    ✗ No capacity detected (train may not be available)")

    return all_capacities, all_zones


def test_train_capacity_detection():
    """Test train capacity number detection with visualization."""
    print("="*60)
    print("Train Capacity Detection Test (4 Train Slots)")
    print("="*60)
    print("\nThis will help you calibrate the zones for detecting")
    print("train capacity numbers for all 4 train slots.")
    print("\nAdjust TRAIN_CAPACITY_ZONE settings in detection_config.py")

    input("\nAfter clicking a task, wait for trains to appear, then press ENTER...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Get full screenshot
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Detect train capacity numbers for all 4 slots
    train_capacities, all_zones = find_all_train_capacities()

    print(f"\nTrain capacity numbers detected: {len(train_capacities)} / 4 slots")

    # Get scale factor for display
    from template_matcher import get_scale_factor
    scale_factor = get_scale_factor()

    # Define colors for each slot
    slot_colors = [
        (255, 0, 255),   # Slot 0: Magenta
        (255, 165, 0),   # Slot 1: Orange
        (0, 255, 0),     # Slot 2: Green
        (255, 255, 0),   # Slot 3: Yellow
    ]

    # Draw all detection zones
    for slot_idx, (zone_left, zone_top, zone_width, zone_height) in enumerate(all_zones):
        region_sx = int(zone_left * scale_factor)
        region_sy = int(zone_top * scale_factor)
        region_sw = int(zone_width * scale_factor)
        region_sh = int(zone_height * scale_factor)

        color = slot_colors[slot_idx]

        cv2.rectangle(screenshot, (region_sx, region_sy), (region_sx + region_sw, region_sy + region_sh),
                     color, 2)
        cv2.putText(screenshot, f"Train {slot_idx + 1}", (region_sx + 5, region_sy + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Draw detected numbers
    for capacity in train_capacities:
        # Draw circle on detected number
        num_sx = int(capacity['x'] * scale_factor)
        num_sy = int(capacity['y'] * scale_factor)

        slot_idx = capacity['slot']
        color = slot_colors[slot_idx]

        # Colored dots for train capacity numbers (color matches slot)
        cv2.circle(screenshot, (num_sx, num_sy), 5, color, -1)

        # Add text label with OCR value
        value_text = str(capacity['value']) if capacity['value'] is not None else "?"
        label = f"Train {slot_idx + 1}: {value_text}"
        cv2.putText(screenshot, label, (num_sx + 10, num_sy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        print(f"  Train {slot_idx + 1} CAPACITY: {value_text} at ({capacity['x']}, {capacity['y']})")

    # Save visualization
    Path("visualizeTries").mkdir(exist_ok=True)
    save_path = "visualizeTries/train_capacity_detection.png"
    cv2.imwrite(save_path, screenshot)
    print(f"\n💾 Visualization saved: {save_path}")

    print("\n" + "="*60)
    print("Legend:")
    print("  Magenta (Train 1) = First train slot (leftmost)")
    print("  Orange (Train 2) = Second train slot")
    print("  Green (Train 3) = Third train slot")
    print("  Yellow (Train 4) = Fourth train slot (rightmost)")
    print("  Colored boxes = Detection zones for each train")
    print("  Colored dots = Detected capacity numbers (color matches train)")
    print("  White labels = OCR values")
    print("="*60)
    print("\nTo adjust the detection zones:")
    print("1. Open detection_config.py")
    print("2. Adjust first train slot position (MOST IMPORTANT):")
    print("   - TRAIN_CAPACITY_ZONE_TOP / TRAIN_CAPACITY_ZONE_BOTTOM (vertical)")
    print("   - TRAIN_CAPACITY_ZONE_LEFT / TRAIN_CAPACITY_ZONE_RIGHT (horizontal)")
    print("3. Adjust gap between trains (OPTIONAL - not used in automation):")
    print("   - TRAIN_CAPACITY_GAP (horizontal spacing between slots)")
    print("4. Re-run this script to verify Train 1 (Magenta) aligns perfectly")
    print("="*60)
    print("\nNOTE: The automation only uses Train 1 detection!")
    print("It detects the first train, sends it, then detects the next one (which moves to first position).")
    print("Trains 2-4 shown here are just for visualization/debugging.")
    print("="*60)


if __name__ == "__main__":
    test_train_capacity_detection()
