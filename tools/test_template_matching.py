#!/usr/bin/env python3
"""
Interactive Template Matching Tester
Test template matching accuracy with customizable search areas and thresholds.

Usage:
    python -m tools.test_template_matching
"""

import cv2
import numpy as np
import pyautogui
import sys
from pathlib import Path
from typing import Optional, Tuple, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detectors.template_matcher import find_template_on_screen, find_all_matches


class TemplateMatchingTester:
    """Interactive tool for testing template matching accuracy."""

    def __init__(self):
        self.screenshot = None
        self.template = None
        self.template_path = None
        self.search_region = None  # (x, y, width, height)
        self.threshold = 0.8
        self.matches = []

    def take_screenshot(self, delay: int = 3):
        """
        Take a screenshot after a delay.

        Args:
            delay: Seconds to wait before taking screenshot
        """
        print(f"\nTaking screenshot in {delay} seconds...")
        print("Switch to your game window now!")

        for i in range(delay, 0, -1):
            print(f"  {i}...")
            import time
            time.sleep(1)

        screenshot = pyautogui.screenshot()
        self.screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        print("✓ Screenshot captured!")

    def select_template(self, template_path: str = None):
        """
        Select a template image to search for.

        Args:
            template_path: Path to template image, or None to browse
        """
        if template_path is None:
            # List available templates
            templates_dir = Path("Templates")
            print("\n" + "="*60)
            print("Available Templates:")
            print("="*60)

            # Categorize templates
            categories = {
                "Buttons": list(templates_dir.glob("buttons/*.png")),
                "Tasks": list(templates_dir.glob("tasks/*.png")),
                "UI": list(templates_dir.glob("ui/*.png")),
                "Materials": list(templates_dir.glob("Materials/*.png"))
            }

            all_templates = []
            for category, templates in categories.items():
                if templates:
                    print(f"\n{category}:")
                    for template in sorted(templates):
                        idx = len(all_templates)
                        all_templates.append(template)
                        print(f"  [{idx}] {template.name}")

            print("\n" + "="*60)
            choice = input("Enter template number (or path to custom template): ").strip()

            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(all_templates):
                    template_path = str(all_templates[idx])
                else:
                    print("Invalid choice!")
                    return False
            else:
                template_path = choice

        # Load template
        self.template_path = template_path
        self.template = cv2.imread(template_path)

        if self.template is None:
            print(f"✗ Failed to load template: {template_path}")
            return False

        h, w = self.template.shape[:2]
        print(f"✓ Template loaded: {Path(template_path).name}")
        print(f"  Size: {w}x{h} pixels")
        return True

    def define_search_region(self):
        """
        Define the search region interactively.
        """
        print("\n" + "="*60)
        print("Search Region Options:")
        print("="*60)
        print("1. Full screen")
        print("2. Top half")
        print("3. Bottom half")
        print("4. Left half")
        print("5. Right half")
        print("6. Center 50%")
        print("7. Bottom-left corner (20% x 20%)")
        print("8. Custom region (enter coordinates)")
        print()

        choice = input("Enter choice [1]: ").strip() or "1"

        screen_width, screen_height = pyautogui.size()

        if choice == "1":
            self.search_region = None
            print("✓ Using full screen")

        elif choice == "2":
            self.search_region = (0, 0, screen_width, screen_height // 2)
            print(f"✓ Top half: {self.search_region}")

        elif choice == "3":
            self.search_region = (0, screen_height // 2, screen_width, screen_height // 2)
            print(f"✓ Bottom half: {self.search_region}")

        elif choice == "4":
            self.search_region = (0, 0, screen_width // 2, screen_height)
            print(f"✓ Left half: {self.search_region}")

        elif choice == "5":
            self.search_region = (screen_width // 2, 0, screen_width // 2, screen_height)
            print(f"✓ Right half: {self.search_region}")

        elif choice == "6":
            margin_x = int(screen_width * 0.25)
            margin_y = int(screen_height * 0.25)
            self.search_region = (margin_x, margin_y,
                                 int(screen_width * 0.5), int(screen_height * 0.5))
            print(f"✓ Center 50%: {self.search_region}")

        elif choice == "7":
            self.search_region = (0, int(screen_height * 0.8),
                                 int(screen_width * 0.2), int(screen_height * 0.2))
            print(f"✓ Bottom-left corner: {self.search_region}")

        elif choice == "8":
            print("\nEnter custom region:")
            try:
                x = int(input("  X (left): "))
                y = int(input("  Y (top): "))
                w = int(input("  Width: "))
                h = int(input("  Height: "))
                self.search_region = (x, y, w, h)
                print(f"✓ Custom region: {self.search_region}")
            except ValueError:
                print("✗ Invalid input, using full screen")
                self.search_region = None
        else:
            print("Invalid choice, using full screen")
            self.search_region = None

    def set_threshold(self):
        """Set the matching threshold."""
        print("\n" + "="*60)
        print("Matching Threshold")
        print("="*60)
        print("Higher = more strict (fewer false positives)")
        print("Lower = more lenient (more matches)")
        print("Typical values: 0.6 - 0.9")
        print()

        threshold_input = input(f"Enter threshold [0.8]: ").strip()

        if threshold_input:
            try:
                self.threshold = float(threshold_input)
                if not 0.0 <= self.threshold <= 1.0:
                    print("Threshold must be between 0.0 and 1.0, using 0.8")
                    self.threshold = 0.8
            except ValueError:
                print("Invalid input, using 0.8")
                self.threshold = 0.8
        else:
            self.threshold = 0.8

        print(f"✓ Threshold set to: {self.threshold}")

    def run_matching(self, find_all: bool = False):
        """
        Run template matching with current settings.

        Args:
            find_all: If True, find all matches; if False, find best match only
        """
        print("\n" + "="*60)
        print("Running Template Matching...")
        print("="*60)
        print(f"Template: {Path(self.template_path).name}")
        print(f"Region: {self.search_region if self.search_region else 'Full screen'}")
        print(f"Threshold: {self.threshold}")
        print(f"Mode: {'Find all matches' if find_all else 'Find best match'}")
        print()

        if find_all:
            self.matches = find_all_matches(
                self.template_path,
                threshold=self.threshold,
                region=self.search_region,
                screenshot_bgr=self.screenshot
            )
            print(f"✓ Found {len(self.matches)} match(es)")
        else:
            match = find_template_on_screen(
                self.template_path,
                threshold=self.threshold,
                region=self.search_region,
                screenshot_bgr=self.screenshot
            )
            self.matches = [match] if match else []

            if match:
                print(f"✓ Found match!")
                print(f"  Position: ({match['x']}, {match['y']})")
                print(f"  Confidence: {match['confidence']:.2%}")
            else:
                print("✗ No match found")

        return len(self.matches) > 0

    def visualize_results(self, save_path: str = "template_match_result.png"):
        """
        Create a visualization of the matching results.

        Args:
            save_path: Path to save the visualization
        """
        if self.screenshot is None:
            print("✗ No screenshot available")
            return

        # Create a copy for visualization
        vis_image = self.screenshot.copy()

        # Get scale factor for coordinate conversion
        from src.detectors.template_matcher import get_scale_factor
        scale_factor = get_scale_factor()

        # Draw search region if defined
        if self.search_region:
            x, y, w, h = self.search_region
            # Scale coordinates to physical pixels
            x_scaled = int(x * scale_factor)
            y_scaled = int(y * scale_factor)
            w_scaled = int(w * scale_factor)
            h_scaled = int(h * scale_factor)
            cv2.rectangle(vis_image, (x_scaled, y_scaled), (x_scaled + w_scaled, y_scaled + h_scaled), (255, 255, 0), 3)
            cv2.putText(vis_image, "Search Region", (x_scaled + 5, y_scaled + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # Draw matches
        for i, match in enumerate(self.matches):
            x, y = match['top_left']
            x2, y2 = match['bottom_right']
            confidence = match['confidence']

            # Scale coordinates to physical pixels
            x_scaled = int(x * scale_factor)
            y_scaled = int(y * scale_factor)
            x2_scaled = int(x2 * scale_factor)
            y2_scaled = int(y2 * scale_factor)

            # Draw bounding box (green for high confidence, yellow for medium, red for low)
            if confidence >= 0.8:
                color = (0, 255, 0)  # Green
            elif confidence >= 0.6:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 0, 255)  # Red

            cv2.rectangle(vis_image, (x_scaled, y_scaled), (x2_scaled, y2_scaled), color, 3)

            # Draw center point
            center_x, center_y = match['x'], match['y']
            center_x_scaled = int(center_x * scale_factor)
            center_y_scaled = int(center_y * scale_factor)
            cv2.circle(vis_image, (center_x_scaled, center_y_scaled), 8, (255, 0, 255), -1)

            # Add label
            label = f"#{i+1}: {confidence:.2%}"
            cv2.putText(vis_image, label, (x_scaled, y_scaled - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Add summary text
        summary = f"Template: {Path(self.template_path).name} | Matches: {len(self.matches)} | Threshold: {self.threshold}"
        cv2.putText(vis_image, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(vis_image, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)

        # Save visualization
        cv2.imwrite(save_path, vis_image)
        print(f"\n✓ Visualization saved to: {save_path}")

        # Try to display (if display available)
        try:
            # Resize for display if too large
            max_width = 1920
            max_height = 1080
            h, w = vis_image.shape[:2]

            if w > max_width or h > max_height:
                scale = min(max_width / w, max_height / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                display_image = cv2.resize(vis_image, (new_w, new_h))
            else:
                display_image = vis_image

            cv2.imshow("Template Matching Results", display_image)
            print("\nPress any key in the image window to close...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Could not display image (headless environment?): {e}")
            print(f"Check saved file: {save_path}")

    def interactive_test(self):
        """Run an interactive template matching test session."""
        print("="*60)
        print("Template Matching Interactive Tester")
        print("="*60)

        # Step 1: Take screenshot
        delay_input = input("\nScreenshot delay in seconds [3]: ").strip()
        delay = int(delay_input) if delay_input.isdigit() else 3
        self.take_screenshot(delay)

        # Step 2: Select template
        if not self.select_template():
            return

        # Step 3: Define search region
        self.define_search_region()

        # Step 4: Set threshold
        self.set_threshold()

        # Step 5: Choose matching mode
        print("\n" + "="*60)
        print("Matching Mode:")
        print("="*60)
        print("1. Find best match only")
        print("2. Find all matches")
        print()
        mode = input("Enter choice [1]: ").strip() or "1"
        find_all = (mode == "2")

        # Step 6: Run matching
        self.run_matching(find_all)

        # Step 7: Visualize
        self.visualize_results()

        # Step 8: Try again?
        print("\n" + "="*60)
        print("Options:")
        print("="*60)
        print("1. Adjust threshold and retry")
        print("2. Change search region and retry")
        print("3. Try different template")
        print("4. Exit")
        print()

        choice = input("Enter choice [4]: ").strip() or "4"

        if choice == "1":
            self.set_threshold()
            self.run_matching(find_all)
            self.visualize_results()

        elif choice == "2":
            self.define_search_region()
            self.run_matching(find_all)
            self.visualize_results()

        elif choice == "3":
            self.select_template()
            self.define_search_region()
            self.set_threshold()
            self.run_matching(find_all)
            self.visualize_results()

        print("\n✓ Test complete!")


def main():
    """Main entry point."""
    tester = TemplateMatchingTester()

    try:
        tester.interactive_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
