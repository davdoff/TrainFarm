#!/usr/bin/env python3
"""
Border Calibration Tool
Use this to fine-tune task card border detection for your specific device/screen.
"""

import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path


def draw_adjustable_borders():
    """Interactive tool to calibrate task card borders."""
    print("="*80)
    print("TASK CARD BORDER CALIBRATION TOOL")
    print("="*80)
    print("\nThis tool helps you calibrate the task card detection borders.")
    print("You'll adjust the borders to perfectly match your task cards.")
    print("\nInstructions:")
    print("1. Open the game's task menu with visible task cards")
    print("2. Press ENTER when ready")
    print("3. A screenshot will be saved with the current border settings")
    print("4. Adjust the values in task_card_detector.py based on what you see")
    print("5. Re-run this script to verify your changes")
    print("="*80)

    input("\nPress ENTER when task menu is open...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Get current values from detection_config.py
    try:
        from detection_config import (CARD_WIDTH, CARD_HEIGHT, CARD_START_X,
                                     CARD_START_Y, CARD_SPACING)
        card_width = CARD_WIDTH
        card_height = CARD_HEIGHT
        start_x = CARD_START_X
        start_y = CARD_START_Y
        spacing = CARD_SPACING
    except:
        print("⚠️  Could not read detection_config.py, using defaults")
        card_width = 374
        card_height = 610
        start_x = 115
        start_y = 195
        spacing = 397

    print(f"\nCurrent settings from detection_config.py:")
    print(f"  CARD_WIDTH   = {card_width}")
    print(f"  CARD_HEIGHT  = {card_height}")
    print(f"  CARD_START_X = {start_x}")
    print(f"  CARD_START_Y = {start_y}")
    print(f"  CARD_SPACING = {spacing}")

    # Calculate scale factor
    screen_width, screen_height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_height, screenshot_width = screenshot_np.shape[:2]
    scale_x = screenshot_width / screen_width
    scale_y = screenshot_height / screen_height
    scale_factor = (scale_x + scale_y) / 2

    print(f"\nDisplay scale factor: {scale_factor}")

    # Convert to BGR for OpenCV
    screenshot = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # Draw borders for up to 5 task cards
    colors = [
        (0, 255, 0),    # Green - Card 1
        (255, 0, 0),    # Blue - Card 2
        (0, 0, 255),    # Red - Card 3
        (255, 255, 0),  # Cyan - Card 4
        (255, 0, 255),  # Magenta - Card 5
    ]

    cards_drawn = 0
    for i in range(5):
        x = start_x + (i * spacing)
        y = start_y

        # Stop if card goes off screen
        if x + card_width > screen_width:
            break

        # Scale for drawing on screenshot
        sx = int(x * scale_factor)
        sy = int(y * scale_factor)
        sw = int(card_width * scale_factor)
        sh = int(card_height * scale_factor)

        # Draw border
        color = colors[i]
        cv2.rectangle(screenshot, (sx, sy), (sx + sw, sy + sh), color, 4)

        # Add label
        label = f"Card {i+1}"
        cv2.putText(screenshot, label, (sx + 10, sy + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)

        # Add corner markers for precise alignment
        marker_size = 20
        # Top-left
        cv2.line(screenshot, (sx, sy), (sx + marker_size, sy), color, 4)
        cv2.line(screenshot, (sx, sy), (sx, sy + marker_size), color, 4)
        # Top-right
        cv2.line(screenshot, (sx + sw, sy), (sx + sw - marker_size, sy), color, 4)
        cv2.line(screenshot, (sx + sw, sy), (sx + sw, sy + marker_size), color, 4)
        # Bottom-left
        cv2.line(screenshot, (sx, sy + sh), (sx + marker_size, sy + sh), color, 4)
        cv2.line(screenshot, (sx, sy + sh), (sx, sy + sh - marker_size), color, 4)
        # Bottom-right
        cv2.line(screenshot, (sx + sw, sy + sh), (sx + sw - marker_size, sy + sh), color, 4)
        cv2.line(screenshot, (sx + sw, sy + sh), (sx + sw, sy + sh - marker_size), color, 4)

        # Draw center crosshair
        center_x = sx + sw // 2
        center_y = sy + sh // 2
        cv2.line(screenshot, (center_x - 10, center_y), (center_x + 10, center_y), color, 2)
        cv2.line(screenshot, (center_x, center_y - 10), (center_x, center_y + 10), color, 2)

        cards_drawn += 1

    # Add calibration info overlay
    info_y = 40
    cv2.rectangle(screenshot, (10, 10), (600, 250), (0, 0, 0), -1)
    cv2.putText(screenshot, "BORDER CALIBRATION", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    info_y += 40
    cv2.putText(screenshot, f"card_width  = {card_width} px", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    info_y += 30
    cv2.putText(screenshot, f"card_height = {card_height} px", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    info_y += 30
    cv2.putText(screenshot, f"start_x     = {start_x} px", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    info_y += 30
    cv2.putText(screenshot, f"start_y     = {start_y} px", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    info_y += 30
    cv2.putText(screenshot, f"spacing     = {spacing} px", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    info_y += 30
    cv2.putText(screenshot, f"Cards drawn: {cards_drawn}", (20, info_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # Save screenshot
    Path("visualizeTries").mkdir(exist_ok=True)
    save_path = "visualizeTries/border_calibration.png"
    cv2.imwrite(save_path, screenshot)

    print(f"\n{'='*80}")
    print(f"✅ Calibration screenshot saved: {save_path}")
    print(f"{'='*80}")
    print("\nHOW TO ADJUST BORDERS:")
    print("\n1. Open the saved image: visualizeTries/border_calibration.png")
    print("\n2. Check if the colored borders align with your task cards:")
    print("   - Borders should tightly fit around each card")
    print("   - Corner markers should be at the card corners")
    print("   - Cards should not overlap")
    print("\n3. Adjust values in detection_config.py:")
    print("   - CARD_WIDTH:   Make wider/narrower to fit card width")
    print("   - CARD_HEIGHT:  Make taller/shorter to fit card height")
    print("   - CARD_START_X: Move left (decrease) or right (increase)")
    print("   - CARD_START_Y: Move up (decrease) or down (increase)")
    print("   - CARD_SPACING: Increase if cards overlap, decrease if gap too large")
    print("\n4. Re-run this script to verify your changes:")
    print("   python calibrate_borders.py")
    print(f"\n{'='*80}")


def calibrate_detection_zone():
    """Calibrate the material detection zone within cards."""
    print("\n" + "="*80)
    print("MATERIAL DETECTION ZONE CALIBRATION")
    print("="*80)
    print("\nThis shows where the script will look for material numbers.")
    print("\nInstructions:")
    print("1. First calibrate borders using the main tool")
    print("2. Then use test_complete_detection.py to see the detection zone")
    print("3. Adjust material_y_start and material_y_end in test_complete_detection.py")
    print("\nCurrent detection zone settings:")

    try:
        from detection_config import MATERIAL_ZONE_START, MATERIAL_ZONE_END
        print(f"  MATERIAL_ZONE_START = {MATERIAL_ZONE_START:.2f} (start at {MATERIAL_ZONE_START*100:.0f}% from top)")
        print(f"  MATERIAL_ZONE_END   = {MATERIAL_ZONE_END:.2f} (end at {MATERIAL_ZONE_END*100:.0f}% from top)")
        print(f"\nThis means the detection zone covers {(MATERIAL_ZONE_END-MATERIAL_ZONE_START)*100:.0f}% of card height")
        print("from the material icons down to just above the DELIVER text.")
    except:
        print("  Could not read current settings from detection_config.py")

    print("\nTo adjust the detection zone:")
    print("  Edit detection_config.py:")
    print("  - MATERIAL_ZONE_START: Decrease to search higher, increase to search lower")
    print("  - MATERIAL_ZONE_END: Increase to search further down, decrease to search less")
    print("\nRun: python test_complete_detection.py to visualize the zone")
    print("="*80)


if __name__ == "__main__":
    draw_adjustable_borders()
    print("\n")
    calibrate_detection_zone()
