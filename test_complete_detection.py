#!/usr/bin/env python3
"""
Complete detection test - shows task card borders and material number detection.
"""

import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path
from task_card_detector import TaskCardDetector

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️ pytesseract not installed - number values will not be read")


def _is_red_text(roi):
    """Check if text region is red colored."""
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    red_pixels = cv2.countNonZero(red_mask)
    total_pixels = roi.shape[0] * roi.shape[1]
    return (red_pixels / total_pixels) > 0.3  # >30% red = red text


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
        Path("visualizeTries/ocr_debug").mkdir(parents=True, exist_ok=True)
        cv2.imwrite(f"visualizeTries/ocr_debug/roi_{debug_index}_original.png", enlarged)
        cv2.imwrite(f"visualizeTries/ocr_debug/roi_{debug_index}_otsu.png", binary1)
        cv2.imwrite(f"visualizeTries/ocr_debug/roi_{debug_index}_adaptive.png", binary2)
        cv2.imwrite(f"visualizeTries/ocr_debug/roi_{debug_index}_simple.png", binary3)

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


def find_material_numbers(card_x, card_y, card_w, card_h, scale_factor):
    """
    Find black or red text numbers in the material area of a task card.

    Returns:
        List of (x, y) positions where numbers were found
    """
    # Import detection zone settings from centralized config
    from detection_config import MATERIAL_ZONE_START, MATERIAL_ZONE_END

    # Focus on material area (between title and DELIVER)
    material_y_start = int(card_h * MATERIAL_ZONE_START)
    material_y_end = int(card_h * MATERIAL_ZONE_END)
    material_height = material_y_end - material_y_start

    # Capture the material region
    screenshot = pyautogui.screenshot(region=(
        card_x,
        card_y + material_y_start,
        card_w,
        material_height
    ))
    region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

    # Import text detection settings
    from detection_config import BLACK_TEXT_MAX

    # Detect black text (material quantities - usually black)
    black_mask = cv2.inRange(gray, 0, BLACK_TEXT_MAX)

    # Also detect red text (warehouse stock numbers)
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # Combine black and red masks
    text_mask = cv2.bitwise_or(black_mask, red_mask)

    # Find contours of text regions
    contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
        return [], region

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

    # Now process merged boxes
    number_positions = []
    for idx, (x, y, w, h) in enumerate(merged_boxes):
        # Filter by final width (merged number should be reasonable size)
        if w < NUMBER_MIN_WIDTH or w > NUMBER_MAX_WIDTH * 3:  # Allow up to 3x width for multi-digit
            continue

        # Calculate center of number
        center_x = x + w // 2
        center_y = y + h // 2

        # Convert to absolute screen coordinates (card_x/y are already in logical pixels)
        abs_x = card_x + center_x
        abs_y = card_y + material_y_start + center_y

        # Determine if this is black or red text (with small padding)
        padding = 2
        roi_x = max(0, x - padding)
        roi_y = max(0, y - padding)
        roi_w = min(region.shape[1] - roi_x, w + 2 * padding)
        roi_h = min(region.shape[0] - roi_y, h + 2 * padding)
        text_roi = region[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        is_red = _is_red_text(text_roi)

        # OCR to read the number
        number_value = _ocr_number(text_roi, debug_index=idx)

        number_positions.append({
            'x': abs_x,
            'y': abs_y,
            'text_x': x,
            'text_y': y,
            'text_w': w,
            'text_h': h,
            'is_red': is_red,
            'value': number_value
        })

    return number_positions, region


def test_complete_detection():
    """Test both task card detection and material number detection with visualization."""
    print("="*60)
    print("Complete Detection Test")
    print("="*60)

    input("\nOpen the task menu with visible task cards, then press ENTER...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Initialize detector
    task_detector = TaskCardDetector()

    # Get screenshot
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Find task cards
    cards = task_detector.find_task_cards()
    print(f"\nFound {len(cards)} task card position(s)")

    # Process each card
    for i, (card_x, card_y, card_w, card_h) in enumerate(cards, 1):
        print(f"\n=== Card {i} ===")
        print(f"Position: ({card_x}, {card_y})")
        print(f"Size: {card_w}x{card_h}")

        # Check if task is available
        is_available = task_detector.is_task_available(card_x, card_y, card_w, card_h)
        status = "AVAILABLE" if is_available else "COMPLETING"
        color = (0, 255, 0) if is_available else (0, 0, 255)  # Green if available, Red if completing

        print(f"Status: {status}")

        # Draw card border
        sx = int(card_x * task_detector.scale_factor)
        sy = int(card_y * task_detector.scale_factor)
        sw = int(card_w * task_detector.scale_factor)
        sh = int(card_h * task_detector.scale_factor)

        cv2.rectangle(screenshot, (sx, sy), (sx + sw, sy + sh), color, 3)
        cv2.putText(screenshot, f"{i}: {status}", (sx, sy - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Detect material numbers if available
        if is_available:
            number_positions, region = find_material_numbers(card_x, card_y, card_w, card_h, task_detector.scale_factor)
            print(f"Material numbers detected: {len(number_positions)}")

            # Draw detected numbers and click positions
            for num_pos in number_positions:
                # Draw box around detected number
                num_sx = int(num_pos['x'] * task_detector.scale_factor)
                num_sy = int(num_pos['y'] * task_detector.scale_factor)

                # Color code by text color: red text = red dot, black text = yellow dot
                dot_color = (0, 0, 255) if num_pos['is_red'] else (255, 255, 0)
                cv2.circle(screenshot, (num_sx, num_sy), 5, dot_color, -1)

                # Import click offset setting
                from detection_config import CLICK_OFFSET_Y

                # Click position above the number
                click_x = num_pos['x']
                click_y = num_pos['y'] + CLICK_OFFSET_Y  # CLICK_OFFSET_Y is negative (e.g., -50)
                click_sx = int(click_x * task_detector.scale_factor)
                click_sy = int(click_y * task_detector.scale_factor)

                # Draw click position
                cv2.circle(screenshot, (click_sx, click_sy), 15, (255, 0, 255), -1)  # Magenta for click
                cv2.line(screenshot, (num_sx, num_sy), (click_sx, click_sy), (255, 255, 255), 1)  # Line from number to click

                # Add text label with OCR value and color
                color_text = "RED" if num_pos['is_red'] else "BLK"
                value_text = str(num_pos['value']) if num_pos['value'] is not None else "?"
                label = f"{value_text} ({color_text})"
                cv2.putText(screenshot, label, (num_sx + 10, num_sy),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                print(f"  {color_text} '{value_text}' at ({num_pos['x']}, {num_pos['y']}) -> Click at ({click_x}, {click_y})")

    # Draw material search region on first card for reference
    if cards:
        from detection_config import MATERIAL_ZONE_START, MATERIAL_ZONE_END

        card_x, card_y, card_w, card_h = cards[0]
        material_y_start = int(card_h * MATERIAL_ZONE_START)
        material_y_end = int(card_h * MATERIAL_ZONE_END)

        region_sx = int(card_x * task_detector.scale_factor)
        region_sy = int((card_y + material_y_start) * task_detector.scale_factor)
        region_sw = int(card_w * task_detector.scale_factor)
        region_sh = int((material_y_end - material_y_start) * task_detector.scale_factor)

        cv2.rectangle(screenshot, (region_sx, region_sy), (region_sx + region_sw, region_sy + region_sh),
                     (0, 255, 255), 1)  # Cyan for material search region
        cv2.putText(screenshot, "Material Search Zone", (region_sx + 5, region_sy + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Save visualization
    Path("visualizeTries").mkdir(exist_ok=True)
    save_path = "visualizeTries/complete_detection.png"
    cv2.imwrite(save_path, screenshot)
    print(f"\n💾 Visualization saved: {save_path}")

    print("\n" + "="*60)
    print("Legend:")
    print("  Green border = Available task")
    print("  Red border = Completing task")
    print("  Yellow dots = Black text numbers")
    print("  Red dots = Red text numbers")
    print("  Magenta circles = Click positions (above numbers)")
    print("  White lines = Connection from number to click position")
    print("  White labels = OCR value and color (BLK/RED)")
    print("  Cyan box = Material search zone (first card)")
    print("="*60)


if __name__ == "__main__":
    test_complete_detection()
