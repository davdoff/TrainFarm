#!/usr/bin/env python3
"""
Interactive Window Setup
Reusable functions for marking game window corners.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from src/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pyautogui
import json


def mark_window_corners_interactive():
    """
    Interactive corner marking - same as automation workflow.

    Returns:
        dict with 'x', 'y', 'width', 'height' or None if cancelled
    """
    print("\n" + "="*60)
    print("Game Window Setup")
    print("="*60)
    print("Move your mouse to mark the game boundaries")
    print()

    # Step 1: Top-left corner
    print("STEP 1: Mark TOP-LEFT corner of game")
    print("-" * 60)
    print("Position your mouse at the TOP-LEFT corner of the GAME CANVAS")
    print("(Not the browser window - the actual game area)")
    print()
    input("Press ENTER when ready...")

    top_left = pyautogui.position()
    print(f"✅ Top-left: ({top_left[0]}, {top_left[1]})")
    print()

    # Step 2: Bottom-right corner
    print("STEP 2: Mark BOTTOM-RIGHT corner of game")
    print("-" * 60)
    print("Position your mouse at the BOTTOM-RIGHT corner of the GAME CANVAS")
    print()
    input("Press ENTER when ready...")

    bottom_right = pyautogui.position()
    print(f"✅ Bottom-right: ({bottom_right[0]}, {bottom_right[1]})")
    print()

    # Calculate dimensions
    game_x = top_left[0]
    game_y = top_left[1]
    game_width = bottom_right[0] - top_left[0]
    game_height = bottom_right[1] - top_left[1]

    print("="*60)
    print("Game Area Detected:")
    print("="*60)
    print(f"  Position: ({game_x}, {game_y})")
    print(f"  Size: {game_width} x {game_height}")
    print(f"  Aspect Ratio: {game_width/game_height:.2f}")
    print()

    return {
        'x': game_x,
        'y': game_y,
        'width': game_width,
        'height': game_height
    }


def save_game_area_to_cache(area):
    """
    Save game area to cache file.

    Args:
        area: dict with x, y, width, height
    """
    config = {
        "last_used": "default",
        "saved_configs": {
            "default": area
        }
    }

    config_path = Path("game_area_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Configuration saved to: {config_path}")


def load_or_setup_game_area(force_setup=False, save_to_cache=True):
    """
    Load game area from cache, or setup if not found.

    Args:
        force_setup: If True, always run setup even if cache exists
        save_to_cache: If True, save the setup to cache

    Returns:
        dict with x, y, width, height or None if cancelled
    """
    from src.config.game_area_cache import load_last_game_area

    # Check for cached area
    if not force_setup:
        cached_area = load_last_game_area()

        if cached_area:
            print("\n" + "="*60)
            print("Found Previous Game Area Configuration:")
            print("="*60)
            print(f"  Position: ({cached_area['x']}, {cached_area['y']})")
            print(f"  Size: {cached_area['width']} x {cached_area['height']}")
            print("="*60)
            print()

            use_cached = input("Use these coordinates? (y/n) [y]: ").strip().lower()

            if use_cached != 'n':
                print("✅ Using saved coordinates")
                return cached_area
            else:
                print("\nStarting new setup...")

    # Run interactive setup
    area = mark_window_corners_interactive()

    if area and save_to_cache:
        save_game_area_to_cache(area)

    return area


def quick_test_capture(area):
    """
    Quick test capture to verify window area.

    Args:
        area: dict with x, y, width, height
    """
    print("\n" + "="*60)
    print("Test Capture")
    print("="*60)
    print("Taking a test screenshot in 3 seconds...")
    print("Make sure the game is visible!")
    print()

    import time
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    screenshot = pyautogui.screenshot(region=(
        area['x'], area['y'], area['width'], area['height']
    ))

    # Save test capture
    output_dir = Path("visualizeTries")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "test_capture.png"
    screenshot.save(output_path)

    print(f"\n✅ Test capture saved to: {output_path}")
    print("Open this file to verify it captured the correct game area.")
    print()
