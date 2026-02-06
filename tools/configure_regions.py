#!/usr/bin/env python3
"""
Interactive Region Configuration Tool

This tool allows you to:
1. Take a screenshot of the game
2. Visually select rectangular regions with the mouse
3. Name and save regions for use in detection_config.py
4. Export as both pixel coordinates and percentages (0.0-1.0)

Usage:
    python tools/configure_regions.py

Controls:
    - Click and drag to draw a rectangle
    - Press 'n' to name and save the current region
    - Press 'c' to clear the current selection
    - Press 'd' to delete the last saved region
    - Press 's' to save all regions to file
    - Press 'g' to generate Python code
    - Press 'q' to quit
    - Press 'r' to retake screenshot
"""

import cv2
import numpy as np
import pyautogui
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time


class RegionConfigurator:
    """Interactive tool for configuring detection regions."""

    def __init__(self):
        self.screenshot = None
        self.display_img = None
        self.regions: List[Dict] = []
        self.current_region = None
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.window_name = "Region Configuration Tool"
        self.scale_factor = 1.0
        self.screen_width = 0
        self.screen_height = 0

        # Colors
        self.COLOR_CURRENT = (0, 255, 0)  # Green for current selection
        self.COLOR_SAVED = (255, 0, 0)     # Blue for saved regions
        self.COLOR_TEXT = (255, 255, 255)  # White for text
        self.COLOR_BG = (0, 0, 0)          # Black for text background

    def capture_screenshot(self):
        """Capture a screenshot of the current screen."""
        print("\n" + "="*60)
        print("Capturing Screenshot")
        print("="*60)
        print("Switching to game window in 2 seconds...")
        time.sleep(2)

        # Capture screenshot
        screenshot = pyautogui.screenshot()
        # Convert PIL image to OpenCV format (RGB to BGR)
        self.screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_height, screenshot_width = self.screenshot.shape[:2]

        # IMPORTANT: Use logical screen size (pyautogui.size()) instead of screenshot size
        # This handles Retina/HiDPI displays correctly
        # Screenshot size may be 2x or more on Retina displays
        self.screen_width, self.screen_height = pyautogui.size()

        # Calculate scale factor for display purposes
        self.pixel_scale = screenshot_width / self.screen_width

        print(f"✓ Screenshot captured: {screenshot_width}x{screenshot_height} (physical)")
        print(f"  Logical screen size: {self.screen_width}x{self.screen_height}")
        if self.pixel_scale > 1.0:
            print(f"  HiDPI detected: {self.pixel_scale}x scale factor")

        # Scale down if too large for display
        # Note: We scale the physical screenshot, not the logical size
        max_display_width = 1920
        max_display_height = 1080

        scale_w = max_display_width / screenshot_width
        scale_h = max_display_height / screenshot_height
        self.scale_factor = min(scale_w, scale_h, 1.0)

        if self.scale_factor < 1.0:
            display_width = int(screenshot_width * self.scale_factor)
            display_height = int(screenshot_height * self.scale_factor)
            print(f"  Scaling display to {display_width}x{display_height} (scale: {self.scale_factor:.2f})")
        else:
            print("  Using full size display")

        self.update_display()

    def update_display(self):
        """Update the display image with all regions."""
        if self.screenshot is None:
            return

        # Create a copy of the screenshot
        self.display_img = self.screenshot.copy()

        # Draw all saved regions
        # Regions are stored in logical coordinates, need to scale to physical for drawing
        for region in self.regions:
            x1, y1, x2, y2 = region['x1'], region['y1'], region['x2'], region['y2']
            # Scale to physical coordinates for drawing on screenshot
            x1_phys = int(x1 * self.pixel_scale)
            y1_phys = int(y1 * self.pixel_scale)
            x2_phys = int(x2 * self.pixel_scale)
            y2_phys = int(y2 * self.pixel_scale)
            cv2.rectangle(self.display_img, (x1_phys, y1_phys), (x2_phys, y2_phys), self.COLOR_SAVED, 2)

            # Draw label background
            label = region['name']
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, thickness)

            # Position label above the rectangle (use physical coordinates)
            label_y = y1_phys - 10 if y1_phys > 30 else y1_phys + text_h + 10
            cv2.rectangle(self.display_img,
                         (x1_phys, label_y - text_h - 5),
                         (x1_phys + text_w + 5, label_y + 5),
                         self.COLOR_BG, -1)
            cv2.putText(self.display_img, label, (x1_phys, label_y),
                       font, font_scale, self.COLOR_SAVED, thickness)

        # Draw current selection (scale to physical coordinates)
        if self.start_point and self.end_point:
            start_phys = (int(self.start_point[0] * self.pixel_scale),
                         int(self.start_point[1] * self.pixel_scale))
            end_phys = (int(self.end_point[0] * self.pixel_scale),
                       int(self.end_point[1] * self.pixel_scale))
            cv2.rectangle(self.display_img, start_phys, end_phys,
                         self.COLOR_CURRENT, 2)

        # Scale for display if needed
        if self.scale_factor < 1.0:
            display_width = int(self.screen_width * self.scale_factor)
            display_height = int(self.screen_height * self.scale_factor)
            display = cv2.resize(self.display_img, (display_width, display_height))
        else:
            display = self.display_img

        # Add instructions overlay
        self.draw_instructions(display)

        cv2.imshow(self.window_name, display)

    def draw_instructions(self, img):
        """Draw instruction text overlay."""
        instructions = [
            "CONTROLS:",
            "Click & Drag: Draw region",
            "N: Name & save region",
            "C: Clear current",
            "D: Delete last",
            "S: Save to file",
            "G: Generate code",
            "R: Retake screenshot",
            "Q: Quit"
        ]

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        y_offset = 25

        for i, text in enumerate(instructions):
            y = y_offset + (i * 20)
            # Draw background
            (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
            cv2.rectangle(img, (5, y - text_h - 2), (15 + text_w, y + 5),
                         self.COLOR_BG, -1)
            # Draw text
            color = self.COLOR_TEXT if i > 0 else (0, 255, 255)  # Yellow for title
            cv2.putText(img, text, (10, y), font, font_scale, color, thickness)

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for region selection."""
        if self.screenshot is None:
            return

        # Scale coordinates back to physical screenshot size
        phys_x = int(x / self.scale_factor)
        phys_y = int(y / self.scale_factor)

        # Convert to logical coordinates (divide by HiDPI scale)
        actual_x = int(phys_x / self.pixel_scale)
        actual_y = int(phys_y / self.pixel_scale)

        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (actual_x, actual_y)
            self.end_point = None

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.end_point = (actual_x, actual_y)
                self.update_display()

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.start_point:
                self.end_point = (actual_x, actual_y)
                self.update_display()
                print(f"\n✓ Region selected: ({self.start_point[0]}, {self.start_point[1]}) to ({self.end_point[0]}, {self.end_point[1]})")
                print("  Press 'n' to name and save, or 'c' to clear")

    def save_current_region(self):
        """Name and save the current region."""
        if not self.start_point or not self.end_point:
            print("❌ No region selected. Click and drag to select a region first.")
            return

        # Ensure coordinates are ordered (top-left to bottom-right)
        x1 = min(self.start_point[0], self.end_point[0])
        y1 = min(self.start_point[1], self.end_point[1])
        x2 = max(self.start_point[0], self.end_point[0])
        y2 = max(self.start_point[1], self.end_point[1])

        # Calculate dimensions
        width = x2 - x1
        height = y2 - y1

        # Calculate percentages
        x1_pct = x1 / self.screen_width
        y1_pct = y1 / self.screen_height
        x2_pct = x2 / self.screen_width
        y2_pct = y2 / self.screen_height
        width_pct = width / self.screen_width
        height_pct = height / self.screen_height

        print("\n" + "="*60)
        print("Save Region")
        print("="*60)
        print(f"Logical Pixel Coordinates (PyAutoGUI space):")
        print(f"  Screen size: {self.screen_width}x{self.screen_height}")
        print(f"  Top-Left: ({x1}, {y1})")
        print(f"  Bottom-Right: ({x2}, {y2})")
        print(f"  Size: {width}x{height}")
        print(f"\nPercentage (0.0-1.0):")
        print(f"  x1: {x1_pct:.4f}, y1: {y1_pct:.4f}")
        print(f"  x2: {x2_pct:.4f}, y2: {y2_pct:.4f}")
        print(f"  width: {width_pct:.4f}, height: {height_pct:.4f}")
        if hasattr(self, 'pixel_scale') and self.pixel_scale > 1.0:
            print(f"\nNote: Physical pixels would be {self.pixel_scale}x these values (HiDPI display)")
        print()

        name = input("Enter region name (e.g., MATERIAL_ZONE_LEFT): ").strip()

        if not name:
            print("❌ Region name cannot be empty")
            return

        region = {
            'name': name,
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'width': width,
            'height': height,
            'x1_pct': x1_pct,
            'y1_pct': y1_pct,
            'x2_pct': x2_pct,
            'y2_pct': y2_pct,
            'width_pct': width_pct,
            'height_pct': height_pct,
            'screen_width': self.screen_width,
            'screen_height': self.screen_height
        }

        self.regions.append(region)
        print(f"✅ Region '{name}' saved!")

        # Clear current selection
        self.start_point = None
        self.end_point = None
        self.update_display()

    def clear_current(self):
        """Clear the current selection without saving."""
        self.start_point = None
        self.end_point = None
        self.update_display()
        print("✓ Current selection cleared")

    def delete_last(self):
        """Delete the last saved region."""
        if self.regions:
            deleted = self.regions.pop()
            print(f"✓ Deleted region '{deleted['name']}'")
            self.update_display()
        else:
            print("❌ No regions to delete")

    def save_to_file(self):
        """Save all regions to a JSON file."""
        if not self.regions:
            print("❌ No regions to save")
            return

        output_file = Path("region_config.json")
        data = {
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'regions': self.regions
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Saved {len(self.regions)} region(s) to {output_file}")

    def generate_code(self):
        """Generate Python code for detection_config.py."""
        if not self.regions:
            print("❌ No regions to generate code for")
            return

        print("\n" + "="*60)
        print("Generated Python Code for detection_config.py")
        print("="*60)
        print()

        for region in self.regions:
            name = region['name']
            print(f"# {name}")
            print(f"# Pixel coordinates: ({region['x1']}, {region['y1']}) to ({region['x2']}, {region['y2']})")
            print(f"# Size: {region['width']}x{region['height']} px")
            print(f"{name}_LEFT = {region['x1_pct']:.4f}")
            print(f"{name}_TOP = {region['y1_pct']:.4f}")
            print(f"{name}_RIGHT = {region['x2_pct']:.4f}")
            print(f"{name}_BOTTOM = {region['y2_pct']:.4f}")
            print()

        # Also save to file
        code_file = Path("region_config_code.py")
        with open(code_file, 'w') as f:
            f.write("# Auto-generated region configuration\n")
            f.write(f"# Screen size: {self.screen_width}x{self.screen_height}\n")
            f.write(f"# Generated with tools/configure_regions.py\n\n")

            for region in self.regions:
                name = region['name']
                f.write(f"# {name}\n")
                f.write(f"# Pixel coordinates: ({region['x1']}, {region['y1']}) to ({region['x2']}, {region['y2']})\n")
                f.write(f"# Size: {region['width']}x{region['height']} px\n")
                f.write(f"{name}_LEFT = {region['x1_pct']:.4f}\n")
                f.write(f"{name}_TOP = {region['y1_pct']:.4f}\n")
                f.write(f"{name}_RIGHT = {region['x2_pct']:.4f}\n")
                f.write(f"{name}_BOTTOM = {region['y2_pct']:.4f}\n\n")

        print(f"✅ Code also saved to {code_file}")
        print()

    def run(self):
        """Run the interactive region configuration tool."""
        print("\n" + "="*60)
        print("Interactive Region Configuration Tool")
        print("="*60)
        print()
        print("This tool helps you define precise detection zones")
        print("for use in your automation code.")
        print()

        # Capture initial screenshot
        self.capture_screenshot()

        # Create window and set mouse callback
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        print("\n" + "="*60)
        print("Interactive Mode Started")
        print("="*60)
        print("Click and drag on the image to select regions")
        print()

        while True:
            self.update_display()
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                # Quit
                print("\nQuitting...")
                break

            elif key == ord('n'):
                # Name and save current region
                self.save_current_region()

            elif key == ord('c'):
                # Clear current selection
                self.clear_current()

            elif key == ord('d'):
                # Delete last region
                self.delete_last()

            elif key == ord('s'):
                # Save to file
                self.save_to_file()

            elif key == ord('g'):
                # Generate code
                self.generate_code()

            elif key == ord('r'):
                # Retake screenshot
                cv2.destroyAllWindows()
                self.capture_screenshot()
                cv2.namedWindow(self.window_name)
                cv2.setMouseCallback(self.window_name, self.mouse_callback)

        cv2.destroyAllWindows()

        # Final summary
        print("\n" + "="*60)
        print("Summary")
        print("="*60)
        print(f"Total regions defined: {len(self.regions)}")
        for region in self.regions:
            print(f"  - {region['name']}")

        if self.regions:
            print("\nDon't forget to:")
            print("1. Copy the generated code to src/config/detection_config.py")
            print("2. Or load from region_config.json")


def main():
    """Main entry point."""
    configurator = RegionConfigurator()
    configurator.run()


if __name__ == "__main__":
    main()
