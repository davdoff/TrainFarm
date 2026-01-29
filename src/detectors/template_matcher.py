#!/usr/bin/env python3
"""
Template Matching Script
Takes a screenshot template and finds its coordinates on the screen.

Usage:
    python template_matcher.py <template_image_path>

Example:
    python template_matcher.py button_screenshot.png
"""

import cv2
import numpy as np
import pyautogui
import sys
from pathlib import Path


def get_scale_factor():
    """
    Calculate the scale factor between screenshot resolution and PyAutoGUI coordinates.
    This handles Retina displays and high-DPI screens.

    Returns:
        float: Scale factor (e.g., 2.0 for Retina displays)
    """
    # Get PyAutoGUI screen size (logical resolution)
    screen_width, screen_height = pyautogui.size()

    # Get actual screenshot size (physical resolution)
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_height, screenshot_width = screenshot_np.shape[:2]

    # Calculate scale factor
    scale_x = screenshot_width / screen_width
    scale_y = screenshot_height / screen_height

    # They should be the same, but take average just in case
    return (scale_x + scale_y) / 2


def find_template_on_screen(template_path, threshold=0.8, region=None, screenshot_bgr=None):
    """
    Find a template image on the current screen.

    Args:
        template_path: Path to the template image (screenshot of button/text)
        threshold: Match confidence threshold (0-1, default 0.8)
        region: Optional tuple (x, y, width, height) to search only that area.
                Coordinates should be in PyAutoGUI space (logical pixels).
        screenshot_bgr: Optional pre-captured screenshot in BGR format. If None, takes new screenshot.

    Returns:
        Dictionary with coordinates and confidence, or None if not found
        {
            'x': center_x,
            'y': center_y,
            'top_left': (x, y),
            'bottom_right': (x, y),
            'confidence': float,
            'width': int,
            'height': int
        }
    """
    # Use provided screenshot or take a new one
    if screenshot_bgr is None:
        # Take screenshot of current screen (or region if specified)
        if region:
            screenshot = pyautogui.screenshot(region=region)
            region_x, region_y = region[0], region[1]
        else:
            screenshot = pyautogui.screenshot()
            region_x, region_y = 0, 0
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    else:
        # Use provided screenshot
        screenshot = screenshot_bgr
        if region:
            region_x, region_y = region[0], region[1]
            # Crop to region if specified
            scale_factor = get_scale_factor()
            x, y, w, h = region
            x_scaled = int(x * scale_factor)
            y_scaled = int(y * scale_factor)
            w_scaled = int(w * scale_factor)
            h_scaled = int(h * scale_factor)
            screenshot = screenshot[y_scaled:y_scaled+h_scaled, x_scaled:x_scaled+w_scaled]
        else:
            region_x, region_y = 0, 0

    # Load template image (force BGR, ignore alpha channel)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {template_path}")

    # Get template dimensions
    template_height, template_width = template.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # Find the best match
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if match confidence is above threshold
    if max_val < threshold:
        return None

    # Get scale factor for Retina/HiDPI displays
    scale_factor = get_scale_factor()

    # Calculate coordinates in screenshot space
    top_left = max_loc
    bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
    center_x = top_left[0] + template_width // 2
    center_y = top_left[1] + template_height // 2

    # Convert to PyAutoGUI coordinate space (divide by scale factor and add region offset)
    return {
        'x': int(center_x / scale_factor) + region_x,
        'y': int(center_y / scale_factor) + region_y,
        'top_left': (int(top_left[0] / scale_factor) + region_x, int(top_left[1] / scale_factor) + region_y),
        'bottom_right': (int(bottom_right[0] / scale_factor) + region_x, int(bottom_right[1] / scale_factor) + region_y),
        'confidence': max_val,
        'width': int(template_width / scale_factor),
        'height': int(template_height / scale_factor)
    }


def find_all_matches(template_path, threshold=0.8, region=None, screenshot_bgr=None):
    """
    Find ALL occurrences of a template on screen (for repeated buttons/icons).

    Args:
        template_path: Path to the template image
        threshold: Match confidence threshold (0-1, default 0.8)
        region: Optional tuple (x, y, width, height) to search only that area.
                Coordinates should be in PyAutoGUI space (logical pixels).
        screenshot_bgr: Optional pre-captured screenshot in BGR format. If None, takes new screenshot.

    Returns:
        List of coordinate dictionaries
    """
    # Use provided screenshot or take a new one
    if screenshot_bgr is None:
        if region:
            screenshot = pyautogui.screenshot(region=region)
            region_x, region_y = region[0], region[1]
        else:
            screenshot = pyautogui.screenshot()
            region_x, region_y = 0, 0
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    else:
        # Use provided screenshot
        screenshot = screenshot_bgr
        if region:
            region_x, region_y = region[0], region[1]
            # Crop to region if specified
            scale_factor = get_scale_factor()
            x, y, w, h = region
            x_scaled = int(x * scale_factor)
            y_scaled = int(y * scale_factor)
            w_scaled = int(w * scale_factor)
            h_scaled = int(h * scale_factor)
            screenshot = screenshot[y_scaled:y_scaled+h_scaled, x_scaled:x_scaled+w_scaled]
        else:
            region_x, region_y = 0, 0

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {template_path}")

    template_height, template_width = template.shape[:2]

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # Get scale factor for Retina/HiDPI displays
    scale_factor = get_scale_factor()

    # Find all locations above threshold
    locations = np.where(result >= threshold)
    matches = []

    for pt in zip(*locations[::-1]):
        top_left = pt
        bottom_right = (pt[0] + template_width, pt[1] + template_height)
        center_x = pt[0] + template_width // 2
        center_y = pt[1] + template_height // 2
        confidence = result[pt[1], pt[0]]

        # Convert to PyAutoGUI coordinate space (divide by scale factor and add region offset)
        matches.append({
            'x': int(center_x / scale_factor) + region_x,
            'y': int(center_y / scale_factor) + region_y,
            'top_left': (int(top_left[0] / scale_factor) + region_x, int(top_left[1] / scale_factor) + region_y),
            'bottom_right': (int(bottom_right[0] / scale_factor) + region_x, int(bottom_right[1] / scale_factor) + region_y),
            'confidence': float(confidence),
            'width': int(template_width / scale_factor),
            'height': int(template_height / scale_factor)
        })

    return matches


def visualize_match(template_path, threshold=0.8, save_path="match_result.png"):
    """
    Create a visualization showing where the template was found.
    Saves an image with a red rectangle around the match.

    Args:
        template_path: Path to template image
        threshold: Match confidence threshold
        save_path: Where to save the visualization
    """
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    match = find_template_on_screen(template_path, threshold)

    if match:
        cv2.rectangle(screenshot, match['top_left'], match['bottom_right'],
                     (0, 0, 255), 3)
        cv2.circle(screenshot, (match['x'], match['y']), 5, (0, 255, 0), -1)
        cv2.imwrite(save_path, screenshot)
        print(f"Match visualization saved to: {save_path}")
    else:
        print("No match found to visualize")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python template_matcher.py <template_image_path>")
        print("\nExample: python template_matcher.py button.png")
        sys.exit(1)

    template_path = sys.argv[1]

    if not Path(template_path).exists():
        print(f"Error: Template file not found: {template_path}")
        sys.exit(1)

    print(f"Searching for template: {template_path}")
    print("Taking screenshot and matching...")

    # Find the template
    match = find_template_on_screen(template_path, threshold=0.8)

    if match:
        print("\n✓ MATCH FOUND!")
        print(f"  Center coordinates: ({match['x']}, {match['y']})")
        print(f"  Top-left corner: {match['top_left']}")
        print(f"  Bottom-right corner: {match['bottom_right']}")
        print(f"  Confidence: {match['confidence']:.2%}")
        print(f"  Size: {match['width']}x{match['height']} pixels")

        # Create visualization
        visualize_match(template_path)

        print("\nTo click this location, use:")
        print(f"  pyautogui.click({match['x']}, {match['y']})")

    else:
        print("\n✗ No match found")
        print("  Try lowering the threshold or taking a new screenshot")
        print("  Example: match = find_template_on_screen('template.png', threshold=0.7)")
