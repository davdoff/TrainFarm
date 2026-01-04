#!/usr/bin/env python3
"""
Quick test for material scanner integration.
Tests only the material scanning part without running the full workflow.
"""

import time
from task_automation import TaskAutomation

def test_material_scanning():
    """Test material scanning on current screen."""
    print("="*60)
    print("Material Scanner Integration Test")
    print("="*60)

    automation = TaskAutomation(click_delay=0.5)

    print("\nMaterial templates loaded:")
    for name in automation.material_scanner.material_templates.keys():
        print(f"  - {name}")

    input("\nOpen a task card with materials visible, then press ENTER...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Test on a sample card region (first task card position)
    card_x, card_y = 110, 150
    card_width, card_height = 360, 600

    print(f"\n=== Scanning Task Card ===")
    print(f"Region: ({card_x}, {card_y}, {card_width}x{card_height})")

    materials_found = automation.material_scanner.find_materials_on_card(
        card_x, card_y, card_width, card_height, visualize=True
    )

    print(f"\n=== Results ===")
    print(f"Found {len(materials_found)} material(s)")

    if materials_found:
        for mat in materials_found:
            status = "✓ Available" if mat['available'] else "✗ Not available"
            print(f"  - {mat['name']}: {status}")

        all_available = automation.material_scanner.all_materials_available(materials_found)
        print(f"\nAll materials available: {all_available}")

        # Find empty click area
        click_x, click_y = automation.material_scanner.find_empty_click_area(
            card_x, card_y, card_width, card_height, materials_found
        )
        print(f"Empty click area: ({click_x}, {click_y})")

        # Visualize (optional)
        print("\nTo see where the click would happen, check the coordinates above")
    else:
        print("  No materials detected on this card")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_material_scanning()
