#!/usr/bin/env python3
"""
Visualization Script for Game Automation
Shows all buttons, detection areas, and zones with labels.
"""

import cv2
import numpy as np
import pyautogui
from pathlib import Path
import json

# Import detection configuration
from detection_config import (
    CARD_WIDTH, CARD_HEIGHT, CARD_START_X, CARD_START_Y, CARD_SPACING,
    MATERIAL_ZONE_START, MATERIAL_ZONE_END,
    DELIVER_ZONE_START, DELIVER_ZONE_END, DELIVER_ZONE_LEFT, DELIVER_ZONE_RIGHT,
    TRAIN_CAPACITY_ZONE_TOP, TRAIN_CAPACITY_ZONE_BOTTOM,
    TRAIN_CAPACITY_ZONE_LEFT, TRAIN_CAPACITY_ZONE_RIGHT, TRAIN_CAPACITY_GAP,
    OPERATOR_COUNT_OFFSET_X, OPERATOR_COUNT_ZONE_WIDTH,
    OPERATOR_COUNT_OFFSET_Y, OPERATOR_COUNT_ZONE_HEIGHT,
    CLICK_OFFSET_Y
)

from window_manager import WindowManager
from game_area_cache import load_last_game_area
from interactive_setup import load_or_setup_game_area


def draw_text_with_bg(img, text, pos, font_scale=0.6, thickness=2,
                      text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """Draw text with background for better visibility."""
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    x, y = pos

    # Draw background rectangle
    cv2.rectangle(img,
                  (x - 5, y - text_height - 5),
                  (x + text_width + 5, y + baseline + 5),
                  bg_color, -1)

    # Draw text
    cv2.putText(img, text, (x, y), font, font_scale, text_color, thickness)


def visualize_all_areas():
    """Create visualization showing all detection areas and buttons."""

    # Load or setup game area interactively
    game_area = load_or_setup_game_area(force_setup=False, save_to_cache=True)

    if not game_area:
        print("\n❌ Setup cancelled or failed.")
        return

    # Initialize window manager
    wm = WindowManager(use_window_mode=True)
    wm.set_manual_window(
        game_area['x'],
        game_area['y'],
        game_area['width'],
        game_area['height']
    )

    window_width = wm.window_width
    window_height = wm.window_height
    window_x = wm.window_x
    window_y = wm.window_y

    # Get scale factor for Retina displays
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_height, screenshot_width = screenshot_np.shape[:2]
    screen_width, screen_height = pyautogui.size()
    scale_factor = screenshot_width / screen_width

    print(f"\nScale factor: {scale_factor}")
    print(f"Screenshot size: {screenshot_width}x{screenshot_height}")
    print(f"Screen size: {screen_width}x{screen_height}")
    print(f"Window: ({window_x}, {window_y}) {window_width}x{window_height}")

    # Convert to OpenCV format
    img = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # Create overlay
    overlay = img.copy()

    # ========================================================================
    # 1. DRAW TASK CARDS
    # ========================================================================
    print("\n=== Drawing Task Cards ===")

    card_width = int(CARD_WIDTH * window_width)
    card_height = int(CARD_HEIGHT * window_height)
    start_x = int(CARD_START_X * window_width) + window_x
    start_y = int(CARD_START_Y * window_height) + window_y
    spacing = int(CARD_SPACING * window_width)

    for i in range(5):
        x = start_x + (i * spacing)
        y = start_y

        # Check bounds
        if x + card_width > window_x + window_width:
            break

        # Scale for drawing
        sx = int(x * scale_factor)
        sy = int(y * scale_factor)
        sw = int(card_width * scale_factor)
        sh = int(card_height * scale_factor)

        # Draw card border (blue)
        cv2.rectangle(overlay, (sx, sy), (sx + sw, sy + sh), (255, 200, 0), 3)

        # Label
        draw_text_with_bg(overlay, f"Task Card {i+1}", (sx + 10, sy + 30),
                         text_color=(255, 200, 0), bg_color=(0, 0, 0))

        # Draw material detection zone (cyan)
        mat_y_start = int(y + card_height * MATERIAL_ZONE_START)
        mat_y_end = int(y + card_height * MATERIAL_ZONE_END)

        smy1 = int(mat_y_start * scale_factor)
        smy2 = int(mat_y_end * scale_factor)

        cv2.rectangle(overlay, (sx, smy1), (sx + sw, smy2), (255, 255, 0), 2)
        draw_text_with_bg(overlay, "Material Zone", (sx + 10, smy1 + 20),
                         font_scale=0.5, text_color=(255, 255, 0))

        # Draw deliver detection zone (green)
        del_y_start = int(y + card_height * DELIVER_ZONE_START)
        del_y_end = int(y + card_height * DELIVER_ZONE_END)
        del_x_start = int(x + card_width * DELIVER_ZONE_LEFT)
        del_x_end = int(x + card_width * DELIVER_ZONE_RIGHT)

        sdy1 = int(del_y_start * scale_factor)
        sdy2 = int(del_y_end * scale_factor)
        sdx1 = int(del_x_start * scale_factor)
        sdx2 = int(del_x_end * scale_factor)

        cv2.rectangle(overlay, (sdx1, sdy1), (sdx2, sdy2), (0, 255, 0), 2)
        draw_text_with_bg(overlay, "Deliver Zone", (sdx1 + 5, sdy1 + 20),
                         font_scale=0.5, text_color=(0, 255, 0))

    print(f"Drew {min(5, (window_x + window_width - start_x) // spacing)} task cards")

    # ========================================================================
    # 2. DRAW TRAIN CAPACITY ZONES
    # ========================================================================
    print("\n=== Drawing Train Capacity Zones ===")

    for train_idx in range(4):
        train_left = TRAIN_CAPACITY_ZONE_LEFT + (train_idx * TRAIN_CAPACITY_GAP)

        # Check bounds
        if train_left >= 1.0:
            break

        train_x1 = int((window_x + train_left * window_width) * scale_factor)
        train_x2 = int((window_x + TRAIN_CAPACITY_ZONE_RIGHT * window_width + train_idx * TRAIN_CAPACITY_GAP * window_width) * scale_factor)
        train_y1 = int((window_y + TRAIN_CAPACITY_ZONE_TOP * window_height) * scale_factor)
        train_y2 = int((window_y + TRAIN_CAPACITY_ZONE_BOTTOM * window_height) * scale_factor)

        # Draw train capacity zone (magenta)
        cv2.rectangle(overlay, (train_x1, train_y1), (train_x2, train_y2), (255, 0, 255), 2)
        draw_text_with_bg(overlay, f"Train {train_idx+1}", (train_x1 + 5, train_y1 + 20),
                         font_scale=0.5, text_color=(255, 0, 255))

    print(f"Drew train capacity zones")

    # ========================================================================
    # 3. DRAW OPERATOR COUNT ZONE (if operator icon template exists)
    # ========================================================================
    print("\n=== Looking for Operator Icon ===")

    operator_icon_path = "Templates/OperatorIcon.png"
    if Path(operator_icon_path).exists():
        # Try to find operator icon
        from template_matcher import find_template_on_screen

        operator_match = find_template_on_screen(operator_icon_path, threshold=0.6)

        if operator_match:
            op_x = operator_match['x']
            op_y = operator_match['y']

            print(f"Found operator icon at ({op_x}, {op_y})")

            # Calculate operator count zone
            count_x1 = int((op_x + OPERATOR_COUNT_OFFSET_X * screen_width) * scale_factor)
            count_x2 = int((op_x + OPERATOR_COUNT_OFFSET_X * screen_width + OPERATOR_COUNT_ZONE_WIDTH * screen_width) * scale_factor)
            count_y1 = int((op_y + OPERATOR_COUNT_OFFSET_Y * screen_height) * scale_factor)
            count_y2 = int((op_y + OPERATOR_COUNT_ZONE_HEIGHT * screen_height) * scale_factor)

            # Draw operator count zone (orange)
            cv2.rectangle(overlay, (count_x1, count_y1), (count_x2, count_y2), (0, 165, 255), 2)
            draw_text_with_bg(overlay, "Operator Count", (count_x1 + 5, count_y1 - 10),
                             font_scale=0.5, text_color=(0, 165, 255))

            # Draw operator icon location
            op_sx = int(op_x * scale_factor)
            op_sy = int(op_y * scale_factor)
            cv2.circle(overlay, (op_sx, op_sy), 15, (0, 165, 255), 3)
        else:
            print("Operator icon not found on screen")

    # ========================================================================
    # 4. FIND AND MARK TEMPLATE BUTTONS
    # ========================================================================
    print("\n=== Finding Template Buttons ===")

    # Load UI coordinates
    ui_coords_path = "ui_coordinates.json"
    if Path(ui_coords_path).exists():
        with open(ui_coords_path, 'r') as f:
            ui_coords = json.load(f)

        # Draw saved element positions
        for element_name, element_data in ui_coords.get('elements', {}).items():
            if element_data.get('x') is not None and element_data.get('y') is not None:
                ex = element_data['x']
                ey = element_data['y']
                ew = element_data.get('width', 50)
                eh = element_data.get('height', 50)

                print(f"Drawing {element_name} at ({ex}, {ey})")

                # Scale
                sex = int(ex * scale_factor)
                sey = int(ey * scale_factor)
                sew = int(ew * scale_factor)
                seh = int(eh * scale_factor)

                # Draw rectangle (red)
                cv2.rectangle(overlay, (sex, sey), (sex + sew, sey + seh), (0, 0, 255), 3)
                draw_text_with_bg(overlay, element_name.replace('_', ' ').title(),
                                 (sex, sey - 10), text_color=(0, 0, 255))

    # Try to find other buttons with template matching
    templates_to_find = [
        ("Templates/Storage.png", "Storage Button", (128, 0, 128)),
        ("Templates/DispatchButton.png", "Dispatch Button", (0, 255, 255)),
        ("Templates/CollectButtonTask.png", "Collect Button (Task)", (255, 128, 0)),
        ("Templates/CollectButtonOperator.png", "Collect Button (Operator)", (255, 128, 128)),
    ]

    from template_matcher import find_template_on_screen

    for template_path, label, color in templates_to_find:
        if Path(template_path).exists():
            match = find_template_on_screen(template_path, threshold=0.6)
            if match:
                mx = match['x']
                my = match['y']
                print(f"Found {label} at ({mx}, {my})")

                smx = int(mx * scale_factor)
                smy = int(my * scale_factor)

                cv2.circle(overlay, (smx, smy), 20, color, 3)
                draw_text_with_bg(overlay, label, (smx + 25, smy),
                                 text_color=color)

    # ========================================================================
    # 5. BLEND AND SAVE
    # ========================================================================

    # Blend overlay with original
    alpha = 0.7
    output = cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)

    # Add legend
    legend_y = 50
    legend_x = 50

    legend_items = [
        ("Task Cards", (255, 200, 0)),
        ("Material Zone", (255, 255, 0)),
        ("Deliver Zone", (0, 255, 0)),
        ("Train Capacity", (255, 0, 255)),
        ("Operator Count", (0, 165, 255)),
        ("Saved Buttons", (0, 0, 255)),
    ]

    for i, (label, color) in enumerate(legend_items):
        y = legend_y + i * 35
        cv2.rectangle(output, (legend_x, y), (legend_x + 30, y + 20), color, -1)
        draw_text_with_bg(output, label, (legend_x + 40, y + 17),
                         font_scale=0.6, text_color=(255, 255, 255))

    # Add title
    title = "Game Automation - All Areas & Buttons"
    draw_text_with_bg(output, title, (screenshot_width // 2 - 300, 40),
                     font_scale=1.2, thickness=3, text_color=(255, 255, 255), bg_color=(0, 0, 128))

    # Add info text
    info_y = screenshot_height - 100
    info_lines = [
        f"Window: ({window_x}, {window_y}) {window_width}x{window_height}",
        f"Scale Factor: {scale_factor:.2f}",
        f"Click Offset Y: {CLICK_OFFSET_Y*100:.1f}% ({int(CLICK_OFFSET_Y*window_height)}px)"
    ]

    for i, line in enumerate(info_lines):
        draw_text_with_bg(output, line, (legend_x, info_y + i * 30),
                         font_scale=0.5, text_color=(255, 255, 255))

    # Save
    output_dir = Path("visualizeTries")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "all_areas_labeled.png"

    cv2.imwrite(str(output_path), output)

    print(f"\n{'='*60}")
    print(f"Visualization saved to: {output_path}")
    print(f"{'='*60}")
    print(f"\nOpen the image to see all labeled areas and buttons!")

    # Also save a zoomed version of task cards
    if start_x >= 0 and start_y >= 0:
        # Crop to task card area
        crop_x1 = int(start_x * scale_factor) - 50
        crop_x2 = int((start_x + 3 * spacing + card_width) * scale_factor) + 50
        crop_y1 = int(start_y * scale_factor) - 50
        crop_y2 = int((start_y + card_height) * scale_factor) + 50

        # Clamp to image bounds
        crop_x1 = max(0, crop_x1)
        crop_y1 = max(0, crop_y1)
        crop_x2 = min(screenshot_width, crop_x2)
        crop_y2 = min(screenshot_height, crop_y2)

        task_cards_zoom = output[crop_y1:crop_y2, crop_x1:crop_x2]
        zoom_path = output_dir / "task_cards_zoom.png"
        cv2.imwrite(str(zoom_path), task_cards_zoom)
        print(f"Task cards zoom saved to: {zoom_path}")


def main():
    """Main entry point."""
    print("="*60)
    print("Game Automation Area Visualization")
    print("="*60)
    print("\nThis script will:")
    print("  1. Ask you to mark the game window corners")
    print("  2. Create a labeled visualization showing:")
    print("     - Task card borders and detection zones")
    print("     - Material and deliver detection areas")
    print("     - Train capacity zones")
    print("     - Operator count zone")
    print("     - All detected buttons")
    print("\n" + "="*60)
    print()

    visualize_all_areas()

    print("\n" + "="*60)
    print("Visualization Complete!")
    print("="*60)
    print("Check the output files in 'visualizeTries/' directory:")
    print("  - all_areas_labeled.png")
    print("  - task_cards_zoom.png")
    print("="*60)


if __name__ == "__main__":
    main()
