#!/usr/bin/env python3
"""
Task Automation Main Script
Automates the workflow:
1. Click Task button
2. Click FullTask (first available task)
3. Scan materials and detect insufficient ones (red numbers)
4. Queue materials that need collection
5. Navigate to warehouse for each material
6. Return after collection
"""

import time
import pyautogui
from typing import List, Optional, Tuple
from pathlib import Path

from template_matcher import find_template_on_screen, find_all_matches
from ui_config import UIConfig
from color_detector import ColorDetector
from operator_checker import OperatorChecker
from resource_collector import ResourceCollector
from resource_generator import ResourceGenerator
from task_card_detector import TaskCardDetector
from material_scanner import MaterialScanner
from train_dispatcher import TrainDispatcher


class TaskAutomation:
    """Main automation controller."""

    def __init__(self, click_delay: float = 0.5):
        """
        Initialize the automation system.

        Args:
            click_delay: Delay between clicks in seconds
        """
        self.config = UIConfig()
        self.color_detector = ColorDetector()
        self.operator_checker = OperatorChecker()
        self.resource_collector = ResourceCollector()
        self.resource_generator = ResourceGenerator()
        self.task_card_detector = TaskCardDetector()
        self.material_scanner = MaterialScanner()
        self.train_dispatcher = TrainDispatcher()
        self.click_delay = click_delay
        self.available_operators = 0  # Track how many operators we have

        # Safety feature: enable fail-safe (move mouse to corner to abort)
        pyautogui.FAILSAFE = True

        print("Task Automation initialized")
        print("Move mouse to top-left corner to emergency stop")

    def safe_click(self, x: int, y: int, clicks: int = 1):
        """Perform a safe click with delay."""
        pyautogui.click(x, y, clicks=clicks)
        time.sleep(self.click_delay)

    def locate_and_click(self, element_name: str, threshold: float = 0.8) -> bool:
        """
        Locate a UI element and click it.

        Args:
            element_name: Name of the element in UIConfig
            threshold: Match confidence threshold

        Returns:
            True if found and clicked, False otherwise
        """
        element = self.config.get_element(element_name)
        if not element:
            print(f"Error: Element '{element_name}' not found in config")
            return False

        print(f"Searching for {element_name}...")
        match = find_template_on_screen(element.template_path, threshold)

        if match:
            print(f"Found {element_name} at ({match['x']}, {match['y']}) "
                  f"with {match['confidence']:.2%} confidence")

            # Update config with found coordinates
            self.config.update_element(element_name, match)

            # Click the element
            self.safe_click(match['x'], match['y'])
            return True
        else:
            print(f"Could not find {element_name}")
            return False

    def open_task_menu(self) -> bool:
        """Click on the Task button."""
        print("\n=== Step 1: Opening Task Menu ===")
        return self.locate_and_click("task_button")

    def select_full_task(self) -> bool:
        """Click on the FullTask (first available task)."""
        print("\n=== Selecting Task ===")

        # Check if we have a pre-determined next task position
        if hasattr(self, '_next_task_coords') and self._next_task_coords:
            task_x, task_y = self._next_task_coords
            print(f"Clicking pre-selected available task at ({task_x}, {task_y})")
            self.safe_click(task_x, task_y)
            return True

        # Fallback: Get Task button position as reference
        task_coords = self.config.get_coordinates("task_button")

        if task_coords:
            # FullTask should be about 50 pixels to the right of Task button
            fulltask_x = task_coords[0] + 50
            fulltask_y = task_coords[1]
            print(f"Clicking task at estimated position ({fulltask_x}, {fulltask_y})")
            print(f"  (50 pixels right of Task button)")
            self.safe_click(fulltask_x, fulltask_y)
            return True

        # Last resort: try template matching
        print("No task reference, trying template matching...")
        if self.locate_and_click("full_task", threshold=0.7):
            return True

        print("Could not locate task")
        return False

    def scan_materials(self) -> List[Tuple[int, int]]:
        """
        Scan for all material icons on screen.

        Returns:
            List of (x, y) coordinates for each material icon found
        """
        print("\n=== Step 3: Scanning Materials ===")

        element = self.config.get_element("material_icon")
        if not element:
            print("Error: material_icon not found in config")
            return []

        matches = find_all_matches(element.template_path, threshold=0.75)
        print(f"Found {len(matches)} material icons")

        material_coords = [(m['x'], m['y']) for m in matches]
        return material_coords

    def check_material_sufficiency(self, material_coords: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Check which materials are insufficient (have red numbers).

        Args:
            material_coords: List of material icon coordinates

        Returns:
            List of (x, y) coordinates for materials with red (insufficient) numbers
        """
        print("\n=== Step 4: Checking Material Sufficiency ===")

        insufficient = []

        for i, (x, y) in enumerate(material_coords):
            status = self.color_detector.detect_material_status(x, y)
            print(f"Material {i+1} at ({x}, {y}): {status}")

            if status == 'insufficient':
                insufficient.append((x, y))

        print(f"Found {len(insufficient)} insufficient materials")
        return insufficient

    # OLD METHOD - NOT USED ANYMORE (replaced by color-based detection)
    # def create_material_queue(self, insufficient_coords: List[Tuple[int, int]]):
    #     """
    #     Create a queue of materials that need to be collected.
    #     Also captures icon images for each material.
    #
    #     Args:
    #         insufficient_coords: Coordinates of materials that are insufficient
    #     """
    #     pass  # Old implementation removed - now using _find_material_numbers()

    def close_task_dialog(self) -> bool:
        """
        Press X button to close the task dialog.
        This is done after checking materials, before going to warehouse.
        """
        print("\n=== Closing Task Dialog ===")
        # Implement X button detection and click
        # For now, using ESC key as fallback
        pyautogui.press('esc')
        time.sleep(self.click_delay)
        return True

    def open_warehouse(self) -> bool:
        """Navigate to the warehouse."""
        print("\n=== Step 6: Opening Warehouse ===")
        return self.locate_and_click("storage")

    # OLD METHODS - NOT USED ANYMORE (replaced by color-based detection)
    # These methods used the old Material class and queue system
    # Now we use _find_material_numbers() which detects black/red text

    # def find_material_in_warehouse(self, material, max_scrolls: int = 5):
    #     pass  # Old implementation removed

    # def collect_material(self, material):
    #     pass  # Old implementation removed

    # def process_material_queue(self):
    #     pass  # Old implementation removed

    def get_task_card_bounds_from_click(self, click_x: int, click_y: int) -> Tuple[int, int, int, int]:
        """
        Get the task card bounds from a click position.
        Uses the task card detector's fixed grid to determine the card region.

        Args:
            click_x, click_y: Click position on a task card

        Returns:
            (x, y, width, height) of the task card region
        """
        # Get all task card positions from detector
        cards = self.task_card_detector.find_task_cards()

        # Find which card contains the click position
        for card_x, card_y, card_w, card_h in cards:
            # Check if click position is within this card
            if (card_x <= click_x <= card_x + card_w and
                card_y <= click_y <= card_y + card_h):
                return (card_x, card_y, card_w, card_h)

        # Default: return estimated card bounds around click position
        # (fallback if click is outside detected cards)
        card_width = 360
        card_height = 600
        estimated_x = click_x - card_width // 2
        estimated_y = 150  # Standard y position
        return (estimated_x, estimated_y, card_width, card_height)

    def _find_and_click_blue_button(self) -> bool:
        """
        Find and click the blue button in the material popup.
        The button is always blue but has varying text.

        Returns:
            True if button found and clicked, False otherwise
        """
        print("\n=== Looking for Blue Button ===")

        import cv2
        import numpy as np

        # Capture screen
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2HSV)

        # Blue color range (the button is a bright blue)
        lower_blue = np.array([90, 100, 150])   # H, S, V
        upper_blue = np.array([130, 255, 255])

        # Create mask for blue areas
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Find contours of blue regions
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get scale factor
        from template_matcher import get_scale_factor
        scale_factor = get_scale_factor()

        # Find largest blue region (should be the button)
        if contours:
            # Sort by area, largest first
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours[:3]:  # Check top 3 largest blue regions
                area = cv2.contourArea(contour)

                # Button should be reasonably large (at least 10000 pixels in screenshot)
                if area < 10000:
                    continue

                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)

                # Button should be wider than tall (rectangular)
                aspect_ratio = w / h
                if aspect_ratio < 1.5:  # Should be at least 1.5x wider than tall
                    continue

                # Calculate center position (accounting for scale factor)
                center_x = int((x + w // 2) / scale_factor)
                center_y = int((y + h // 2) / scale_factor)

                print(f"Found blue button: size={w}x{h}, area={area}, at ({center_x}, {center_y})")

                # Click the button
                self.safe_click(center_x, center_y)
                return True

        print("❌ Blue button not found")
        return False

    def _dispatch_trains_for_material_generation(self, deliver_amount, warehouse_stock):
        """
        Dispatch trains to generate materials until we have enough.
        Uses average train capacity instead of OCR for each train.

        Args:
            deliver_amount: Amount needed for the task
            warehouse_stock: Current amount in warehouse (red number value)

        Returns:
            bool: True if enough material generated, False otherwise
        """
        from detection_config import AVERAGE_TRAIN_CAPACITY

        # Calculate how much we need to generate
        material_needed = deliver_amount - warehouse_stock
        print(f"\n📊 Material needed: {material_needed} (Deliver: {deliver_amount}, Stock: {warehouse_stock})")

        if material_needed <= 0:
            print("✅ Warehouse has enough stock already!")
            return True

        # First, check for and click any Collect buttons
        # (Materials ready to collect from previous trains)
        print("\n=== Checking for Collect Buttons (Material Generation) ===")
        collect_count = 0
        max_collect_attempts = 10  # Safety limit

        for attempt in range(max_collect_attempts):
            print(f"Attempt {attempt + 1}/{max_collect_attempts}...")

            # Try task context first (most likely for material generation)
            collect_button = self.resource_collector.find_collect_button(context="task")

            # If not found, try operator context as fallback
            if not collect_button:
                print("  Trying operator context as fallback...")
                collect_button = self.resource_collector.find_collect_button(context="operator")

            if collect_button:
                print(f"✓ Found Collect button {collect_count + 1}, clicking...")
                self.safe_click(collect_button[0], collect_button[1])
                collect_count += 1
                time.sleep(0.5)  # Wait for next collect button to appear
            else:
                # No more collect buttons
                print("No collect buttons found with either template")
                break

        if collect_count > 0:
            print(f"✅ Collected {collect_count} material batch(es)")
            print("   (Materials collected, will re-check what's still needed)")
            time.sleep(1.0)
        else:
            print("ℹ️  No collect buttons found, proceeding to dispatch trains")

        material_generated = 0
        train_count = 0
        max_trains = 10  # Safety limit

        print(f"\n🚂 Starting train dispatch loop to generate {material_needed} units")
        print(f"   Using average train capacity: {AVERAGE_TRAIN_CAPACITY}")

        while material_generated < material_needed and train_count < max_trains:
            train_count += 1

            print(f"\n🚂 Train #{train_count}: Estimated capacity = {AVERAGE_TRAIN_CAPACITY}")
            print(f"   Progress: {material_generated}/{material_needed} units generated")

            # Click the first train (we don't need to detect its exact position with OCR)
            # Just click in the first train area
            screen_width, screen_height = pyautogui.size()

            # Use train detection zone from config to click first train
            from detection_config import (TRAIN_CAPACITY_ZONE_TOP, TRAIN_CAPACITY_ZONE_BOTTOM,
                                          TRAIN_CAPACITY_ZONE_LEFT, TRAIN_CAPACITY_ZONE_RIGHT)

            # Calculate center of first train zone
            train_x = int(screen_width * ((TRAIN_CAPACITY_ZONE_LEFT + TRAIN_CAPACITY_ZONE_RIGHT) / 2))
            train_y = int(screen_height * ((TRAIN_CAPACITY_ZONE_TOP + TRAIN_CAPACITY_ZONE_BOTTOM) / 2))

            print(f"   Clicking first train at ({train_x}, {train_y})")
            self.safe_click(train_x, train_y)
            time.sleep(0.5)  # Wait for train details to appear

            # Click the Dispatch button
            if self.train_dispatcher.dispatch_train():
                print(f"   ✓ Train {train_count} dispatched successfully")

                # Update progress using average capacity
                material_generated += AVERAGE_TRAIN_CAPACITY
                print(f"   ✓ Total generated (estimated): {material_generated}/{material_needed}")

                # Check if we have enough
                if material_generated >= material_needed:
                    print(f"\n✅ Enough material generated! ({material_generated} >= {material_needed})")
                    break

                # Wait for next train to move into position
                print("   ⏳ Waiting for next train to appear...")
                time.sleep(1.5)
            else:
                print(f"   ❌ Failed to dispatch train {train_count}")
                print("   Stopping dispatch attempts")
                break

        if material_generated >= material_needed:
            print(f"\n✅ Material generation complete!")
            print(f"   Trains sent: {train_count}")
            print(f"   Material generated: {material_generated}")
            return True
        else:
            print(f"\n⚠️  Material generation incomplete")
            print(f"   Trains sent: {train_count}")
            print(f"   Material generated: {material_generated}/{material_needed}")
            return False

    def _ocr_number(self, roi, debug_index=0):
        """
        Use OCR to read number from text region.

        Args:
            roi: OpenCV image region containing the number
            debug_index: Index for debug output naming

        Returns:
            Integer value of the number, or None if not readable
        """
        try:
            import pytesseract
        except ImportError:
            return None

        try:
            import cv2
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

            # Return most common result, or first valid one
            if results:
                result = max(set(results), key=results.count)
                return result
            return None
        except Exception:
            return None

    def _find_deliver_amount(self, card_x, card_y, card_w, card_h):
        """
        Find DELIVER amount (how much material needed for task).

        Returns:
            Integer amount or None
        """
        import cv2
        import numpy as np
        from detection_config import (DELIVER_ZONE_START, DELIVER_ZONE_END,
                                      DELIVER_ZONE_LEFT, DELIVER_ZONE_RIGHT,
                                      BLACK_TEXT_MAX, NUMBER_MIN_WIDTH, NUMBER_MAX_WIDTH,
                                      NUMBER_MIN_HEIGHT, NUMBER_MAX_HEIGHT)

        # Focus on DELIVER area (right side of card, below material icons)
        deliver_y_start = int(card_h * DELIVER_ZONE_START)
        deliver_y_end = int(card_h * DELIVER_ZONE_END)
        deliver_height = deliver_y_end - deliver_y_start

        deliver_x_start = int(card_w * DELIVER_ZONE_LEFT)
        deliver_x_end = int(card_w * DELIVER_ZONE_RIGHT)
        deliver_width = deliver_x_end - deliver_x_start

        # Capture the DELIVER region (right side only)
        screenshot = pyautogui.screenshot(region=(
            card_x + deliver_x_start,
            card_y + deliver_y_start,
            deliver_width,
            deliver_height
        ))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        # Detect black text
        black_mask = cv2.inRange(gray, 0, BLACK_TEXT_MAX)

        # Find contours
        contours, _ = cv2.findContours(black_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get valid boxes
        valid_boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h < NUMBER_MIN_HEIGHT or h > NUMBER_MAX_HEIGHT:
                continue
            valid_boxes.append([x, y, w, h])

        if not valid_boxes:
            return None

        # Sort and merge
        valid_boxes.sort(key=lambda b: b[0])
        merged_boxes = []
        current_box = valid_boxes[0]

        for next_box in valid_boxes[1:]:
            curr_x, curr_y, curr_w, curr_h = current_box
            next_x, next_y, next_w, next_h = next_box
            y_diff = abs(curr_y - next_y)
            x_gap = next_x - (curr_x + curr_w)
            avg_width = (curr_w + next_w) / 2

            if y_diff < 5 and x_gap < avg_width * 1.5:
                new_x = curr_x
                new_y = min(curr_y, next_y)
                new_w = (next_x + next_w) - curr_x
                new_h = max(curr_h, next_h)
                current_box = [new_x, new_y, new_w, new_h]
            else:
                merged_boxes.append(current_box)
                current_box = next_box

        merged_boxes.append(current_box)

        # Process first merged box (should be DELIVER number)
        for x, y, w, h in merged_boxes:
            if w < NUMBER_MIN_WIDTH or w > NUMBER_MAX_WIDTH * 3:
                continue

            # Extract ROI for OCR (with padding)
            padding = 2
            roi_x = max(0, x - padding)
            roi_y = max(0, y - padding)
            roi_w = min(region.shape[1] - roi_x, w + 2 * padding)
            roi_h = min(region.shape[0] - roi_y, h + 2 * padding)
            text_roi = region[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

            # OCR to read the number
            deliver_amount = self._ocr_number(text_roi, debug_index=0)
            return deliver_amount

        return None

    def _find_material_numbers(self, card_x, card_y, card_w, card_h):
        """
        Find material numbers (black/red text) in task card.
        Black numbers = current inventory amount
        Red numbers = warehouse stock low

        Returns:
            List of dicts with 'x', 'y', 'is_red', 'value' keys
        """
        import cv2
        import numpy as np
        from detection_config import (MATERIAL_ZONE_START, MATERIAL_ZONE_END,
                                      BLACK_TEXT_MAX, NUMBER_MIN_WIDTH, NUMBER_MAX_WIDTH,
                                      NUMBER_MIN_HEIGHT, NUMBER_MAX_HEIGHT)

        # Focus on material area
        material_y_start = int(card_h * MATERIAL_ZONE_START)
        material_y_end = int(card_h * MATERIAL_ZONE_END)
        material_height = material_y_end - material_y_start

        # Capture region
        screenshot = pyautogui.screenshot(region=(
            card_x, card_y + material_y_start, card_w, material_height
        ))
        region = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        # Detect black text
        black_mask = cv2.inRange(gray, 0, BLACK_TEXT_MAX)

        # Detect red text
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)

        # Combine masks
        text_mask = cv2.bitwise_or(black_mask, red_mask)

        # Find contours
        contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        number_positions = []
        for idx, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)

            # Filter by size
            if w < NUMBER_MIN_WIDTH or w > NUMBER_MAX_WIDTH or h < NUMBER_MIN_HEIGHT or h > NUMBER_MAX_HEIGHT:
                continue

            # Check if red or black
            text_roi = region[y:y+h, x:x+w]
            hsv_roi = cv2.cvtColor(text_roi, cv2.COLOR_BGR2HSV)
            red_pixels = cv2.countNonZero(cv2.bitwise_or(
                cv2.inRange(hsv_roi, lower_red1, upper_red1),
                cv2.inRange(hsv_roi, lower_red2, upper_red2)
            ))
            total_pixels = text_roi.shape[0] * text_roi.shape[1]
            is_red = (red_pixels / total_pixels) > 0.3

            # OCR to read the number (current inventory amount)
            number_value = self._ocr_number(text_roi, debug_index=idx)

            # Convert to absolute coordinates
            abs_x = card_x + x + w // 2
            abs_y = card_y + material_y_start + y + h // 2

            number_positions.append({
                'x': abs_x,
                'y': abs_y,
                'is_red': is_red,
                'value': number_value  # Current inventory amount
            })

        return number_positions

    def run_full_workflow(self):
        """Execute the complete automation workflow."""
        print("\n" + "="*60)
        print("Starting Task Automation Workflow")
        print("="*60)

        try:
            # Step 0: Check if operators are available
            print("\n=== Step 0: Checking Operator Availability ===")
            if not self.operator_checker.has_available_operators():
                print("❌ No operators available - all are occupied")

                # Try to read when next operator will be available
                wait_time = self.operator_checker.read_next_operator_timer()
                if wait_time:
                    minutes = wait_time // 60
                    seconds = wait_time % 60
                    print(f"⏱️  Next operator available in: {minutes}m {seconds}s")
                    return False  # Signal to retry later
                else:
                    print("⏱️  Could not read timer - will retry in 60 seconds")
                    return False  # Signal to retry later

            # Get the count of available operators for train dispatching
            self.available_operators = self.operator_checker.get_available_operator_count()
            print(f"Will dispatch trains for {self.available_operators} operator(s)")

            # Step 1: Open task menu
            if not self.open_task_menu():
                print("Failed to open task menu")
                return False

            # Wait for task menu to open
            time.sleep(1.0)

            # Step 1.5: Check if first task has a Collect button (completed task)
            print("\n=== Checking for Completed Task ===")
            from template_matcher import find_template_on_screen

            collect_tasks_template = "Templates/CollectButtonTasks.png"
            collect_match = find_template_on_screen(collect_tasks_template, threshold=0.6)

            if collect_match:
                print(f"✓ Found completed task with Collect button at ({collect_match['x']}, {collect_match['y']})")
                print("Clicking to collect from completed task...")
                self.safe_click(collect_match['x'], collect_match['y'])

                # Wait for collection
                time.sleep(3.0)

                print("Clicking first task again to open it...")
                # Click the first task position (should be roughly where collect button was)
                # Use the task card detector to get the first card position
                cards = self.task_card_detector.find_task_cards()
                if cards:
                    first_card_x, first_card_y, first_card_w, first_card_h = cards[0]
                    # Click on the first card (center)
                    click_x = first_card_x + first_card_w // 2
                    click_y = first_card_y + first_card_h // 3
                    self.safe_click(click_x, click_y)
                    time.sleep(1.0)
                    print("✅ Completed task collected and reopened")
            else:
                print("No completed task collect button found")

            # Step 1.5: Find next available task using task card detector
            print("\n=== Finding Next Available Task ===")
            available_task = self.task_card_detector.find_first_available_task()

            if not available_task:
                print("❌ No available tasks found")
                print("All visible tasks are completing or locked.")
                self.close_task_dialog()
                return False  # Retry later

            task_x, task_y = available_task
            print(f"✅ Found available task at ({task_x}, {task_y})")

            # Update the select_full_task to use this position
            self._next_task_coords = available_task

            # Step 2: Get task card bounds for material scanning
            print("\n=== Step 2: Detecting Material Numbers ===")
            card_x, card_y, card_w, card_h = self.get_task_card_bounds_from_click(task_x, task_y)
            print(f"Task card region: ({card_x}, {card_y}, {card_w}x{card_h})")

            # Give time for the task display to show
            time.sleep(0.5)

            # Step 3: Find material numbers (black or red text)
            from detection_config import MATERIAL_ZONE_START, MATERIAL_ZONE_END, CLICK_OFFSET_Y
            material_numbers = self._find_material_numbers(card_x, card_y, card_w, card_h)

            if not material_numbers:
                print("\n✅ No material numbers detected!")
                print("Clicking task card to start...")

                # Click empty area on card (center-right)
                click_x, click_y = self.material_scanner.find_empty_click_area(
                    card_x, card_y, card_w, card_h, []
                )
                self.safe_click(click_x, click_y)

                # Wait for UI to load (trains or collect buttons)
                print("\n⏳ Waiting for UI to load...")
                time.sleep(2.5)

                # First, check for and click any Collect buttons
                # (Resources ready to collect from previous tasks)
                print("\n=== Checking for Collect Buttons ===")
                print("(Collect buttons appear where Dispatch button normally is)")
                collect_count = 0
                max_collect_attempts = 10  # Safety limit

                for attempt in range(max_collect_attempts):
                    print(f"Attempt {attempt + 1}/{max_collect_attempts}...")
                    collect_button = self.resource_collector.find_collect_button(context="task")
                    if collect_button:
                        print(f"✓ Found Collect button {collect_count + 1}, clicking...")
                        self.safe_click(collect_button[0], collect_button[1])
                        collect_count += 1
                        time.sleep(0.5)  # Wait for next collect button to appear
                    else:
                        # No more collect buttons
                        print("No more collect buttons found")
                        break

                if collect_count > 0:
                    print(f"✅ Collected {collect_count} resource(s)")
                    # Wait a moment after collecting
                    time.sleep(1.0)
                else:
                    print("ℹ️  No collect buttons found, proceeding to dispatch trains")

                # Now dispatch trains for all available operators
                dispatch_success = self.train_dispatcher.dispatch_trains_for_task(
                    self.available_operators
                )

                if dispatch_success:
                    print("✅ Task started and trains dispatched successfully!")
                else:
                    print("⚠️  Task started but train dispatch may have failed")

                print("\n" + "="*60)
                print("Workflow completed successfully!")
                print("="*60)
                return True

            # Step 4: Determine action based on number colors
            has_red = any(num['is_red'] for num in material_numbers)
            has_black = any(not num['is_red'] for num in material_numbers)

            print(f"\nDetected: {len(material_numbers)} number(s)")
            print(f"  Red (warehouse stock low): {sum(1 for n in material_numbers if n['is_red'])}")
            print(f"  Black (current inventory): {sum(1 for n in material_numbers if not n['is_red'])}")

            # Display inventory amounts
            print("\n📦 Current Inventory:")
            for num in material_numbers:
                color = "RED" if num['is_red'] else "BLACK"
                value_str = str(num['value']) if num['value'] is not None else "?"
                print(f"  {color}: {value_str} units")

            if has_black and not has_red:
                print("\n✅ All materials available (only black numbers)!")
                print("Clicking task card to start...")

                # Click BELOW black number (on the task background/card to start task)
                black_number = next((n for n in material_numbers if not n['is_red']), None)
                if black_number:
                    click_x = black_number['x']
                    click_y = black_number['y'] + abs(CLICK_OFFSET_Y)  # Click BELOW (positive offset)
                    print(f"Clicking below black number at ({click_x}, {click_y})")
                else:
                    # No numbers, click center
                    click_x = card_x + card_w // 2
                    click_y = card_y + card_h // 3
                    print(f"Clicking task center at ({click_x}, {click_y})")
                self.safe_click(click_x, click_y)

                # Wait for UI to load (trains or collect buttons)
                print("\n⏳ Waiting for UI to load...")
                time.sleep(2.5)

                # First, check for and click any Collect buttons
                # (Resources ready to collect from previous tasks)
                print("\n=== Checking for Collect Buttons ===")
                print("(Collect buttons appear where Dispatch button normally is)")
                collect_count = 0
                max_collect_attempts = 10  # Safety limit

                for attempt in range(max_collect_attempts):
                    print(f"Attempt {attempt + 1}/{max_collect_attempts}...")
                    collect_button = self.resource_collector.find_collect_button(context="task")
                    if collect_button:
                        print(f"✓ Found Collect button {collect_count + 1}, clicking...")
                        self.safe_click(collect_button[0], collect_button[1])
                        collect_count += 1
                        time.sleep(0.5)  # Wait for next collect button to appear
                    else:
                        # No more collect buttons
                        print("No more collect buttons found")
                        break

                if collect_count > 0:
                    print(f"✅ Collected {collect_count} resource(s)")
                    # Wait a moment after collecting
                    time.sleep(1.0)
                else:
                    print("ℹ️  No collect buttons found, proceeding to dispatch trains")

                # Now dispatch trains for all available operators
                dispatch_success = self.train_dispatcher.dispatch_trains_for_task(
                    self.available_operators
                )

                if dispatch_success:
                    print("✅ Task started and trains dispatched successfully!")
                else:
                    print("⚠️  Task started but train dispatch may have failed")

            else:
                print("\n⚠️  Materials needed from warehouse (red numbers detected)!")

                # Get DELIVER amount to know how much we need
                deliver_amount = self._find_deliver_amount(card_x, card_y, card_w, card_h)

                if deliver_amount is None:
                    print("❌ Could not detect DELIVER amount - skipping task")
                    # Close task and retry
                    print("Pressing ESC to go back...")
                    pyautogui.press('esc')
                    time.sleep(1.0)
                    pyautogui.press('esc')
                    time.sleep(1.0)
                    return False

                print(f"📋 DELIVER amount needed: {deliver_amount}")

                # Find first red number (warehouse stock) and click ABOVE it (on the material icon)
                red_number = next((n for n in material_numbers if n['is_red']), None)
                if red_number:
                    warehouse_stock = red_number['value'] if red_number['value'] is not None else 0
                    print(f"📦 Warehouse stock: {warehouse_stock}")

                    click_x = red_number['x']
                    click_y = red_number['y'] + CLICK_OFFSET_Y  # Click ABOVE (negative offset)
                    print(f"Clicking above red number (material icon) at ({click_x}, {click_y})")
                    self.safe_click(click_x, click_y)

                    # Wait for popup to appear
                    print("\n⏳ Waiting for material popup...")
                    time.sleep(1.5)

                    # Find and click the blue button in the popup
                    if self._find_and_click_blue_button():
                        print("✅ Clicked blue button - navigating to material source")

                        # Wait longer for UI to fully load
                        print("⏳ Waiting for material generation UI to load...")
                        time.sleep(3.0)  # Wait for navigation to source and UI to load

                        # Dispatch trains to generate materials
                        generation_success = self._dispatch_trains_for_material_generation(
                            deliver_amount, warehouse_stock
                        )

                        if generation_success:
                            print("\n✅ Material generation complete!")
                        else:
                            print("\n⚠️  Material generation incomplete - may not have enough")

                        # Press ESC twice to go back to task menu
                        print("\nClosing material generation UI...")
                        pyautogui.press('esc')
                        time.sleep(1.0)
                        pyautogui.press('esc')
                        time.sleep(1.0)

                        # Restart the cycle to check tasks again
                        print("\n🔄 Restarting cycle to check tasks...")
                        return False  # Return False to restart the workflow
                    else:
                        print("❌ Failed to find blue button in popup")
                else:
                    print("⚠️  No red numbers found despite has_red=True")
                    print("This shouldn't happen - skipping task")

                # Close the task dialog
                print("\n=== Closing Task Dialog ===")
                for i in range(3):
                    self.close_task_dialog()
                    time.sleep(0.3)

                # Step 6: Open warehouse
                if not self.open_warehouse():
                    print("Failed to open warehouse")
                    return False

                # Step 7: Process queue
                self.process_material_queue()

                print("\n⚠️  Materials collected, but task not started yet")
                print("Will retry workflow to start the task with collected materials")
                return False  # Retry to start the task with materials now available

            print("\n" + "="*60)
            print("Workflow completed successfully!")
            print("="*60)
            return True  # Success

        except pyautogui.FailSafeException:
            print("\n!!! EMERGENCY STOP - Mouse moved to corner !!!")
            raise  # Re-raise to stop the loop
        except Exception as e:
            print(f"\nError during workflow: {e}")
            import traceback
            traceback.print_exc()
            return False  # Failed, can retry


def main():
    """Main entry point with polling loop."""
    print("="*60)
    print("Task Automation Script")
    print("="*60)
    print("\nThis will continuously monitor and automate tasks")
    print("Move mouse to top-left corner to emergency stop")

    # 5-second startup countdown
    print("\nStarting in:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("  Starting automation!\n")

    automation = TaskAutomation(click_delay=0.5)
    poll_interval = 30  # Check every 30 seconds for debugging

    try:
        while True:
            # Run the workflow
            success = automation.run_full_workflow()

            if success:
                print("\n✅ Task workflow completed successfully!")
                print(f"⏳ Waiting {poll_interval} seconds before next check...")
                time.sleep(poll_interval)
            else:
                # Operators not available, check timer
                wait_time = automation.operator_checker.read_next_operator_timer()

                if wait_time:
                    # Add 10 seconds buffer
                    wait_time += 10
                    minutes = wait_time // 60
                    seconds = wait_time % 60
                    print(f"\n⏳ Waiting {minutes}m {seconds}s for operators to become available...")
                    time.sleep(wait_time)
                else:
                    # Default wait time
                    print(f"\n⏳ Waiting {poll_interval} seconds before retry...")
                    time.sleep(poll_interval)

    except pyautogui.FailSafeException:
        print("\n!!! EMERGENCY STOP - Mouse moved to corner !!!")
        print("Automation stopped.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
        print("Automation stopped.")


if __name__ == "__main__":
    main()
