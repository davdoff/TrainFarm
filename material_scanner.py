#!/usr/bin/env python3
"""
Material Scanner
Scans task cards for specific materials and checks their availability.
"""

import cv2
import numpy as np
import pyautogui
from pathlib import Path
from typing import List, Tuple, Optional
from template_matcher import find_all_matches, find_template_on_screen
from color_detector import ColorDetector

# Try to import pytesseract for OCR
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️  pytesseract not installed - quantity reading will be limited")
    print("   Install with: pip install pytesseract")


class MaterialScanner:
    """Scans for materials on task cards."""

    def __init__(self, materials_folder: str = "Templates/Materials"):
        self.materials_folder = Path(materials_folder)
        self.color_detector = ColorDetector()
        self.material_templates = self._load_material_templates()
        self.deliver_template = "Templates/DeliverTextLeftOfTheAmountNeeded.png"
        self.warehouse_template = "Templates/Storage.png"

    def _load_material_templates(self) -> dict:
        """Load all material templates from the Materials folder.
        Groups variants of the same material (e.g., Nails, Nails_blue).
        """
        templates = {}

        if not self.materials_folder.exists():
            print(f"⚠️  Materials folder not found: {self.materials_folder}")
            print(f"   Create it and add material PNG files")
            return templates

        # Load all PNG files from Materials folder
        for template_file in self.materials_folder.glob("*.png"):
            filename = template_file.stem  # Filename without .png

            # Group variants: "MaterialName_variant" or just "MaterialName"
            # e.g., "Nails_blue" and "Nails" both map to "Nails"
            base_name = filename.split('_')[0]

            # Store as list of paths for this material (supports multiple variants)
            if base_name not in templates:
                templates[base_name] = []
            templates[base_name].append(str(template_file))

        print(f"Loaded {len(templates)} material type(s)")
        for name, paths in templates.items():
            if len(paths) > 1:
                print(f"  - {name} ({len(paths)} variants)")
            else:
                print(f"  - {name}")

        return templates

    def _is_warehouse_icon(self, x: int, y: int) -> bool:
        """
        Check if a position matches the warehouse/storage icon.

        Args:
            x, y: Position to check

        Returns:
            True if warehouse icon detected at this position
        """
        # Check small region around the position
        try:
            region_size = 80
            screenshot = pyautogui.screenshot(region=(x - 20, y - 20, region_size, region_size))
            region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Load warehouse template
            warehouse_template = cv2.imread(self.warehouse_template)
            if warehouse_template is None:
                return False

            # Try to match
            result = cv2.matchTemplate(region, warehouse_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            # If high confidence match, it's the warehouse
            if max_val > 0.7:
                print(f"    ⚠️  Skipping - this is the warehouse icon!")
                return True

        except Exception:
            # If region is out of bounds or error, assume not warehouse
            pass

        return False

    def find_materials_on_card(self, card_x: int, card_y: int,
                               card_width: int, card_height: int,
                               visualize: bool = False) -> List[dict]:
        """
        Find all materials visible on a specific task card.
        Uses feature-based matching to ignore background colors.

        Args:
            card_x, card_y, card_width, card_height: Task card region
            visualize: If True, saves visualization image

        Returns:
            List of material dicts with {name, x, y, available}
        """
        materials_found = []

        # Capture the card region
        screenshot = pyautogui.screenshot(region=(card_x, card_y, card_width, card_height))
        card_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # For visualization
        if visualize:
            vis_image = card_image.copy()

        # Search for each material template using feature matching
        for material_name, template_paths in self.material_templates.items():
            # Try all variants of this material (e.g., white bg and blue bg)
            all_matches = []
            for template_path in template_paths:
                matches = self._find_material_with_features(card_image, template_path, card_x, card_y)
                all_matches.extend(matches)

            # Remove duplicates from different variants (keep best confidence)
            matches = all_matches
            if len(matches) > 1:
                matches.sort(key=lambda m: m['confidence'], reverse=True)
                unique = []
                for match in matches:
                    is_dup = any(abs(match['x'] - u['x']) < 30 and abs(match['y'] - u['y']) < 30
                                for u in unique)
                    if not is_dup:
                        unique.append(match)
                matches = unique

            for match in matches:
                mat_x = match['x']
                mat_y = match['y']

                # Skip if position is outside valid material area
                # Materials appear in upper 60% of card (not at bottom where warehouse/buttons are)
                rel_y = mat_y - card_y  # Y position relative to card top
                if rel_y > card_height * 0.6:
                    print(f"    ⚠️  Skipping {material_name} at ({mat_x}, {mat_y}) - too low on card (y={rel_y}, max={card_height * 0.6:.0f})")
                    continue

                # Skip if this is the warehouse icon
                if self._is_warehouse_icon(mat_x, mat_y):
                    continue

                # Check if material is available (has green checkmark or black text)
                is_available = self._check_material_availability(mat_x, mat_y)

                materials_found.append({
                    'name': material_name,
                    'x': mat_x,
                    'y': mat_y,
                    'width': match['width'],
                    'height': match['height'],
                    'available': is_available,
                    'confidence': match['confidence']
                })

                print(f"  Found '{material_name}' at ({mat_x}, {mat_y}) - "
                      f"{'✓ Available' if is_available else '✗ Not available'} "
                      f"(conf: {match['confidence']:.2%})")

                # Draw on visualization
                if visualize:
                    # Convert absolute coords to card-relative coords
                    from template_matcher import get_scale_factor
                    scale_factor = get_scale_factor()
                    rel_x = int((mat_x * scale_factor) - card_x)
                    rel_y = int((mat_y * scale_factor) - card_y)
                    rel_w = int(match['width'] * scale_factor)
                    rel_h = int(match['height'] * scale_factor)

                    # Draw rectangle
                    color = (0, 255, 0) if is_available else (0, 0, 255)
                    cv2.rectangle(vis_image, (rel_x, rel_y),
                                (rel_x + rel_w, rel_y + rel_h), color, 2)

                    # Draw label
                    label = f"{material_name} {match['confidence']:.0%}"
                    cv2.putText(vis_image, label, (rel_x, rel_y - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Save visualization
        if visualize:
            Path("visualizeTries").mkdir(exist_ok=True)
            cv2.imwrite("visualizeTries/material_detection.png", vis_image)
            print(f"\n💾 Visualization saved to: visualizeTries/material_detection.png")

        return materials_found

    def _find_material_with_features(self, card_image, template_path, offset_x, offset_y):
        """
        Find material using multiple matching strategies (handles background variations).

        Args:
            card_image: The card region image
            template_path: Path to material template
            offset_x, offset_y: Card position offset for absolute coordinates

        Returns:
            List of matches
        """
        # Load template
        template = cv2.imread(template_path)
        if template is None:
            return []

        template_h, template_w = template.shape[:2]

        # Strategy 1: Regular template matching
        result_regular = cv2.matchTemplate(card_image, template, cv2.TM_CCOEFF_NORMED)

        # Strategy 2: Edge-based matching (ignores colors)
        card_gray = cv2.cvtColor(card_image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        card_edges = cv2.Canny(card_gray, 50, 150)
        template_edges = cv2.Canny(template_gray, 50, 150)
        result_edges = cv2.matchTemplate(card_edges, template_edges, cv2.TM_CCOEFF_NORMED)

        # Strategy 3: Normalized cross-correlation (more robust)
        result_ccorr = cv2.matchTemplate(card_image, template, cv2.TM_CCORR_NORMED)

        # Combine all strategies (take best result from any method)
        result = np.maximum.reduce([
            result_regular,
            result_edges * 0.7,  # Weight edges slightly less
            result_ccorr * 0.85   # Weight ccorr slightly less
        ])

        threshold = 0.48  # Lower threshold - rely on position filtering to prevent false positives

        # Debug: Show best match confidence
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.4:
            template_name = Path(template_path).stem
            print(f"    [DEBUG] {template_name}: best match {max_val:.2%} at {max_loc}")

        locations = np.where(result >= threshold)
        matches = []

        from template_matcher import get_scale_factor
        scale_factor = get_scale_factor()

        for pt in zip(*locations[::-1]):
            # Convert to absolute screen coordinates
            abs_x = int((offset_x + pt[0]) / scale_factor)
            abs_y = int((offset_y + pt[1]) / scale_factor)

            matches.append({
                'x': abs_x,
                'y': abs_y,
                'width': int(template_w / scale_factor),
                'height': int(template_h / scale_factor),
                'confidence': float(result[pt[1], pt[0]])
            })

        # Remove duplicate matches (keep best confidence)
        if matches:
            matches.sort(key=lambda m: m['confidence'], reverse=True)
            unique_matches = []
            for match in matches:
                is_duplicate = False
                for existing in unique_matches:
                    if abs(match['x'] - existing['x']) < 30 and abs(match['y'] - existing['y']) < 30:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_matches.append(match)

            return unique_matches[:5]

        return []

    def _check_material_availability(self, material_x: int, material_y: int) -> bool:
        """
        Check if a material is available (green checkmark or black text below it).

        Args:
            material_x, material_y: Material icon position

        Returns:
            True if available, False if not
        """
        # Check for green checkmark near the material
        # Checkmark is usually to the right and slightly below the material icon
        checkmark_region_x = material_x + 30
        checkmark_region_y = material_y + 20

        # Check for green color
        screenshot = pyautogui.screenshot(region=(checkmark_region_x, checkmark_region_y, 40, 40))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        lower_green = np.array([40, 100, 100])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)

        green_pixels = cv2.countNonZero(green_mask)
        if green_pixels > 100:  # If substantial green found
            return True

        # Alternative: Check for black text (number) below material
        text_region_y = material_y + 50
        screenshot = pyautogui.screenshot(region=(material_x - 10, text_region_y, 40, 30))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        black_mask = cv2.inRange(gray, 0, 50)
        black_pixels = cv2.countNonZero(black_mask)

        # If substantial black text (black numbers = available, red = not available)
        if black_pixels > 50:
            return True

        return False

    def find_empty_click_area(self, card_x: int, card_y: int,
                              card_width: int, card_height: int,
                              materials: List[dict]) -> Tuple[int, int]:
        """
        Find an empty white area on the card to click (avoiding materials).
        Clicks on the left edge of the task card, avoiding materials entirely.

        Args:
            card_x, card_y, card_width, card_height: Card bounds
            materials: List of materials on the card

        Returns:
            (x, y) coordinates of empty area to click
        """
        # Strategy: Click on the left side of the card at a fixed position
        # This is typically where the task card's white/empty area is
        # Materials are usually in the middle/right area

        # Click on the left third of the card, upper-middle height
        click_x = card_x + int(card_width * 0.25)  # 25% from left edge
        click_y = card_y + int(card_height * 0.35)  # 35% from top

        print(f"DEBUG: Card bounds: ({card_x}, {card_y}, {card_width}x{card_height})")
        if materials:
            print(f"DEBUG: Found {len(materials)} materials:")
            for i, mat in enumerate(materials):
                print(f"  Material {i+1}: ({mat['x']}, {mat['y']}) - {mat['name']}")
        print(f"DEBUG: Clicking at ({click_x}, {click_y})")
        print(f"       (25% from left, 35% from top of card)")

        return (click_x, click_y)

    def _read_number_from_region(self, x: int, y: int, width: int, height: int,
                                   is_red: bool = False) -> Optional[int]:
        """
        Read a number from a specific screen region using OCR.

        Args:
            x, y, width, height: Region to read from
            is_red: If True, preprocess for red text; otherwise for black text

        Returns:
            Parsed number, or None if can't read
        """
        if not HAS_OCR:
            return None

        # Capture region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Preprocess based on text color
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        if is_red:
            # For red text: extract red channel and threshold
            _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        else:
            # For black text: simple threshold
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # Save debug image
        Path("visualizeTries").mkdir(exist_ok=True)
        cv2.imwrite(f"visualizeTries/ocr_debug_{x}_{y}.png", binary)

        # Use pytesseract to read text (digits only)
        text = pytesseract.image_to_string(binary, config='--psm 7 digits')
        text = text.strip()

        # Parse number
        try:
            # Extract just digits
            import re
            digits = re.findall(r'\d+', text)
            if digits:
                return int(digits[0])
        except ValueError:
            pass

        return None

    def read_material_quantities(self, card_x: int, card_y: int,
                                  card_width: int, card_height: int,
                                  materials: List[dict]) -> List[dict]:
        """
        Read quantities for materials on a task card.
        Looks for red numbers (warehouse stock) below materials and
        the amount needed to the right of "Deliver" text.

        Args:
            card_x, card_y, card_width, card_height: Card bounds
            materials: List of materials found on card

        Returns:
            Updated materials list with 'warehouse_stock' and 'needed' fields
        """
        print("\n=== Reading Material Quantities ===")

        # Find "Deliver" text to get the needed amount
        deliver_match = find_template_on_screen(self.deliver_template, threshold=0.6)
        needed_amount = None

        if deliver_match:
            # Read number to the right of "Deliver"
            # Estimate: number is about 100-150px to the right
            deliver_x = deliver_match['x']
            deliver_y = deliver_match['y']

            # Read needed amount (to the right of deliver)
            needed_x = deliver_x + 150
            needed_y = deliver_y - 5
            needed_amount = self._read_number_from_region(needed_x, needed_y, 80, 30, is_red=False)

            if needed_amount:
                print(f"📋 Task requires: {needed_amount} total materials")
            else:
                print("⚠️  Could not read needed amount")

        # Read warehouse stock for each material (red text below material)
        for mat in materials:
            mat_x = mat['x']
            mat_y = mat['y']
            mat_h = mat['height']

            # Red number is below the material icon
            stock_x = mat_x - 10
            stock_y = mat_y + mat_h + 5
            warehouse_stock = self._read_number_from_region(stock_x, stock_y, 50, 25, is_red=True)

            mat['warehouse_stock'] = warehouse_stock if warehouse_stock is not None else 0
            mat['needed'] = needed_amount

            print(f"  {mat['name']}:")
            print(f"    Warehouse stock: {mat['warehouse_stock']}")
            print(f"    Task needs: {needed_amount}")
            if warehouse_stock is not None and needed_amount is not None:
                if warehouse_stock < needed_amount:
                    print(f"    ⚠️  INSUFFICIENT! Need {needed_amount - warehouse_stock} more")
                else:
                    print(f"    ✓ Sufficient")

        return materials

    def all_materials_available(self, materials: List[dict]) -> bool:
        """
        Check if all materials in the list are available.

        Args:
            materials: List of material dicts

        Returns:
            True if all available, False if any are missing
        """
        if not materials:
            return True  # No materials = all available

        return all(mat['available'] for mat in materials)


def test_material_scanner():
    """Test the material scanner."""
    print("="*60)
    print("Material Scanner Test")
    print("="*60)

    scanner = MaterialScanner()

    if not scanner.material_templates:
        print("\n⚠️  No material templates found!")
        print("Add material PNG files to the 'Materials/' folder")
        return

    print("\nOpen a task with materials visible")
    input("Press ENTER when ready...")

    import time
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Test on a sample card region (adjust these values)
    print("\nScanning sample card region...")
    card_x, card_y = 110, 150
    card_width, card_height = 360, 600

    materials = scanner.find_materials_on_card(card_x, card_y, card_width, card_height)

    print(f"\nFound {len(materials)} material(s)")

    if materials:
        all_available = scanner.all_materials_available(materials)
        print(f"\nAll materials available: {all_available}")

        click_x, click_y = scanner.find_empty_click_area(card_x, card_y,
                                                         card_width, card_height,
                                                         materials)
        print(f"Empty area to click: ({click_x}, {click_y})")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    test_material_scanner()
