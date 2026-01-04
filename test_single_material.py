#!/usr/bin/env python3
"""
Test a single material template to see matching confidence.
"""

import time
import cv2
import numpy as np
import pyautogui
from pathlib import Path

def test_material_match(material_name: str):
    """Test matching for a specific material."""
    print("="*60)
    print(f"Testing Material: {material_name}")
    print("="*60)

    template_path = f"Templates/Materials/{material_name}.png"

    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        return

    print(f"\nTemplate: {template_path}")
    print("\nOpen a task card where this material is visible")
    input("Press ENTER when ready...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Capture first task card area
    card_x, card_y = 110, 150
    card_width, card_height = 360, 600

    screenshot = pyautogui.screenshot(region=(card_x, card_y, card_width, card_height))
    card_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Load template
    template = cv2.imread(template_path)
    if template is None:
        print(f"❌ Could not load template")
        return

    print(f"\nTemplate size: {template.shape[1]}x{template.shape[0]}")

    # Try different matching methods
    print("\n" + "="*60)
    print("MATCHING RESULTS")
    print("="*60)

    # Method 1: Regular template matching
    result_regular = cv2.matchTemplate(card_image, template, cv2.TM_CCOEFF_NORMED)
    _, max_val_regular, _, max_loc_regular = cv2.minMaxLoc(result_regular)
    print(f"\n1. Regular Matching:")
    print(f"   Best: {max_val_regular:.2%} at {max_loc_regular}")

    # Method 2: Edge-based matching
    card_gray = cv2.cvtColor(card_image, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    card_edges = cv2.Canny(card_gray, 50, 150)
    template_edges = cv2.Canny(template_gray, 50, 150)
    result_edges = cv2.matchTemplate(card_edges, template_edges, cv2.TM_CCOEFF_NORMED)
    _, max_val_edges, _, max_loc_edges = cv2.minMaxLoc(result_edges)
    print(f"\n2. Edge-Based Matching:")
    print(f"   Best: {max_val_edges:.2%} at {max_loc_edges}")

    # Method 3: Combined (what we use)
    result_combined = np.where(result_regular > 0.6, result_regular,
                              np.maximum(result_regular, result_edges * 0.6))
    _, max_val_combined, _, max_loc_combined = cv2.minMaxLoc(result_combined)
    print(f"\n3. Combined Matching (our method):")
    print(f"   Best: {max_val_combined:.2%} at {max_loc_combined}")

    # Show threshold status
    threshold = 0.48
    print(f"\n" + "="*60)
    print(f"Current threshold: {threshold:.2%}")
    if max_val_combined >= threshold:
        print(f"✅ WOULD BE DETECTED (conf: {max_val_combined:.2%})")
    else:
        shortage = threshold - max_val_combined
        print(f"❌ NOT DETECTED (conf: {max_val_combined:.2%}, need {shortage:.2%} more)")
        print(f"\nSuggestions:")
        if max_val_combined >= 0.60:
            print(f"  - Lower threshold to {max_val_combined - 0.02:.2f}")
        else:
            print(f"  - Re-crop template with cleaner background")
            print(f"  - Ensure material icon is centered")
            print(f"  - Try white background instead of current")

    # Save visualization
    vis = card_image.copy()

    # Draw best match location
    h, w = template.shape[:2]
    top_left = max_loc_combined
    bottom_right = (top_left[0] + w, top_left[1] + h)
    color = (0, 255, 0) if max_val_combined >= threshold else (0, 0, 255)
    cv2.rectangle(vis, top_left, bottom_right, color, 2)
    cv2.putText(vis, f"{max_val_combined:.0%}",
               (top_left[0], top_left[1] - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    Path("visualizeTries").mkdir(exist_ok=True)
    save_path = f"visualizeTries/test_{material_name}.png"
    cv2.imwrite(save_path, vis)
    print(f"\n💾 Visualization saved: {save_path}")

    print("\n" + "="*60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        material = sys.argv[1]
    else:
        material = input("Enter material name (e.g., 'Nails', 'Steel', 'Coal'): ")

    test_material_match(material)
