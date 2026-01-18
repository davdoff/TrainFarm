#!/usr/bin/env python3
"""
Resource Generation Module
Handles collecting resources from mines/sources or crafting in factories.
"""

import time
import pyautogui
import cv2
import numpy as np
from typing import Optional, Tuple, List
from template_matcher import find_template_on_screen, find_all_matches
from pathlib import Path
from color_detector import ColorDetector
import pytesseract


class ResourceGenerator:
    """Handles resource generation from mines and factories."""

    def __init__(self):
        self.trains_bottom_template = "Templates/allTrainInBottomOfScreen.png"
        self.train_clicked_template = "Templates/trainClicked.png"
        self.dispatch_button_template = None  # You'll need to create this
        self.color_detector = ColorDetector()
        self.confirm_button_template = "Templates/ConfirmButton.png"  # You may need to create this
        self.max_crafting_depth = 5  # Prevent infinite recursion

    def detect_location_type(self) -> str:
        """
        Detect if we're at a mine/source or factory.

        Returns:
            'mine' if trains are at bottom (direct collection)
            'factory' if no trains (crafting)
            'unknown' if can't determine
        """
        print("\n=== Detecting Location Type ===")

        # Check if trains are visible at bottom
        match = find_template_on_screen(self.trains_bottom_template, threshold=0.6)

        if match:
            print("✅ Detected: MINE/SOURCE (trains visible at bottom)")
            return 'mine'
        else:
            print("✅ Detected: FACTORY (no trains, must craft)")
            return 'factory'

    def collect_from_mine(self) -> bool:
        """
        Collect resources from a mine/source using trains.

        Process:
        1. Find trains at bottom of screen
        2. Click first train (highest capacity)
        3. Click Dispatch button

        Returns:
            True if successful, False otherwise
        """
        print("\n=== Collecting from Mine/Source ===")

        # Find the first train (leftmost/highest capacity)
        train_coords = self.find_first_train()

        if not train_coords:
            print("❌ Could not find first train")
            return False

        x, y = train_coords
        print(f"Found first train at ({x}, {y})")

        # Click the train
        print("Clicking first train...")
        pyautogui.click(x, y)
        time.sleep(0.8)  # Wait for train details to show

        # Verify train is clicked (optional - check for trainClicked template)
        if self.verify_train_clicked():
            print("✅ Train selected successfully")
        else:
            print("⚠️  Train might not be selected, continuing anyway...")

        # Find and click Dispatch button
        dispatch_coords = self.find_dispatch_button()

        if not dispatch_coords:
            print("❌ Could not find Dispatch button")
            # Try pressing ESC to go back
            pyautogui.press('esc')
            return False

        dispatch_x, dispatch_y = dispatch_coords
        print(f"Found Dispatch button at ({dispatch_x}, {dispatch_y})")
        print("Clicking Dispatch...")
        pyautogui.click(dispatch_x, dispatch_y)
        time.sleep(1.0)  # Wait for dispatch to complete

        print("✅ Resource collection dispatched!")
        return True

    def find_first_train(self) -> Optional[Tuple[int, int]]:
        """
        Find the first train (leftmost) at the bottom of the screen.

        Returns:
            (x, y) coordinates of first train, or None if not found
        """
        # The trains are at the bottom of screen
        # We need to find the leftmost train

        # Strategy 1: Look for a specific train icon/template
        # For now, we'll estimate based on screen size

        screen_width, screen_height = pyautogui.size()

        # Trains are at bottom, let's estimate first train position
        # Usually around 1/6 from left, near bottom
        estimated_x = screen_width // 6
        estimated_y = screen_height - 100  # 100 pixels from bottom

        print(f"Estimated first train position: ({estimated_x}, {estimated_y})")

        # TODO: Could use template matching for train icon
        # For now, return estimated position
        return (estimated_x, estimated_y)

    def verify_train_clicked(self) -> bool:
        """
        Verify that a train is selected by looking for the trainClicked template.

        Returns:
            True if train is selected, False otherwise
        """
        match = find_template_on_screen(self.train_clicked_template, threshold=0.6)
        return match is not None

    def find_dispatch_button(self) -> Optional[Tuple[int, int]]:
        """
        Find the Dispatch button.

        Returns:
            (x, y) coordinates of Dispatch button, or None if not found
        """
        if self.dispatch_button_template and Path(self.dispatch_button_template).exists():
            match = find_template_on_screen(self.dispatch_button_template, threshold=0.7)
            if match:
                return (match['x'], match['y'])

        # Fallback: Estimate position
        # Dispatch button is usually in the lower right area after selecting train
        screen_width, screen_height = pyautogui.size()

        # Estimate: right side, lower part
        estimated_x = screen_width - 150
        estimated_y = screen_height - 150

        print(f"⚠️  Dispatch button template not found, using estimate: ({estimated_x}, {estimated_y})")
        return (estimated_x, estimated_y)

    def detect_red_text_in_factory_popup(self) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Detect if there is red text in the factory popup (indicating insufficient materials).

        Returns:
            (has_red, coordinates) - has_red is True if red text found, coordinates is the location
        """
        print("\n=== Checking for Red Text in Factory Popup ===")

        # Capture the center portion of the screen where the popup appears
        screen_width, screen_height = pyautogui.size()

        # Define popup area (center of screen, roughly where the popup is)
        popup_x = int(screen_width * 0.3)
        popup_y = int(screen_height * 0.3)
        popup_width = int(screen_width * 0.4)
        popup_height = int(screen_height * 0.4)

        # Capture the popup area
        image = self.color_detector.capture_region(popup_x, popup_y, popup_width, popup_height)

        # Convert to HSV for red detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for red color
        mask = None
        for lower, upper in self.color_detector.RED_RANGES:
            lower_bound = np.array(lower, dtype=np.uint8)
            upper_bound = np.array(upper, dtype=np.uint8)
            range_mask = cv2.inRange(hsv, lower_bound, upper_bound)

            if mask is None:
                mask = range_mask
            else:
                mask = cv2.bitwise_or(mask, range_mask)

        # Find contours of red regions
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find the largest red region (likely the red text number)
            largest_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest_contour)

            if M["m00"] > 0:
                # Calculate center of red region
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                # Convert to screen coordinates
                screen_x = popup_x + cx
                screen_y = popup_y + cy

                print(f"✅ Red text detected at ({screen_x}, {screen_y})")
                return True, (screen_x, screen_y)

        print("✅ No red text detected - materials are sufficient")
        return False, None

    def find_material_icon_above_red_text(self, red_text_x: int, red_text_y: int) -> Optional[Tuple[int, int]]:
        """
        Find the material icon above the red text.

        Args:
            red_text_x: X coordinate of the red text
            red_text_y: Y coordinate of the red text

        Returns:
            (x, y) coordinates of the material icon to click, or None if not found
        """
        print("\n=== Finding Material Icon Above Red Text ===")

        # Material icon should be directly above the red number
        # Use the SAME X coordinate as the red text
        icon_x = red_text_x

        # Try different offsets above the red text (in pixels, will be converted by window manager)
        # OLD: [80, 100, 120, 140, 160] pixels
        # For 1080p: 80px = 7.4%, 100px = 9.3%, 120px = 11.1%, 140px = 13%, 160px = 14.8%
        # Note: These will be passed to window_manager for conversion
        offsets = [80, 100, 120, 140, 160]  # Pixels - WindowManager will handle conversion

        for offset in offsets:
            icon_y = red_text_y - offset
            print(f"Trying offset {offset}: ({icon_x}, {icon_y})")

            # Check if position is valid
            if icon_y > 0:
                print(f"✅ Material icon estimated at ({icon_x}, {icon_y})")
                return (icon_x, icon_y)

        print("❌ Could not determine material icon position")
        return None

    def find_and_click_confirm_button(self) -> bool:
        """
        Find and click the CONFIRM button in the factory popup.

        Returns:
            True if successful, False otherwise
        """
        print("\n=== Finding and Clicking CONFIRM Button ===")

        # Try to find confirm button using template matching
        if Path(self.confirm_button_template).exists():
            match = find_template_on_screen(self.confirm_button_template, threshold=0.7)
            if match:
                print(f"✅ Found CONFIRM button at ({match['x']}, {match['y']})")
                pyautogui.click(match['x'], match['y'])
                time.sleep(1.0)
                return True

        # Fallback: CONFIRM button is typically at bottom center of popup
        screen_width, screen_height = pyautogui.size()
        confirm_x = screen_width // 2
        confirm_y = int(screen_height * 0.65)  # Lower part of popup

        print(f"⚠️  Using estimated CONFIRM button position: ({confirm_x}, {confirm_y})")
        pyautogui.click(confirm_x, confirm_y)
        time.sleep(1.0)
        return True

    def craft_in_factory(self, material_icon_path: str, depth: int = 0) -> bool:
        """
        Craft a material in a factory with recursive dependency handling.

        Process:
        1. Click blue button to go to factory
        2. Check for red text (insufficient materials)
        3. If red text exists: click material icon above it to craft dependency (recursive)
        4. If no red text: click CONFIRM to start crafting

        Args:
            material_icon_path: Path to the material icon we want to craft
            depth: Current recursion depth (for dependency crafting)

        Returns:
            True if successful, False otherwise
        """
        if depth >= self.max_crafting_depth:
            print(f"❌ Maximum crafting depth ({self.max_crafting_depth}) reached - possible circular dependency")
            return False

        indent = "  " * depth
        print(f"\n{indent}=== Crafting in Factory (Depth: {depth}) ===")
        print(f"{indent}Looking for material icon: {material_icon_path}")

        # At this point, we assume we've already navigated to the factory
        # and the popup is showing the material we want to craft

        # Wait for popup to fully load
        time.sleep(1.5)

        # Check for red text (insufficient materials for crafting)
        has_red, red_coords = self.detect_red_text_in_factory_popup()

        if has_red and red_coords:
            print(f"{indent}⚠️  Red text detected - material dependencies are insufficient")

            # Find the material icon above the red text
            red_x, red_y = red_coords
            material_icon_coords = self.find_material_icon_above_red_text(red_x, red_y)

            if not material_icon_coords:
                print(f"{indent}❌ Could not find material icon above red text")
                return False

            icon_x, icon_y = material_icon_coords
            print(f"{indent}Clicking on dependency material at ({icon_x}, {icon_y})...")
            pyautogui.click(icon_x, icon_y)
            time.sleep(1.5)

            # Now we need to click the blue button again to go to this material's source
            print(f"{indent}Looking for blue button to navigate to dependency source...")
            blue_button_coords = self.find_blue_button()

            if not blue_button_coords:
                print(f"{indent}❌ Could not find blue button for dependency")
                pyautogui.press('esc')
                return False

            blue_x, blue_y = blue_button_coords
            print(f"{indent}Clicking blue button at ({blue_x}, {blue_y})...")
            pyautogui.click(blue_x, blue_y)
            time.sleep(1.5)

            # Recursively craft the dependency
            print(f"{indent}🔄 Recursively crafting dependency...")
            success = self.craft_in_factory(material_icon_path, depth + 1)

            if not success:
                print(f"{indent}❌ Failed to craft dependency")
                return False

            print(f"{indent}✅ Dependency crafted successfully")

            # After crafting dependency, we should be back at the current material popup
            # Try to confirm again
            time.sleep(1.0)
            return self.find_and_click_confirm_button()

        else:
            # No red text - materials are sufficient, click CONFIRM
            print(f"{indent}✅ Materials are sufficient - clicking CONFIRM")
            return self.find_and_click_confirm_button()

    def find_blue_button(self) -> Optional[Tuple[int, int]]:
        """
        Find the blue button at the top of the screen (used to navigate to material source).
        Uses the same robust detection as task_automation._find_and_click_blue_button()

        Returns:
            (x, y) coordinates of the blue button, or None if not found
        """
        print("\n=== Finding Blue Button ===")

        # Capture full screen
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        # Convert to HSV for blue detection
        hsv = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2HSV)

        # Blue color range (same as task_automation.py)
        blue_lower = np.array([90, 100, 150], dtype=np.uint8)  # H, S, V
        blue_upper = np.array([130, 255, 255], dtype=np.uint8)

        # Create mask for blue
        mask = cv2.inRange(hsv, blue_lower, blue_upper)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get scale factor (for retina displays)
        try:
            from template_matcher import get_scale_factor
            scale_factor = get_scale_factor()
        except:
            scale_factor = 1.0

        if contours:
            # Sort by area, largest first
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            # Check top 3 largest blue regions
            for contour in contours[:3]:
                area = cv2.contourArea(contour)

                # Button should be reasonably large (at least 10000 pixels)
                if area < 10000:
                    print(f"  Skipping small blue region (area={area})")
                    continue

                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)

                # Button should be wider than tall (rectangular)
                aspect_ratio = w / h
                if aspect_ratio < 1.5:  # Should be at least 1.5x wider than tall
                    print(f"  Skipping non-rectangular region (aspect={aspect_ratio:.2f})")
                    continue

                # Calculate center position (accounting for scale factor)
                center_x = int((x + w // 2) / scale_factor)
                center_y = int((y + h // 2) / scale_factor)

                print(f"✅ Blue button found: size={w}x{h}, area={area}, at ({center_x}, {center_y})")
                return (center_x, center_y)

        # If no valid button found, return None (don't use fallback)
        print("⚠️  Blue button not detected (no valid blue rectangular regions found)")
        return None

    def generate_resource(self, material_icon_path: str) -> bool:
        """
        Generate/collect a resource - auto-detects mine vs factory.

        Args:
            material_icon_path: Path to the material icon (needed for factory)

        Returns:
            True if successful, False otherwise
        """
        # Detect where we are
        location_type = self.detect_location_type()

        if location_type == 'mine':
            # Collect from mine using trains
            success = self.collect_from_mine()

            if success:
                # Wait a bit, then press ESC to return to warehouse
                time.sleep(1.0)
                print("Pressing ESC to return to warehouse...")
                pyautogui.press('esc')

            return success

        elif location_type == 'factory':
            # Craft in factory
            success = self.craft_in_factory(material_icon_path)

            if success:
                # Wait a bit, then press ESC to return to warehouse
                time.sleep(1.0)
                print("Pressing ESC to return to warehouse...")
                pyautogui.press('esc')

            return success

        else:
            print("❌ Unknown location type")
            # Try pressing ESC to go back
            pyautogui.press('esc')
            return False


def test_resource_generator():
    """Test the resource generator."""
    print("="*60)
    print("Resource Generator Test")
    print("="*60)
    print()
    print("Instructions:")
    print("1. Navigate to a mine/source OR factory in your game")
    print("2. Press ENTER when ready")
    print("3. The test will detect the type and attempt generation")
    print()

    input("Press ENTER when ready...")

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    print("\n" + "="*60)
    print("TESTING RESOURCE GENERATION")
    print("="*60 + "\n")

    generator = ResourceGenerator()

    # Detect location
    location_type = generator.detect_location_type()

    print("\n" + "="*60)
    print(f"Location Type: {location_type.upper()}")
    print("="*60)

    if location_type == 'mine':
        print("\nWould you like to test mine collection? (y/n)")
        if input().lower() == 'y':
            result = generator.collect_from_mine()
            print(f"\nResult: {'Success' if result else 'Failed'}")

    elif location_type == 'factory':
        print("\nFactory detected - would need material icon to test crafting")
        print("Use the full workflow to test factory crafting")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    test_resource_generator()
