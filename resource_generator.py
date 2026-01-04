#!/usr/bin/env python3
"""
Resource Generation Module
Handles collecting resources from mines/sources or crafting in factories.
"""

import time
import pyautogui
from typing import Optional, Tuple
from template_matcher import find_template_on_screen, find_all_matches
from pathlib import Path


class ResourceGenerator:
    """Handles resource generation from mines and factories."""

    def __init__(self):
        self.trains_bottom_template = "Templates/allTrainInBottomOfScreen.png"
        self.train_clicked_template = "Templates/trainClicked.png"
        self.dispatch_button_template = None  # You'll need to create this

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

    def craft_in_factory(self, material_icon_path: str) -> bool:
        """
        Craft a material in a factory.

        Args:
            material_icon_path: Path to the material icon we want to craft

        Returns:
            True if successful, False otherwise
        """
        print("\n=== Crafting in Factory ===")
        print(f"Looking for material icon: {material_icon_path}")

        if not Path(material_icon_path).exists():
            print(f"❌ Material icon not found: {material_icon_path}")
            return False

        # Search for the material icon in the factory
        # Try with scrolling
        max_scrolls = 5

        for scroll_attempt in range(max_scrolls + 1):
            if scroll_attempt > 0:
                print(f"Scrolling in factory... (attempt {scroll_attempt}/{max_scrolls})")
                pyautogui.scroll(-3)  # Scroll down
                time.sleep(0.3)

            # Search for material icon
            match = find_template_on_screen(material_icon_path, threshold=0.75)

            if match:
                print(f"✅ Found material in factory at ({match['x']}, {match['y']})")

                # Click the material to craft it
                print("Clicking material to craft...")
                pyautogui.click(match['x'], match['y'])
                time.sleep(1.0)

                print("✅ Crafting initiated!")
                return True

        print("❌ Could not find material in factory after scrolling")
        return False

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
