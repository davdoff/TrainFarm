#!/usr/bin/env python3
"""
Example script showing how to use TemplateMatchingTester programmatically.

Usage:
    python tools/example_template_test.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.test_template_matching import TemplateMatchingTester


def example_test_dispatch_button():
    """Test the Dispatch button in bottom-left corner."""
    print("="*60)
    print("Example 1: Testing Dispatch Button")
    print("="*60)

    tester = TemplateMatchingTester()

    # Take screenshot
    tester.take_screenshot(delay=5)

    # Select template
    tester.select_template("Templates/buttons/DispatchButton.png")

    # Define search region (bottom-left corner)
    tester.search_region = (0, 1728, 432, 432)  # Adjust based on your screen
    print(f"✓ Search region: {tester.search_region}")

    # Set threshold
    tester.threshold = 0.7
    print(f"✓ Threshold: {tester.threshold}")

    # Run matching
    tester.run_matching(find_all=False)

    # Visualize
    tester.visualize_results("dispatch_button_test.png")


def example_test_all_materials():
    """Test finding all material icons on screen."""
    print("\n" + "="*60)
    print("Example 2: Finding All Coal Icons")
    print("="*60)

    tester = TemplateMatchingTester()

    # Take screenshot
    tester.take_screenshot(delay=5)

    # Select template
    tester.select_template("Templates/Materials/Coal.png")

    # Use full screen to find all
    tester.search_region = None
    print("✓ Using full screen")

    # Lower threshold for better detection
    tester.threshold = 0.6
    print(f"✓ Threshold: {tester.threshold}")

    # Find all matches
    tester.run_matching(find_all=True)

    # Visualize
    tester.visualize_results("coal_icons_test.png")


def example_threshold_sweep():
    """Test multiple thresholds to find optimal value."""
    print("\n" + "="*60)
    print("Example 3: Threshold Sweep for Confirm Button")
    print("="*60)

    tester = TemplateMatchingTester()

    # Take screenshot
    tester.take_screenshot(delay=5)

    # Select template
    tester.select_template("Templates/buttons/ConfirmButton.png")

    # Use center region (where popups appear)
    tester.search_region = (540, 540, 1080, 1080)  # Center 50%
    print(f"✓ Search region: {tester.search_region}")

    # Test multiple thresholds
    thresholds = [0.9, 0.85, 0.8, 0.75, 0.7, 0.65]

    for threshold in thresholds:
        tester.threshold = threshold
        print(f"\nTesting threshold: {threshold}")

        if tester.run_matching(find_all=False):
            print(f"✓ FOUND at threshold {threshold}")
            tester.visualize_results(f"confirm_button_threshold_{threshold}.png")
            print(f"Optimal threshold found: {threshold}")
            break
        else:
            print(f"✗ Not found at threshold {threshold}")


def example_region_comparison():
    """Compare different search regions for performance."""
    print("\n" + "="*60)
    print("Example 4: Search Region Comparison")
    print("="*60)

    import time

    tester = TemplateMatchingTester()

    # Take screenshot
    tester.take_screenshot(delay=5)

    # Select template
    tester.select_template("Templates/tasks/TaskCompleting.png")
    tester.threshold = 0.7

    regions = {
        "Full screen": None,
        "Top half": (0, 0, 2160, 1080),
        "Top-left corner": (0, 0, 432, 432),
    }

    for region_name, region in regions.items():
        print(f"\nTesting: {region_name}")
        tester.search_region = region

        start_time = time.time()
        found = tester.run_matching(find_all=False)
        elapsed = time.time() - start_time

        print(f"  Time: {elapsed*1000:.1f}ms")
        print(f"  Found: {found}")

        if found:
            tester.visualize_results(f"task_completing_{region_name.replace(' ', '_')}.png")


def main():
    """Run example tests."""
    print("Template Matching Tester - Example Scripts")
    print("="*60)
    print("\nSelect example to run:")
    print("1. Test Dispatch button (bottom-left region)")
    print("2. Find all Coal icons (full screen)")
    print("3. Threshold sweep for Confirm button")
    print("4. Compare search regions")
    print("5. Run all examples")
    print()

    choice = input("Enter choice [1]: ").strip() or "1"

    if choice == "1":
        example_test_dispatch_button()
    elif choice == "2":
        example_test_all_materials()
    elif choice == "3":
        example_threshold_sweep()
    elif choice == "4":
        example_region_comparison()
    elif choice == "5":
        example_test_dispatch_button()
        example_test_all_materials()
        example_threshold_sweep()
        example_region_comparison()
    else:
        print("Invalid choice")

    print("\n" + "="*60)
    print("Example complete!")
    print("="*60)


if __name__ == "__main__":
    main()
