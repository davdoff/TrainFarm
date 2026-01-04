#!/usr/bin/env python3
"""
Material Shape Detector
Finds material containers by detecting rounded rectangles with white/blue backgrounds.
"""

import cv2
import numpy as np
import pyautogui
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class MaterialShapeDetector:
    """Detects material containers by shape rather than icon matching."""

    def __init__(self):
        from template_matcher import get_scale_factor
        self.scale_factor = get_scale_factor()

        # Load completing icon template to exclude it
        self.completing_icon = self._load_completing_icon()

    def _load_completing_icon(self):
        """Load the completing task icon template."""
        template_path = Path("Templates/completingTask.png")
        if template_path.exists():
            return cv2.imread(str(template_path))
        return None

    def find_rounded_rectangles(self, card_x: int, card_y: int, card_width: int, card_height: int,
                                 visualize: bool = False) -> List[Dict]:
        """
        Find rounded rectangle shapes (material containers) in the upper portion of a task card.

        Args:
            card_x, card_y: Top-left position of task card
            card_width, card_height: Card dimensions
            visualize: If True, save debug visualization

        Returns:
            List of detected material containers with positions
        """
        print(f"\n=== Detecting Material Shapes ===")
        print(f"Card region: ({card_x}, {card_y}, {card_width}x{card_height})")

        # Focus on upper-middle area where materials appear
        # Materials are typically in the top portion of the card
        material_y_start = int(card_height * 0.18)  # Start below title/progress (after "3/4")
        material_y_end = int(card_height * 0.45)    # End before "DELIVER" section
        material_height = material_y_end - material_y_start

        # Capture the material region
        scaled_x = int(card_x * self.scale_factor)
        scaled_y = int((card_y + material_y_start) * self.scale_factor)
        scaled_w = int(card_width * self.scale_factor)
        scaled_h = int(material_height * self.scale_factor)

        screenshot = pyautogui.screenshot(region=(
            card_x,
            card_y + material_y_start,
            card_width,
            material_height
        ))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        print(f"Material search region: y={card_y + material_y_start} to {card_y + material_y_end}")

        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        # Detect edges
        edges = cv2.Canny(gray, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        materials = []
        debug_image = region.copy() if visualize else None

        print(f"Found {len(contours)} contours, filtering for material shapes...")

        for contour in contours:
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by size (materials are roughly 50-80px square)
            if w < 40 or w > 100 or h < 40 or h > 100:
                continue

            # Aspect ratio should be close to square (0.8 to 1.3)
            aspect_ratio = w / h
            if aspect_ratio < 0.7 or aspect_ratio > 1.4:
                continue

            # Get ROI for checks
            roi = region[y:y+h, x:x+w]

            # Skip if this looks like the completing icon (clock)
            if self._is_completing_icon(roi):
                if visualize:
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(debug_image, "CLOCK", (x, y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                continue

            # Check if the area has white or blue background
            if not self._has_material_background(roi):
                continue

            # Check if there's a number below this container (material quantity)
            # Look for black text (number) directly below the container
            has_number = self._has_number_below(region, x, y, w, h)
            if not has_number:
                if visualize:
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (255, 0, 0), 1)
                    cv2.putText(debug_image, "NO NUM", (x, y - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                continue

            # Convert to absolute screen coordinates
            abs_x = int((card_x + x) / self.scale_factor)
            abs_y = int((card_y + material_y_start + y) / self.scale_factor)
            abs_w = int(w / self.scale_factor)
            abs_h = int(h / self.scale_factor)

            material = {
                'x': abs_x,
                'y': abs_y,
                'width': abs_w,
                'height': abs_h,
                'center_x': abs_x + abs_w // 2,
                'center_y': abs_y + abs_h // 2
            }

            materials.append(material)

            if visualize:
                # Draw on debug image
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(debug_image, f"{abs_w}x{abs_h}",
                           (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Remove overlapping detections (keep largest)
        materials = self._remove_overlaps(materials)

        print(f"✅ Detected {len(materials)} material container(s)")

        if visualize:
            Path("visualizeTries").mkdir(exist_ok=True)
            save_path = "visualizeTries/material_shapes.png"
            cv2.imwrite(save_path, debug_image)
            print(f"Visualization saved: {save_path}")

        return materials

    def _is_completing_icon(self, roi: np.ndarray) -> bool:
        """
        Check if ROI matches the completing task clock icon.

        Args:
            roi: Image region to check

        Returns:
            True if this looks like the clock icon
        """
        if self.completing_icon is None:
            return False

        # Resize ROI to match template size for comparison
        try:
            template_h, template_w = self.completing_icon.shape[:2]
            roi_resized = cv2.resize(roi, (template_w, template_h))

            # Template matching
            result = cv2.matchTemplate(roi_resized, self.completing_icon, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            # If confidence > 60%, it's the clock icon
            return max_val > 0.60
        except:
            return False

    def _has_number_below(self, region: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
        """
        Check if there's a number directly below the material container.

        Args:
            region: Full material search region
            x, y, w, h: Bounding box of material container

        Returns:
            True if black text (number) detected below
        """
        # Look in a small area below the container
        below_y = y + h + 2
        below_height = 20

        # Make sure we don't go out of bounds
        if below_y + below_height > region.shape[0]:
            return False

        # Extract region below container
        below_roi = region[below_y:below_y + below_height, x:x + w]

        # Convert to grayscale
        gray = cv2.cvtColor(below_roi, cv2.COLOR_BGR2GRAY)

        # Detect black text (dark pixels)
        black_mask = cv2.inRange(gray, 0, 80)

        # Count black pixels
        black_pixels = cv2.countNonZero(black_mask)
        total_pixels = below_roi.shape[0] * below_roi.shape[1]

        # If more than 3% black pixels, there's likely a number
        black_percentage = black_pixels / total_pixels
        return black_percentage > 0.03

    def _has_material_background(self, roi: np.ndarray) -> bool:
        """
        Check if ROI has white or blue background typical of material containers.

        Args:
            roi: Image region to check

        Returns:
            True if background matches material container pattern
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # White background detection (high value, low saturation)
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 60, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        # Blue background detection
        lower_blue = np.array([90, 80, 100])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Combine masks
        combined_mask = cv2.bitwise_or(white_mask, blue_mask)

        # Calculate percentage of white/blue pixels
        bg_pixels = cv2.countNonZero(combined_mask)
        total_pixels = roi.shape[0] * roi.shape[1]
        bg_percentage = bg_pixels / total_pixels

        # Material containers should have >30% white or blue background
        return bg_percentage > 0.30

    def _remove_overlaps(self, materials: List[Dict]) -> List[Dict]:
        """
        Remove overlapping material detections, keeping the largest ones.

        Args:
            materials: List of detected material containers

        Returns:
            Filtered list without overlaps
        """
        if len(materials) <= 1:
            return materials

        # Sort by area (largest first)
        materials.sort(key=lambda m: m['width'] * m['height'], reverse=True)

        unique = []
        for mat in materials:
            is_overlap = False
            for existing in unique:
                # Check if centers are close (within 40px)
                dx = abs(mat['center_x'] - existing['center_x'])
                dy = abs(mat['center_y'] - existing['center_y'])

                if dx < 40 and dy < 40:
                    is_overlap = True
                    break

            if not is_overlap:
                unique.append(mat)

        return unique

    def find_empty_click_area(self, card_x: int, card_y: int, card_width: int, card_height: int,
                              materials: List[Dict]) -> Tuple[int, int]:
        """
        Find an empty area to click that avoids material containers.

        Args:
            card_x, card_y: Card position
            card_width, card_height: Card dimensions
            materials: List of detected material containers

        Returns:
            (x, y) coordinates for safe click area
        """
        # Default click position (right side of card, upper area)
        default_x = card_x + int(card_width * 0.75)
        default_y = card_y + int(card_height * 0.30)

        if not materials:
            return (default_x, default_y)

        # Try several candidate positions
        candidates = [
            (card_x + int(card_width * 0.75), card_y + int(card_height * 0.30)),  # Right side
            (card_x + int(card_width * 0.50), card_y + int(card_height * 0.35)),  # Center
            (card_x + int(card_width * 0.25), card_y + int(card_height * 0.30)),  # Left side
        ]

        # Find candidate furthest from all materials
        best_pos = default_x, default_y
        best_distance = 0

        for cx, cy in candidates:
            min_distance = float('inf')

            for mat in materials:
                dx = cx - mat['center_x']
                dy = cy - mat['center_y']
                distance = (dx * dx + dy * dy) ** 0.5
                min_distance = min(min_distance, distance)

            if min_distance > best_distance:
                best_distance = min_distance
                best_pos = (cx, cy)

        return best_pos


def test_shape_detection():
    """Test material shape detection on current screen."""
    print("="*60)
    print("Material Shape Detector Test")
    print("="*60)

    input("\nOpen a task card with materials visible, then press ENTER...")

    import time
    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    detector = MaterialShapeDetector()

    # Test on first task card position (updated to match task_card_detector.py)
    card_x, card_y = 110, 135
    card_width, card_height = 360, 670

    materials = detector.find_rounded_rectangles(card_x, card_y, card_width, card_height, visualize=True)

    print(f"\n=== Results ===")
    if materials:
        for i, mat in enumerate(materials, 1):
            print(f"  Material {i}: ({mat['x']}, {mat['y']}) {mat['width']}x{mat['height']}")

        # Find click area
        click_x, click_y = detector.find_empty_click_area(card_x, card_y, card_width, card_height, materials)
        print(f"\nEmpty click area: ({click_x}, {click_y})")
    else:
        print("  No materials detected")

    print("\n" + "="*60)


if __name__ == "__main__":
    test_shape_detection()
