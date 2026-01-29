#!/usr/bin/env python3
"""
Visualization Script - Shows all detection zones
Simple fullscreen visualization of task cards, material zones, etc.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
import pyautogui
import time

from src.config.detection_config import (
    CARD_WIDTH, CARD_HEIGHT, CARD_START_X, CARD_START_Y, CARD_SPACING,
    MATERIAL_ZONE_START, MATERIAL_ZONE_END,
    DELIVER_ZONE_START, DELIVER_ZONE_END, DELIVER_ZONE_LEFT, DELIVER_ZONE_RIGHT,
    TRAIN_CAPACITY_ZONE_TOP, TRAIN_CAPACITY_ZONE_BOTTOM,
    TRAIN_CAPACITY_ZONE_LEFT, TRAIN_CAPACITY_ZONE_RIGHT, TRAIN_CAPACITY_GAP,
    CLICK_OFFSET_Y
)


def draw_text_with_bg(img, text, pos, font_scale=0.6, thickness=2,
                       text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """Draw text with background rectangle for better visibility."""
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    # Draw background rectangle
    x, y = pos
    cv2.rectangle(img,
                  (x - 5, y - text_height - 5),
                  (x + text_width + 5, y + baseline + 5),
                  bg_color, -1)

    # Draw text
    cv2.putText(img, text, pos, font, font_scale, text_color, thickness)


def visualize_all_areas():
    """Create visualization showing all detection areas."""

    print("\n" + "="*60)
    print("DETECTION ZONES VISUALIZATION")
    print("="*60)
    print("\nSwitch to your game window...")
    print("Taking screenshot in 3 seconds...\n")

    # Countdown
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    print("📸 Capturing screenshot...\n")

    # Take fullscreen screenshot
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    img = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()

    # Get scale factor for Retina/HiDPI displays
    screenshot_height, screenshot_width = img.shape[:2]
    scale_x = screenshot_width / screen_width
    scale_y = screenshot_height / screen_height
    scale_factor = (scale_x + scale_y) / 2

    print(f"Screen size: {screen_width}x{screen_height}")
    print(f"Screenshot size: {screenshot_width}x{screenshot_height}")
    print(f"Scale factor: {scale_factor}")

    # Convert window-relative percentages to absolute pixels
    # Assuming fullscreen, so window = screen
    window_width = screen_width
    window_height = screen_height

    # ===== DRAW TASK CARDS =====
    print("\n📋 Drawing task cards...")

    # Calculate card dimensions once
    card_w = int(window_width * CARD_WIDTH)
    card_h = int(window_height * CARD_HEIGHT)
    card_y = int(window_height * CARD_START_Y)

    # Draw cards until they go off screen (same logic as detector)
    card_num = 0
    for i in range(5):  # Try up to 5
        card_x = int(window_width * (CARD_START_X + i * CARD_SPACING))

        # Stop if card goes off screen
        if card_x + card_w > window_width:
            print(f"   Card {i+1} would be off screen, stopping at {card_num} cards")
            break

        card_num += 1

        # Scale to screenshot coordinates
        x1 = int(card_x * scale_factor)
        y1 = int(card_y * scale_factor)
        x2 = int((card_x + card_w) * scale_factor)
        y2 = int((card_y + card_h) * scale_factor)

        # Draw card border
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 100, 0), 3)  # Blue

        # Draw label
        label_pos = (x1 + 10, y1 + 30)
        draw_text_with_bg(img, f"Task Card {i+1}", label_pos,
                         font_scale=0.7, text_color=(255, 255, 255), bg_color=(255, 100, 0))

        # ===== DRAW MATERIAL ZONE (within each card) =====
        mat_y_start = int(card_h * MATERIAL_ZONE_START)
        mat_y_end = int(card_h * MATERIAL_ZONE_END)

        mat_y1 = int((card_y + mat_y_start) * scale_factor)
        mat_y2 = int((card_y + mat_y_end) * scale_factor)

        cv2.rectangle(img, (x1, mat_y1), (x2, mat_y2), (0, 255, 0), 2)  # Green
        draw_text_with_bg(img, "Material Zone", (x1 + 10, mat_y1 + 25),
                         font_scale=0.5, text_color=(255, 255, 255), bg_color=(0, 200, 0))

        # ===== DRAW DELIVER ZONE (within each card) =====
        del_y_start = int(card_h * DELIVER_ZONE_START)
        del_y_end = int(card_h * DELIVER_ZONE_END)
        del_x_start = int(card_w * DELIVER_ZONE_LEFT)
        del_x_end = int(card_w * DELIVER_ZONE_RIGHT)

        del_x1 = int((card_x + del_x_start) * scale_factor)
        del_x2 = int((card_x + del_x_end) * scale_factor)
        del_y1 = int((card_y + del_y_start) * scale_factor)
        del_y2 = int((card_y + del_y_end) * scale_factor)

        cv2.rectangle(img, (del_x1, del_y1), (del_x2, del_y2), (0, 255, 255), 2)  # Yellow
        draw_text_with_bg(img, "Deliver Zone", (del_x1 + 10, del_y1 + 25),
                         font_scale=0.5, text_color=(0, 0, 0), bg_color=(0, 255, 255))

    # ===== DRAW TRAIN CAPACITY ZONES =====
    print("🚂 Drawing train zones...")
    num_trains = 4
    for i in range(num_trains):
        # Calculate train zone position
        train_left = TRAIN_CAPACITY_ZONE_LEFT + (i * TRAIN_CAPACITY_GAP)
        train_right = TRAIN_CAPACITY_ZONE_RIGHT + (i * TRAIN_CAPACITY_GAP)

        train_x1 = int(window_width * train_left * scale_factor)
        train_x2 = int(window_width * train_right * scale_factor)
        train_y1 = int(window_height * TRAIN_CAPACITY_ZONE_TOP * scale_factor)
        train_y2 = int(window_height * TRAIN_CAPACITY_ZONE_BOTTOM * scale_factor)

        cv2.rectangle(img, (train_x1, train_y1), (train_x2, train_y2), (255, 0, 255), 2)  # Purple
        draw_text_with_bg(img, f"Train {i+1}", (train_x1 + 5, train_y1 + 20),
                         font_scale=0.4, text_color=(255, 255, 255), bg_color=(200, 0, 200))

    # ===== DRAW CLICK OFFSET INDICATOR =====
    print("🎯 Drawing click offset indicators...")
    # Show what CLICK_OFFSET_Y means (on first task card)
    card_x = int(window_width * CARD_START_X)
    card_y = int(window_height * CARD_START_Y)
    card_h = int(window_height * CARD_HEIGHT)

    # Material zone middle (where numbers would be)
    mat_y_middle = int(card_h * ((MATERIAL_ZONE_START + MATERIAL_ZONE_END) / 2))
    material_center_y = int((card_y + mat_y_middle) * scale_factor)

    # Click offset (where automation actually clicks)
    click_offset_pixels = int(window_height * CLICK_OFFSET_Y)
    click_y = int((card_y + mat_y_middle + click_offset_pixels) * scale_factor)

    # Draw horizontal lines
    card_x_scaled = int(card_x * scale_factor)
    cv2.line(img, (card_x_scaled, material_center_y),
             (card_x_scaled + 150, material_center_y), (0, 0, 255), 2)  # Red line at number
    cv2.line(img, (card_x_scaled, click_y),
             (card_x_scaled + 150, click_y), (255, 0, 0), 2)  # Blue line at click

    # Draw arrow showing offset
    cv2.arrowedLine(img, (card_x_scaled + 160, material_center_y),
                    (card_x_scaled + 160, click_y), (0, 255, 0), 3, tipLength=0.3)

    draw_text_with_bg(img, "Number here", (card_x_scaled + 10, material_center_y - 10),
                     font_scale=0.5, text_color=(255, 255, 255), bg_color=(0, 0, 255))
    draw_text_with_bg(img, "Click here", (card_x_scaled + 10, click_y + 20),
                     font_scale=0.5, text_color=(255, 255, 255), bg_color=(255, 0, 0))

    # ===== SAVE IMAGE =====
    output_dir = PROJECT_ROOT / "visualizeTries"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "all_detection_zones.png"
    cv2.imwrite(str(output_path), img)

    print(f"\n✅ Visualization saved to: {output_path}")
    print("\nColor Legend:")
    print("  🔵 Blue borders = Task cards")
    print("  🟢 Green boxes = Material detection zones")
    print("  🟡 Yellow boxes = Deliver amount zones")
    print("  🟣 Purple boxes = Train capacity zones")
    print("  🔴 Red line = Number position")
    print("  🔵 Blue line = Click position")
    print("  🟢 Green arrow = Click offset")
    print("\n" + "="*60)


def main():
    """Main entry point."""
    try:
        visualize_all_areas()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
