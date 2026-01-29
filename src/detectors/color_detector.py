#!/usr/bin/env python3
"""
Color Detection Module
Detects specific colors in screen regions (e.g., red text for insufficient materials).
"""

import cv2
import numpy as np
import pyautogui
from typing import Tuple, Optional


class ColorDetector:
    """Detects colors in screen regions using HSV color space."""

    # HSV color ranges
    RED_RANGES = [
        # Red wraps around in HSV, so we need two ranges
        ((0, 100, 100), (10, 255, 255)),     # Lower red range
        ((170, 100, 100), (180, 255, 255))   # Upper red range
    ]

    GREEN_RANGES = [
        ((40, 50, 50), (80, 255, 255))
    ]

    YELLOW_RANGES = [
        ((20, 100, 100), (30, 255, 255))
    ]

    def __init__(self):
        pass

    @staticmethod
    def capture_region(x: int, y: int, width: int, height: int) -> np.ndarray:
        """Capture a specific region of the screen."""
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    @staticmethod
    def is_color_in_range(image: np.ndarray, color_ranges: list) -> bool:
        """Check if any pixels in the image match the color ranges."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        mask = None
        for lower, upper in color_ranges:
            lower_bound = np.array(lower, dtype=np.uint8)
            upper_bound = np.array(upper, dtype=np.uint8)
            range_mask = cv2.inRange(hsv, lower_bound, upper_bound)

            if mask is None:
                mask = range_mask
            else:
                mask = cv2.bitwise_or(mask, range_mask)

        # Count non-zero pixels (pixels matching the color)
        color_pixels = cv2.countNonZero(mask)
        total_pixels = image.shape[0] * image.shape[1]

        # Return True if at least 5% of pixels match the color
        return (color_pixels / total_pixels) > 0.05

    def is_red_at_location(self, x: int, y: int, width: int = 50, height: int = 30) -> bool:
        """
        Check if there is red color at a specific location.
        Useful for detecting red material count numbers.

        Args:
            x, y: Center coordinates to check
            width, height: Size of region to check around the center

        Returns:
            True if red color is detected, False otherwise
        """
        # Calculate region coordinates (centered on x, y)
        region_x = x - width // 2
        region_y = y - height // 2

        # Ensure we don't go out of bounds
        region_x = max(0, region_x)
        region_y = max(0, region_y)

        # Capture the region
        image = self.capture_region(region_x, region_y, width, height)

        # Check for red color
        return self.is_color_in_range(image, self.RED_RANGES)

    def is_green_at_location(self, x: int, y: int, width: int = 50, height: int = 30) -> bool:
        """Check if there is green color at a specific location."""
        region_x = max(0, x - width // 2)
        region_y = max(0, y - height // 2)
        image = self.capture_region(region_x, region_y, width, height)
        return self.is_color_in_range(image, self.GREEN_RANGES)

    def get_dominant_color_type(self, x: int, y: int, width: int = 50, height: int = 30) -> Optional[str]:
        """
        Get the dominant color type at a location.

        Returns:
            'red', 'green', 'yellow', or None if no strong color detected
        """
        region_x = max(0, x - width // 2)
        region_y = max(0, y - height // 2)
        image = self.capture_region(region_x, region_y, width, height)

        if self.is_color_in_range(image, self.RED_RANGES):
            return 'red'
        elif self.is_color_in_range(image, self.GREEN_RANGES):
            return 'green'
        elif self.is_color_in_range(image, self.YELLOW_RANGES):
            return 'yellow'

        return None

    def detect_material_status(self, material_icon_x: int, material_icon_y: int,
                              number_offset_y: int = 30) -> str:
        """
        Detect if a material is sufficient (green/white) or insufficient (red).

        Args:
            material_icon_x, material_icon_y: Material icon coordinates
            number_offset_y: Offset below icon where the number appears

        Returns:
            'insufficient' if red, 'sufficient' otherwise
        """
        number_y = material_icon_y + number_offset_y

        if self.is_red_at_location(material_icon_x, number_y):
            return 'insufficient'
        else:
            return 'sufficient'

    @staticmethod
    def visualize_color_detection(x: int, y: int, width: int = 50, height: int = 30,
                                   save_path: str = "color_detection.png"):
        """
        Create a visualization of the color detection region.
        Useful for debugging and calibration.
        """
        region_x = max(0, x - width // 2)
        region_y = max(0, y - height // 2)

        # Capture full screen
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Draw rectangle around detection region
        cv2.rectangle(screenshot,
                     (region_x, region_y),
                     (region_x + width, region_y + height),
                     (0, 255, 255), 2)  # Yellow rectangle

        cv2.imwrite(save_path, screenshot)
        print(f"Visualization saved to {save_path}")
