#!/usr/bin/env python3
"""
Train Capacity Detector
Detects train capacity numbers for all available train slots.
"""

import cv2
import numpy as np
import pyautogui
from typing import List, Dict, Optional


def _ocr_number(roi) -> Optional[int]:
    """Use OCR to read number from text region."""
    try:
        import pytesseract
    except ImportError:
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

        # Method 1: OTSU
        _, binary1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        text1 = pytesseract.image_to_string(binary1, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        digits1 = ''.join(filter(str.isdigit, text1))
        if digits1:
            results.append(int(digits1))

        # Method 2: Adaptive threshold
        binary2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        text2 = pytesseract.image_to_string(binary2, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        digits2 = ''.join(filter(str.isdigit, text2))
        if digits2:
            results.append(int(digits2))

        # Method 3: Simple threshold
        _, binary3 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        text3 = pytesseract.image_to_string(binary3, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        digits3 = ''.join(filter(str.isdigit, text3))
        if digits3:
            results.append(int(digits3))

        # Return most common result
        if results:
            return max(set(results), key=results.count)
        return None
    except Exception:
        return None


def _find_capacity_in_zone(zone_left: int, zone_top: int, zone_width: int, zone_height: int, slot_idx: int) -> Optional[Dict]:
    """
    Find train capacity number in a specific zone.

    Returns:
        dict with 'capacity', 'slot', 'x', 'y' or None if not found
    """
    # Capture the train capacity region
    screenshot = pyautogui.screenshot(region=(zone_left, zone_top, zone_width, zone_height))
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
        # Filter by height
        if h < NUMBER_MIN_HEIGHT or h > NUMBER_MAX_HEIGHT:
            continue
        valid_boxes.append([x, y, w, h])

    if not valid_boxes:
        return None

    # Sort boxes left to right
    valid_boxes.sort(key=lambda b: b[0])

    # Merge nearby boxes that are on the same line
    merged_boxes = []
    current_box = valid_boxes[0]

    for next_box in valid_boxes[1:]:
        curr_x, curr_y, curr_w, curr_h = current_box
        next_x, next_y, next_w, next_h = next_box

        y_diff = abs(curr_y - next_y)
        x_gap = next_x - (curr_x + curr_w)
        avg_width = (curr_w + next_w) / 2

        if y_diff < 5 and x_gap < avg_width * 1.5:
            # Merge boxes
            new_x = curr_x
            new_y = min(curr_y, next_y)
            new_w = (next_x + next_w) - curr_x
            new_h = max(curr_h, next_h)
            current_box = [new_x, new_y, new_w, new_h]
        else:
            merged_boxes.append(current_box)
            current_box = next_box

    merged_boxes.append(current_box)

    # Process merged boxes
    for x, y, w, h in merged_boxes:
        # Filter by final width
        if w < NUMBER_MIN_WIDTH or w > NUMBER_MAX_WIDTH * 3:
            continue

        # Calculate center
        center_x = x + w // 2
        center_y = y + h // 2

        # Convert to absolute screen coordinates
        abs_x = zone_left + center_x
        abs_y = zone_top + center_y

        # Extract ROI for OCR (with padding)
        padding = 2
        roi_x = max(0, x - padding)
        roi_y = max(0, y - padding)
        roi_w = min(region.shape[1] - roi_x, w + 2 * padding)
        roi_h = min(region.shape[0] - roi_y, h + 2 * padding)
        text_roi = region[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        # OCR to read the number
        capacity = _ocr_number(text_roi)

        if capacity is not None:
            # Sanity check: train capacity is usually between 5-200
            # Filter out obviously wrong readings
            if 5 <= capacity <= 200:
                return {
                    'capacity': capacity,
                    'slot': slot_idx,
                    'x': abs_x,
                    'y': abs_y
                }
            else:
                print(f"    ⚠️  OCR read {capacity} (out of range 5-200), ignoring")

    return None


def get_first_train_capacity() -> Optional[Dict]:
    """
    Get the capacity of the first (leftmost) available train.

    Returns:
        dict with 'capacity', 'x', 'y' or None if no train available
    """
    from detection_config import (TRAIN_CAPACITY_ZONE_TOP, TRAIN_CAPACITY_ZONE_BOTTOM,
                                  TRAIN_CAPACITY_ZONE_LEFT, TRAIN_CAPACITY_ZONE_RIGHT)

    # Get screen size
    screen_width, screen_height = pyautogui.size()

    # Calculate zone dimensions for first train only
    zone_top = int(screen_height * TRAIN_CAPACITY_ZONE_TOP)
    zone_bottom = int(screen_height * TRAIN_CAPACITY_ZONE_BOTTOM)
    zone_height = zone_bottom - zone_top

    zone_left = int(screen_width * TRAIN_CAPACITY_ZONE_LEFT)
    zone_right = int(screen_width * TRAIN_CAPACITY_ZONE_RIGHT)
    zone_width = zone_right - zone_left

    # Detect capacity in first train slot
    train = _find_capacity_in_zone(zone_left, zone_top, zone_width, zone_height, slot_idx=0)

    if train:
        return {
            'capacity': train['capacity'],
            'x': train['x'],
            'y': train['y']
        }

    return None
