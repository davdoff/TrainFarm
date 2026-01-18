#!/usr/bin/env python3
"""
Real-time Visualization Helper
Shows where the automation would click in real-time.
Run this while manually testing to see what areas are being detected.
"""

import cv2
import numpy as np
import pyautogui
from pathlib import Path
import time

from detection_config import *
from window_manager import WindowManager
from game_area_cache import load_last_game_area
from task_card_detector import TaskCardDetector
from interactive_setup import load_or_setup_game_area


def get_mouse_position_info(wm: WindowManager):
    """Get information about current mouse position."""
    mouse_x, mouse_y = pyautogui.position()

    # Check if mouse is in game window
    if (wm.window_x <= mouse_x <= wm.window_x + wm.window_width and
        wm.window_y <= mouse_y <= wm.window_y + wm.window_height):

        # Convert to relative coordinates
        rel_x, rel_y = wm.to_relative_coords(mouse_x, mouse_y)

        return {
            'in_window': True,
            'abs': (mouse_x, mouse_y),
            'rel': (rel_x, rel_y),
            'rel_percent': (f"{rel_x:.3f}", f"{rel_y:.3f}")
        }
    else:
        return {'in_window': False, 'abs': (mouse_x, mouse_y)}


def draw_crosshair(img, x, y, color=(0, 255, 0), size=20):
    """Draw a crosshair at position."""
    cv2.line(img, (x - size, y), (x + size, y), color, 2)
    cv2.line(img, (x, y - size), (x, y + size), color, 2)
    cv2.circle(img, (x, y), 5, color, -1)


def realtime_visualization():
    """Run real-time visualization loop."""

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

    print("="*60)
    print("Real-time Visualization Mode")
    print("="*60)
    print(f"Game Window: ({wm.window_x}, {wm.window_y}) {wm.window_width}x{wm.window_height}")
    print("\nControls:")
    print("  - Move mouse over game area to see position info")
    print("  - Press 'q' to quit")
    print("  - Press 's' to save current screenshot")
    print("  - Press 't' to show task cards")
    print("="*60)
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    show_task_cards = False
    detector = TaskCardDetector(window_manager=wm)

    while True:
        # Capture game window
        screenshot = wm.capture_window()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Get mouse position info
        mouse_info = get_mouse_position_info(wm)

        # Draw overlay
        overlay = img.copy()

        if show_task_cards:
            # Draw task card borders
            card_width = int(CARD_WIDTH * wm.window_width)
            card_height = int(CARD_HEIGHT * wm.window_height)
            start_x = int(CARD_START_X * wm.window_width)
            start_y = int(CARD_START_Y * wm.window_height)
            spacing = int(CARD_SPACING * wm.window_width)

            for i in range(5):
                x = start_x + (i * spacing)
                y = start_y

                if x + card_width > wm.window_width:
                    break

                # Draw card border
                cv2.rectangle(overlay, (x, y), (x + card_width, y + card_height), (255, 200, 0), 2)

                # Draw material zone
                mat_y_start = int(y + card_height * MATERIAL_ZONE_START)
                mat_y_end = int(y + card_height * MATERIAL_ZONE_END)
                cv2.rectangle(overlay, (x, mat_y_start), (x + card_width, mat_y_end), (255, 255, 0), 1)

                # Draw deliver zone
                del_y_start = int(y + card_height * DELIVER_ZONE_START)
                del_y_end = int(y + card_height * DELIVER_ZONE_END)
                del_x_start = int(x + card_width * DELIVER_ZONE_LEFT)
                cv2.rectangle(overlay, (del_x_start, del_y_start), (x + card_width, del_y_end), (0, 255, 0), 1)

        # Blend overlay
        alpha = 0.3
        img = cv2.addWeighted(img, 1 - alpha, overlay, alpha, 0)

        # Draw mouse crosshair if in window
        if mouse_info['in_window']:
            mouse_rel_x = int(mouse_info['rel'][0] * wm.window_width)
            mouse_rel_y = int(mouse_info['rel'][1] * wm.window_height)
            draw_crosshair(img, mouse_rel_x, mouse_rel_y, (0, 255, 255), 30)

        # Draw info panel
        info_bg_height = 180 if mouse_info['in_window'] else 120
        cv2.rectangle(img, (0, 0), (500, info_bg_height), (0, 0, 0), -1)

        # Draw text
        y_offset = 25
        cv2.putText(img, "Real-time Visualization", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        y_offset += 30
        cv2.putText(img, f"Window: {wm.window_width}x{wm.window_height}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        y_offset += 25
        if mouse_info['in_window']:
            cv2.putText(img, f"Mouse Abs: {mouse_info['abs']}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 25
            cv2.putText(img, f"Mouse Rel: ({mouse_info['rel_percent'][0]}, {mouse_info['rel_percent'][1]})",
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 25
            cv2.putText(img, f"Mouse Px:  ({int(mouse_info['rel'][0] * wm.window_width)}, {int(mouse_info['rel'][1] * wm.window_height)})",
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(img, "Mouse outside game window", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)

        y_offset += 30
        task_cards_text = "ON" if show_task_cards else "OFF"
        cv2.putText(img, f"Task Cards: {task_cards_text} (press 't')", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        y_offset += 25
        cv2.putText(img, "Press 'q' to quit, 's' to save", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Show the image
        cv2.imshow("Real-time Visualization", img)

        # Handle key presses
        key = cv2.waitKey(100) & 0xFF

        if key == ord('q'):
            print("\nQuitting...")
            break
        elif key == ord('s'):
            output_dir = Path("visualizeTries")
            output_dir.mkdir(exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"realtime_{timestamp}.png"
            cv2.imwrite(str(filename), img)
            print(f"\nScreenshot saved: {filename}")
        elif key == ord('t'):
            show_task_cards = not show_task_cards
            print(f"\nTask cards overlay: {'ON' if show_task_cards else 'OFF'}")

    cv2.destroyAllWindows()


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("Real-time Visualization Helper")
    print("="*60)
    print("\nThis tool will:")
    print("  1. Ask you to mark the game window corners")
    print("  2. Show real-time view with:")
    print("     - Current mouse position (absolute and relative)")
    print("     - Task card overlays (toggle with 't')")
    print("     - Live view of the game window")
    print("\n" + "="*60)
    print()

    try:
        realtime_visualization()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
