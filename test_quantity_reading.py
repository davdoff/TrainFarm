#!/usr/bin/env python3
"""
Test Material Quantity Reading
Tests OCR for reading warehouse stock and needed amounts.
"""

import time
from material_scanner import MaterialScanner
from task_card_detector import TaskCardDetector

def test_quantity_reading():
    """Test reading material quantities from a task card."""
    print("="*60)
    print("Material Quantity Reading Test")
    print("="*60)

    print("\nOpen a task card with materials visible")
    print("Make sure you can see:")
    print("  - Material icons")
    print("  - Red numbers below materials (warehouse stock)")
    print("  - 'Deliver' text with number to the right (amount needed)")
    input("\nPress ENTER when ready...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    scanner = MaterialScanner()
    card_detector = TaskCardDetector()

    # Get first task card region
    cards = card_detector.find_task_cards()
    if not cards:
        print("❌ No task cards found")
        return

    card_x, card_y, card_w, card_h = cards[0]
    print(f"\n=== Scanning First Task Card ===")
    print(f"Region: ({card_x}, {card_y}, {card_w}x{card_h})")

    # Find materials
    print("\n=== Finding Materials ===")
    materials = scanner.find_materials_on_card(card_x, card_y, card_w, card_h)

    if not materials:
        print("❌ No materials found on card")
        return

    print(f"Found {len(materials)} material(s)")

    # Read quantities
    materials = scanner.read_material_quantities(card_x, card_y, card_w, card_h, materials)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for mat in materials:
        print(f"\n{mat['name']}:")
        print(f"  Position: ({mat['x']}, {mat['y']})")
        print(f"  Available: {mat.get('available', 'Unknown')}")
        print(f"  Warehouse Stock: {mat.get('warehouse_stock', 'Not read')}")
        print(f"  Task Needs: {mat.get('needed', 'Not read')}")

        warehouse = mat.get('warehouse_stock', 0)
        needed = mat.get('needed', 0)
        if warehouse and needed:
            if warehouse < needed:
                shortage = needed - warehouse
                print(f"  ⚠️  SHORT BY: {shortage}")
            else:
                print(f"  ✅ SUFFICIENT")

    print("\n" + "="*60)
    print("Check visualizeTries/ocr_debug_*.png for OCR debugging")
    print("="*60)

if __name__ == "__main__":
    test_quantity_reading()
