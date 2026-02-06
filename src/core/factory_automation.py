#!/usr/bin/env python3
"""
Factory Automation Module

Automates crafting materials in the factory by:
1. Clicking on a material icon (e.g., CopperWire)
2. Clicking the blue button to navigate to factory
3. Detecting missing materials (red text) in the requirements area
4. Using DFS (Depth-First Search) to recursively craft dependencies
5. Crafting materials in correct order (dependencies first)
"""

import cv2
import numpy as np
import pyautogui
import pytesseract
import re
import time
from typing import Optional, Tuple, List, Dict
from pathlib import Path

from src.detectors.template_matcher import find_template_on_screen, get_scale_factor
from src.config.ui_config import UIConfig




class FactoryAutomation:
    """Handles factory crafting workflow."""

    def __init__(self, click_delay: float = 0.5):
        """
        Initialize factory automation.

        Args:
            click_delay: Delay between clicks in seconds
        """
        self.config = UIConfig()
        self.click_delay = click_delay
        self.screen_width, self.screen_height = pyautogui.size()

        # Template paths
        self.confirm_button_template = str(self.config.TEMPLATES_DIR / "buttons" / "ConfirmButton.png")
        self.factory_blue_button_template = str(self.config.TEMPLATES_DIR / "buttons" / "FactoryIconBlueButton.png")
        self.materials_needed_marker_template = str(self.config.TEMPLATES_DIR / "ui" / "TemplateUnderMaterialsNeeded.png")
        self.red_number_template = str(self.config.TEMPLATES_DIR / "ui" / "RedNumber.png")
        self.not_enough_materials_template = str(self.config.TEMPLATES_DIR / "ui" / "NotEnoughMaterialsFactory.png")

        # Store positions for later use
        self.confirm_button_x = None
        self.confirm_button_y = None

        # Sample red color from template for detection
        self.red_color_hsv_lower = None
        self.red_color_hsv_upper = None
        self._sample_red_color_from_template()

        print("Factory Automation initialized")

    def safe_click(self, x: int, y: int, clicks: int = 1):
        """Perform a safe click with delay."""
        pyautogui.click(x, y, clicks=clicks)
        time.sleep(self.click_delay)

    def _sample_red_color_from_template(self):
        """
        Sample the red color from RedNumber.png template.
        Creates HSV range for detecting similar red text in the game.
        """
        print("\n=== Sampling Red Color from Template ===")

        # Load the red number template
        template = cv2.imread(self.red_number_template)
        if template is None:
            print(f"⚠️  RedNumber template not found: {self.red_number_template}")
            print("   Using default red color range")
            # Fallback to default red range
            self.red_color_hsv_lower = np.array([0, 100, 100])
            self.red_color_hsv_upper = np.array([10, 255, 255])
            return

        # Convert to HSV
        hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)

        # Create mask to filter out white/background pixels
        # Red numbers have high saturation and medium-high value
        # Filter: S > 100, V > 100 (ignore white/gray background)
        mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([180, 255, 255]))

        # Get HSV values of red pixels only
        red_pixels = hsv[mask > 0]

        if len(red_pixels) == 0:
            print("⚠️  No red pixels found in template")
            print("   Using default red color range")
            self.red_color_hsv_lower = np.array([0, 100, 100])
            self.red_color_hsv_upper = np.array([10, 255, 255])
            return

        # Calculate median HSV values of red pixels
        median_h = int(np.median(red_pixels[:, 0]))
        median_s = int(np.median(red_pixels[:, 1]))
        median_v = int(np.median(red_pixels[:, 2]))

        print(f"✓ Sampled red color from template:")
        print(f"  Median HSV: H={median_h}, S={median_s}, V={median_v}")
        print(f"  Total red pixels sampled: {len(red_pixels)}")

        # Create range around sampled color with tolerance
        # Hue tolerance: ±15 (red can wrap around 0/180)
        # Saturation tolerance: -50 to keep high saturation
        # Value tolerance: -50 to allow darker shades
        h_tolerance = 15
        s_min = max(0, median_s - 50)
        v_min = max(0, median_v - 50)

        # Red hue wraps around 0/180, so handle both ranges
        if median_h < h_tolerance:
            # Red near 0, create two ranges
            self.red_color_hsv_lower = np.array([0, s_min, v_min])
            self.red_color_hsv_upper = np.array([median_h + h_tolerance, 255, 255])
            print(f"  Range 1: H=[0, {median_h + h_tolerance}], S=[{s_min}, 255], V=[{v_min}, 255]")
        elif median_h > 180 - h_tolerance:
            # Red near 180, create two ranges
            self.red_color_hsv_lower = np.array([median_h - h_tolerance, s_min, v_min])
            self.red_color_hsv_upper = np.array([180, 255, 255])
            print(f"  Range 1: H=[{median_h - h_tolerance}, 180], S=[{s_min}, 255], V=[{v_min}, 255]")
        else:
            # Normal range
            self.red_color_hsv_lower = np.array([median_h - h_tolerance, s_min, v_min])
            self.red_color_hsv_upper = np.array([median_h + h_tolerance, 255, 255])
            print(f"  Range: H=[{median_h - h_tolerance}, {median_h + h_tolerance}], S=[{s_min}, 255], V=[{v_min}, 255]")

    def find_material_icon(self, material_name: str) -> Optional[Tuple[int, int]]:
        """
        Find a material icon on screen.

        Args:
            material_name: Name of the material (e.g., "CopperWire")

        Returns:
            (x, y) coordinates if found, None otherwise
        """
        template_path = str(self.config.TEMPLATES_DIR / "Materials" / f"{material_name}.png")

        if not Path(template_path).exists():
            print(f"❌ Template not found: {template_path}")
            return None

        print(f"Looking for {material_name} icon...")
        match = find_template_on_screen(template_path, threshold=0.7)

        if match:
            print(f"✓ Found {material_name} at ({match['x']}, {match['y']})")
            return (match['x'], match['y'])
        else:
            print(f"❌ {material_name} icon not found")
            return None

    def find_and_click_blue_button(self) -> bool:
        """
        Find and click the factory blue button using template matching.

        Uses the same template matching as test tools - searches entire screen.

        Returns:
            True if button found and clicked, False otherwise
        """
        print("\n=== Looking for Factory Blue Button (Template) ===")
        print("Searching entire screen...")

        # Use the SAME template matching function as test tools
        # Search entire screen (no region parameter)
        match = find_template_on_screen(
            self.factory_blue_button_template,
            threshold=0.7
        )

        if match:
            print(f"✓ Found Factory Blue Button at ({match['x']}, {match['y']})")
            print(f"  Confidence: {match['confidence']:.3f}")

            # Click the button
            self.safe_click(match['x'], match['y'])
            return True
        else:
            print(f"❌ Factory Blue Button not found")
            print(f"  Template: {self.factory_blue_button_template}")
            return False

    def wait_for_confirm_button(self, timeout: float = 5.0) -> bool:
        """
        Wait for the Confirm button to appear (factory UI loaded).
        Saves the button position for later use.

        Searches only in the bottom 40% of screen with 15% padding on sides.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if Confirm button found, False if timeout
        """
        print("\n=== Waiting for Factory UI (Confirm Button) ===")
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")

        # Check scale factor (for Retina/HiDPI displays)
        scale = get_scale_factor()
        print(f"Display scale factor: {scale}x")

        # Define search region: bottom 50% of screen (gives more room for button)
        region_x = int(self.screen_width * 0)  # Full width
        region_y = int(self.screen_height * 0.50)  # Start at 50% down (bottom half)
        region_width = int(self.screen_width)  # Full width
        region_height = int(self.screen_height * 0.50)  # Bottom 50%

        search_region = (region_x, region_y, region_width, region_height)

        print(f"Search region: ({region_x}, {region_y}, {region_width}x{region_height})")
        print(f"  X range: {region_x} to {region_x + region_width}")
        print(f"  Y range: {region_y} to {region_y + region_height}")

        # TEMPORARY FIX: Just use full screen search since region search has issues
        # The region restriction was causing problems with template matching on Retina displays
        # Full screen search is fast anyway since the button is always in the same area
        print("\nSearching for Confirm button (full screen)...")

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout:
            attempt += 1
            if attempt > 1:
                print(f"  Attempt {attempt}...", end='')

            match = find_template_on_screen(self.confirm_button_template, threshold=0.7)
            if match:
                self.confirm_button_x = match['x']
                self.confirm_button_y = match['y']

                print(f"✓ Confirm button found at ({match['x']}, {match['y']}) - confidence {match['confidence']:.3f}")
                return True
            else:
                if attempt > 1:
                    print(" not found")

            time.sleep(0.5)

        print("❌ Confirm button not found (timeout)")
        return False

    def find_material_requirements_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Find the material requirements region using TemplateUnderMaterialsNeeded marker.

        The marker is positioned under the materials needed section.
        Materials are displayed horizontally ABOVE this marker.

        Returns:
            (x, y, width, height) of the requirements region, or None if not found
        """
        print("\n=== Finding Material Requirements Region ===")

        # Find the TemplateUnderMaterialsNeeded marker
        marker_match = find_template_on_screen(self.materials_needed_marker_template, threshold=0.7)

        if not marker_match:
            print("❌ TemplateUnderMaterialsNeeded marker not found")
            return None

        marker_x = marker_match['x']
        marker_y = marker_match['y']

        print(f"✓ TemplateUnderMaterialsNeeded marker found at ({marker_x}, {marker_y})")

        # Materials are displayed on a horizontal line ABOVE this marker
        # Define the region above the marker where materials appear

        # Region width: assume materials span horizontally (use generous width)
        region_width = int(self.screen_width * 0.30)   # 30% of screen width

        # Region height: area above the marker where materials are displayed
        # Reduced to avoid capturing noise below (like "You own: X" text)
        region_height = int(self.screen_height * 0.05)  # 5% of screen height above marker

        # Position: centered on marker horizontally, extends upward from marker
        # Shift up a bit more to focus on just the X/Y numbers
        region_x = marker_x - region_width // 2
        region_y = marker_y - region_height - 20  # Start 20px higher for better text visibility

        # Ensure region is within screen bounds
        region_x = max(0, min(region_x, self.screen_width - region_width))
        region_y = max(0, min(region_y, self.screen_height - region_height))

        print(f"✓ Materials requirements region (above marker):")
        print(f"  Position: ({region_x}, {region_y})")
        print(f"  Size: {region_width}x{region_height}")
        print(f"  (Horizontal line of materials above TemplateUnderMaterialsNeeded)")

        return (region_x, region_y, region_width, region_height)

    def detect_text_in_region(self, region: Tuple[int, int, int, int]) -> List[Dict]:
        """
        Read all text in the materials requirements region using OCR with coordinate detection.

        Uses pytesseract's image_to_data to get bounding boxes for each text clump,
        then splits materials based on large horizontal gaps between them.

        Args:
            region: (x, y, width, height) of the region to search

        Returns:
            List of material requirements with their positions
            [{'text': str, 'x': int, 'y': int, 'width': int, 'height': int}, ...]
        """
        x, y, width, height = region

        print(f"\n=== Reading Text in Materials Region ===")
        print(f"Region: ({x}, {y}, {width}x{height})")

        # Capture the region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Save for debugging
        cv2.imwrite("factory_requirements_region.png", screenshot_bgr)
        print("✓ Saved factory_requirements_region.png")

        # Convert to grayscale
        gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

        # Try multiple preprocessing methods for better OCR
        # Method 1: Simple threshold
        _, simple_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Method 2: Invert for dark text on light background
        inverted = cv2.bitwise_not(gray)

        cv2.imwrite("factory_requirements_adaptive.png", simple_thresh)
        print("✓ Saved factory_requirements_adaptive.png")

        # Use pytesseract image_to_data to get bounding boxes and text
        print("\n=== OCR with Coordinate Detection ===")

        # Try OCR with multiple images to get best results
        best_ocr_data = None
        best_text_count = 0

        for img, method_name in [(screenshot_bgr, "original"), (inverted, "inverted"), (simple_thresh, "threshold")]:
            print(f"  Trying OCR with {method_name} preprocessing...")
            ocr_data = pytesseract.image_to_data(img, config=r'--oem 3 --psm 6',
                                                 output_type=pytesseract.Output.DICT)

            # Count how many valid detections we got
            text_count = 0
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0
                if text and conf > 20:
                    text_count += 1

            print(f"    Found {text_count} text detections")

            if text_count > best_text_count:
                best_text_count = text_count
                best_ocr_data = ocr_data

        print(f"  Using best result with {best_text_count} detections\n")
        ocr_data = best_ocr_data

        # First, print ALL detected text for debugging
        print("DEBUG: All OCR detections:")
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0
            if text:
                print(f"  '{text}' - conf: {conf}, pos: ({ocr_data['left'][i]}, {ocr_data['top'][i]})")

        # Filter valid text detections (confidence > 0 and text not empty)
        text_boxes = []
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0

            # Skip single characters like "|"
            if len(text) <= 1:
                continue

            # Only keep text that looks like material requirements (contains digits)
            if text and conf > 30 and any(char.isdigit() for char in text):
                # Post-process OCR errors
                text = self._fix_ocr_errors(text)

                # Only keep if it looks like X/Y format after fixing
                if '/' in text and re.search(r'\d+\s*/\s*\d+', text):
                    box = {
                        'text': text,
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'conf': conf
                    }
                    text_boxes.append(box)
                    print(f"  ✓ Accepted after fixing: '{text}'")

        if not text_boxes:
            print("❌ No valid X/Y format text detected")
            return []

        # Sort by x-coordinate (left to right)
        text_boxes.sort(key=lambda b: b['x'])

        print(f"✓ Found {len(text_boxes)} text clump(s)")

        # Group text boxes that are close together (same material requirement)
        # Split when horizontal gap is large (>15px = different material)
        materials = []
        current_group = []

        for i, box in enumerate(text_boxes):
            if not current_group:
                # First box
                current_group.append(box)
            else:
                # Check horizontal gap from previous box
                prev_box = current_group[-1]
                gap = box['x'] - (prev_box['x'] + prev_box['width'])

                if gap > 15:  # Large gap = new material (reduced to 15px)
                    # Merge current group into one material
                    merged = self._merge_text_boxes(current_group)
                    materials.append(merged)
                    current_group = [box]
                else:
                    # Same material, add to group
                    current_group.append(box)

        # Add last group
        if current_group:
            merged = self._merge_text_boxes(current_group)
            materials.append(merged)

        # Print each material requirement with position
        print("\n=== Detected Material Requirements ===")
        for i, mat in enumerate(materials, 1):
            print(f"Material {i}: '{mat['text']}' at position ({mat['x']}, {mat['y']}) "
                  f"[{mat['width']}x{mat['height']}]")

        return materials

    def _merge_text_boxes(self, boxes: List[Dict]) -> Dict:
        """
        Merge multiple text boxes into one material requirement.

        Args:
            boxes: List of text box dicts with 'text', 'x', 'y', 'width', 'height'

        Returns:
            Single merged dict with combined text and bounding box
        """
        if len(boxes) == 1:
            return boxes[0]

        # Combine text (space-separated)
        combined_text = ' '.join(box['text'] for box in boxes)

        # Calculate bounding box that encompasses all boxes
        min_x = min(box['x'] for box in boxes)
        min_y = min(box['y'] for box in boxes)
        max_x = max(box['x'] + box['width'] for box in boxes)
        max_y = max(box['y'] + box['height'] for box in boxes)

        return {
            'text': combined_text,
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y,
            'conf': sum(box['conf'] for box in boxes) / len(boxes)  # Average confidence
        }

    def _fix_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors in material requirement text.

        Common errors:
        - "24180" → "24/80" (missing slash)
        - "T2430" → "72/30" (T instead of 7, missing slash)
        - "l" → "1" (lowercase L)
        - "O" → "0" (letter O)

        Args:
            text: Raw OCR text

        Returns:
            Corrected text in X/Y format
        """
        original = text

        # Fix common character substitutions first
        text = text.replace('T', '7')  # T is often misread 7
        text = text.replace('l', '1')  # lowercase L is often 1
        text = text.replace('I', '1')  # uppercase I is often 1
        text = text.replace('O', '0')  # letter O is often 0

        # After character fixes, handle concatenated numbers
        # Pattern: sequence of digits without slash (like "24180" or "7230")
        if '/' not in text and len(text) >= 4 and text.isdigit():
            # Split at position to make XX/XX or X/XX pattern
            # Try XX/XX first (most common: 2 digits / 2 digits)
            if len(text) == 4:
                text = text[:2] + '/' + text[2:]
            elif len(text) == 5:
                # Could be XX/XXX or XXX/XX, try both and see which makes sense
                # For now, assume XX/XXX (e.g., "24180" → "24/180")
                text = text[:2] + '/' + text[2:]
            else:
                # General case: split in middle
                mid = len(text) // 2
                text = text[:mid] + '/' + text[mid:]

            print(f"  Fixed concatenated numbers: '{original}' → '{text}'")

        return text

    def _needs_material(self, material: Dict) -> bool:
        """
        Check if a material is needed (X < Y in X/Y format).

        Args:
            material: Dict with 'text' key containing material requirement like "5/10"

        Returns:
            True if material is needed (X < Y), False otherwise
        """
        text = material['text'].strip()

        # Try to parse X/Y format
        match = re.search(r'(\d+)\s*/\s*(\d+)', text)

        if not match:
            print(f"  ⚠️  Could not parse '{text}' as X/Y format")
            return False

        current = int(match.group(1))
        required = int(match.group(2))

        print(f"  Parsed '{text}' → Current: {current}, Required: {required}", end='')

        if current < required:
            print(f" → NEEDS CRAFTING (missing {required - current})")
            return True
        else:
            print(f" → OK (sufficient)")
            return False

    def click_confirm_button(self) -> bool:
        """
        Click the Confirm button using the saved position.

        Returns:
            True if position saved and clicked, False otherwise
        """
        if self.confirm_button_x is None or self.confirm_button_y is None:
            print("❌ Confirm button position not saved")
            return False

        print(f"\n=== Clicking Confirm Button ===")
        print(f"Position: ({self.confirm_button_x}, {self.confirm_button_y})")

        self.safe_click(self.confirm_button_x, self.confirm_button_y)
        return True

    def check_for_not_enough_materials_popup(self) -> bool:
        """
        Check if "Not Enough Materials" popup appeared after clicking confirm.

        This popup appears in the center of the screen when materials are missing.

        Returns:
            True if popup found, False otherwise
        """
        # Search in center region of screen for the popup
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        search_width = int(self.screen_width * 0.4)
        search_height = int(self.screen_height * 0.4)

        region = (
            center_x - search_width // 2,
            center_y - search_height // 2,
            search_width,
            search_height
        )

        match = find_template_on_screen(
            self.not_enough_materials_template,
            threshold=0.7,
            region=region
        )

        return match is not None

    def click_above_red_text(self, red_text_location: Dict, offset_y: int = 30) -> bool:
        """
        Click above a red text location (to click on the material icon).

        Args:
            red_text_location: Dict with 'x', 'y', 'text' keys
            offset_y: How many pixels above the text to click

        Returns:
            True if clicked successfully
        """
        click_x = red_text_location['x']
        click_y = red_text_location['y'] - offset_y

        print(f"\n=== Clicking Above Red Text ===")
        print(f"Red text: '{red_text_location['text']}' at ({red_text_location['x']}, {red_text_location['y']})")
        print(f"Clicking at: ({click_x}, {click_y}) (offset: -{offset_y}px)")

        self.safe_click(click_x, click_y)
        return True

    def craft_material_dfs(self, click_x: int, click_y: int, depth: int = 0) -> bool:
        """
        Recursively craft a material using DFS approach.

        This function:
        1. Navigates to the material's crafting screen
        2. Detects missing materials
        3. For each missing material, recursively calls itself (DFS - go deep first)
        4. Once all dependencies are satisfied, clicks confirm to craft
        5. Presses ESC to go back

        Args:
            click_x: X coordinate to click to select this material
            click_y: Y coordinate to click to select this material
            depth: Current recursion depth (for logging)

        Returns:
            True if crafted successfully, False if error
        """
        indent = "  " * depth
        print(f"\n{indent}{'='*60}")
        print(f"{indent}DFS Depth {depth}: Crafting Material at ({click_x}, {click_y})")
        print(f"{indent}{'='*60}")

        # Navigate to this material's crafting screen
        print(f"{indent}Clicking material at ({click_x}, {click_y})...")
        self.safe_click(click_x, click_y)
        time.sleep(1.0)

        # Click blue button to navigate to factory
        print(f"{indent}Navigating to factory...")
        if not self.find_and_click_blue_button():
            print(f"{indent}❌ Failed to click blue button")
            return False
        time.sleep(2.0)

        # Wait for factory UI (Confirm button)
        print(f"{indent}Waiting for factory UI...")
        if not self.wait_for_confirm_button():
            return False

        # Save confirm button position
        confirm_x = self.confirm_button_x
        confirm_y = self.confirm_button_y
        print(f"{indent}✓ Confirm button at ({confirm_x}, {confirm_y})")

        # Find material requirements region
        requirements_region = self.find_material_requirements_region()
        if not requirements_region:
            return False

        # Read materials with OCR
        materials = self.detect_text_in_region(requirements_region)

        # Check for missing materials
        missing_materials = []

        if not materials:
            print(f"{indent}✓ No materials detected (can craft immediately)")
        else:
            # Extract region coordinates for screen conversion
            region_x, region_y, region_width, region_height = requirements_region

            # Check each material and store missing ones
            for mat in materials:
                if self._needs_material(mat):
                    # Calculate screen coordinates (center of text)
                    screen_x = region_x + mat['x'] + mat['width'] // 2
                    screen_y = region_y + mat['y'] + mat['height'] // 2

                    # Click position is 50px above the text (where material icon is)
                    click_x_dep = screen_x
                    click_y_dep = screen_y - 50

                    missing_materials.append({
                        'text': mat['text'],
                        'click_x': click_x_dep,
                        'click_y': click_y_dep
                    })

            if missing_materials:
                print(f"{indent}✓ Found {len(missing_materials)} missing material(s)")
            else:
                print(f"{indent}✓ All materials available")

        # DFS: Recursively craft missing materials first (depth-first)
        if missing_materials:
            print(f"{indent}→ Crafting dependencies first (DFS)...")
            for i, dep in enumerate(missing_materials, 1):
                print(f"{indent}→ Dependency {i}/{len(missing_materials)}: {dep['text']}")

                # Recursively craft this dependency (DFS - go deeper)
                # No ESC needed - we click the material directly from current factory screen
                if not self.craft_material_dfs(dep['click_x'], dep['click_y'], depth + 1):
                    return False

                # After crafting dependency (which pressed ESC), we're back at current material's screen
                # Need to navigate back to factory to check remaining dependencies
                if i < len(missing_materials):  # If more dependencies remaining
                    print(f"{indent}  → Returning to parent factory at depth {depth}...")
                    print(f"{indent}  Clicking material at ({click_x}, {click_y})...")
                    self.safe_click(click_x, click_y)
                    time.sleep(1.0)

                    print(f"{indent}  Navigating to factory...")
                    if not self.find_and_click_blue_button():
                        print(f"{indent}  ❌ Failed to click blue button")
                        return False
                    time.sleep(2.0)

                    print(f"{indent}  Waiting for factory UI...")
                    if not self.wait_for_confirm_button():
                        return False
                else:
                    # Last dependency - need to return to factory for final confirm
                    print(f"{indent}  → Last dependency done, returning to parent factory...")
                    print(f"{indent}  Clicking material at ({click_x}, {click_y})...")
                    self.safe_click(click_x, click_y)
                    time.sleep(1.0)

                    print(f"{indent}  Navigating to factory...")
                    if not self.find_and_click_blue_button():
                        print(f"{indent}  ❌ Failed to click blue button")
                        return False
                    time.sleep(2.0)

                    print(f"{indent}  Waiting for factory UI...")
                    if not self.wait_for_confirm_button():
                        return False

            print(f"{indent}✅ All dependencies crafted")

        # All dependencies satisfied, now craft this material
        print(f"{indent}✓ All materials satisfied, crafting now...")
        print(f"{indent}Clicking confirm at ({confirm_x}, {confirm_y})...")
        self.safe_click(confirm_x, confirm_y)
        time.sleep(1.0)  # Wait for popup to appear (if any)

        # FAILSAFE: Check if "Not Enough Materials" popup appeared
        print(f"{indent}Checking for 'Not Enough Materials' popup (failsafe)...")
        if self.check_for_not_enough_materials_popup():
            print(f"{indent}⚠️  'Not Enough Materials' popup detected!")
            print(f"{indent}   OCR likely missed some dependencies. Retrying...")

            # Press ESC to close popup
            print(f"{indent}   Pressing ESC to close popup...")
            pyautogui.press('esc')
            time.sleep(0.5)

            # Re-detect materials with more aggressive settings
            print(f"{indent}   Re-running OCR detection...")
            requirements_region = self.find_material_requirements_region()
            if not requirements_region:
                return False

            materials = self.detect_text_in_region(requirements_region)

            # Rebuild missing materials list
            missing_materials_retry = []
            region_x, region_y, region_width, region_height = requirements_region

            for mat in materials:
                if self._needs_material(mat):
                    screen_x = region_x + mat['x'] + mat['width'] // 2
                    screen_y = region_y + mat['y'] + mat['height'] // 2
                    click_x_dep = screen_x
                    click_y_dep = screen_y - 50

                    missing_materials_retry.append({
                        'text': mat['text'],
                        'click_x': click_x_dep,
                        'click_y': click_y_dep
                    })

            if missing_materials_retry:
                print(f"{indent}   Found {len(missing_materials_retry)} missing materials on retry")

                # Craft the missing dependencies
                for i, dep in enumerate(missing_materials_retry, 1):
                    print(f"{indent}   → Retry Dependency {i}/{len(missing_materials_retry)}: {dep['text']}")

                    if not self.craft_material_dfs(dep['click_x'], dep['click_y'], depth + 1):
                        return False

                    # Navigate back to current material
                    if i < len(missing_materials_retry) or True:  # Always navigate back
                        print(f"{indent}     → Returning to parent factory...")
                        self.safe_click(click_x, click_y)
                        time.sleep(1.0)

                        if not self.find_and_click_blue_button():
                            return False
                        time.sleep(2.0)

                        if not self.wait_for_confirm_button():
                            return False

                # Try confirming again
                print(f"{indent}   Clicking confirm again after crafting missed dependencies...")
                self.safe_click(confirm_x, confirm_y)
                time.sleep(1.5)
            else:
                print(f"{indent}   ⚠️  No materials detected on retry either!")
                return False

        print(f"{indent}✅ Crafted successfully at depth {depth}")

        # Press ESC to go back (unless this is the root material)
        if depth > 0:
            print(f"{indent}Pressing ESC to return to parent...")
            pyautogui.press('esc')
            time.sleep(0.5)

        return True

    def craft_material(self, material_name: str) -> bool:
        """
        Main workflow to craft a material using DFS approach.

        Uses depth-first search to recursively craft dependencies before parent materials.

        Args:
            material_name: Name of the material to craft (e.g., "CopperWire")

        Returns:
            True if successful, False otherwise
        """
        print("\n" + "="*60)
        print(f"Factory Crafting: {material_name} (DFS)")
        print("="*60)

        workflow_start = time.time()

        # Find root material icon
        print("\n=== Finding Root Material ===")
        material_coords = self.find_material_icon(material_name)
        if not material_coords:
            return False

        print(f"✓ Material found at ({material_coords[0]}, {material_coords[1]})")

        # Start DFS recursive crafting from root material
        if not self.craft_material_dfs(material_coords[0], material_coords[1], depth=0):
            print("❌ Failed to craft material")
            return False

        print(f"\n⏱️  TOTAL workflow time: {time.time() - workflow_start:.1f}s")
        print("✅ Crafting completed successfully!")
        return True


def test_factory_automation():
    """Test the factory automation with CopperWire."""
    print("="*60)
    print("Factory Automation Test")
    print("="*60)
    print("\nThis will test the factory workflow:")
    print("1. Find and click CopperWire material icon")
    print("2. Click blue button to go to factory")
    print("3. Detect red text (missing materials)")
    print("4. Click above first red text")
    print()

    input("Position game and press ENTER to start...")

    print("\nStarting in 3 seconds...")
    time.sleep(3)

    factory = FactoryAutomation()
    success = factory.craft_material("CopperWire")

    if success:
        print("\n✅ Test completed!")
    else:
        print("\n❌ Test failed")


if __name__ == "__main__":
    test_factory_automation()
