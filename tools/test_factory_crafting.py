#!/usr/bin/env python3
"""
Test Factory Crafting Workflow

This tool tests the factory automation module:
1. Finds and clicks a material icon (CopperWire)
2. Clicks the blue button to navigate to factory
3. Detects red text (missing materials) in requirements
4. Clicks above the first red text to test navigation

Usage:
    python tools/test_factory_crafting.py [material_name]

Example:
    python tools/test_factory_crafting.py CopperWire
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.factory_automation import FactoryAutomation


def main():
    """Main entry point."""
    # Get material name from command line or use default
    material_name = sys.argv[1] if len(sys.argv) > 1 else "CopperWire"

    print("="*60)
    print(f"Factory Crafting Test: {material_name}")
    print("="*60)
    print("\nThis test will:")
    print(f"1. Find and click {material_name} icon")
    print("2. Click blue button to navigate to factory")
    print("3. Wait for factory UI (Confirm button)")
    print("4. Find the material requirements region")
    print("5. Detect red text (missing materials)")
    print("6. Click above first red text (TEST)")
    print()
    print("Prerequisites:")
    print("- Game must be open and in fullscreen (F11)")
    print(f"- {material_name} icon must be visible on screen")
    print("- You should be at the main game view")
    print()

    input("Press ENTER when ready...")

    print("\nStarting in 3 seconds...")
    print("Move mouse to top-left corner to emergency stop")

    import time
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    print("\nStarting test!\n")

    # Initialize factory automation
    factory = FactoryAutomation(click_delay=0.5)

    # Run the test
    success = factory.craft_material(material_name)

    print("\n" + "="*60)
    if success:
        print("✅ Test completed successfully!")
        print()
        print("Review the output:")
        print("1. Did it find the material icon?")
        print("2. Did it click the blue button?")
        print("3. Did it detect red text?")
        print("4. Did clicking above red text navigate correctly?")
        print()
        print("Check saved debug images:")
        print("  - factory_requirements_region.png")
        print("  - factory_requirements_bottom.png")
        print("  - factory_requirements_red_mask.png")
    else:
        print("❌ Test failed - check the output above for errors")
    print("="*60)


if __name__ == "__main__":
    main()
