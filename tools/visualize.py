#!/usr/bin/env python3
"""
Main Visualization Script
Simple menu to access all visualization tools.
Each tool will prompt to mark window corners before running.
"""

import subprocess
import sys
from pathlib import Path


def print_menu():
    """Print main menu."""
    print("\n" + "="*60)
    print("Game Automation - Visualization Tools")
    print("="*60)
    print()
    print("Each tool will ask you to mark window corners before running.")
    print("(You can reuse previous coordinates if window hasn't moved)")
    print()
    print("Choose an option:")
    print()
    print("  1. Generate Labeled Screenshot")
    print("     - Shows all areas and buttons with labels")
    print("     - Saves to: visualizeTries/all_areas_labeled.png")
    print()
    print("  2. Real-time Interactive Viewer")
    print("     - Live view with mouse position tracking")
    print("     - Press 't' to toggle overlays, 's' to save, 'q' to quit")
    print()
    print("  3. Quick Test Capture")
    print("     - Just capture the game window to verify setup")
    print("     - Saves to: visualizeTries/test_capture.png")
    print()
    print("  4. Exit")
    print()
    print("="*60)


def run_static_visualization():
    """Run static visualization."""
    print("\n" + "="*60)
    print("Launching Static Visualization...")
    print("="*60)
    print()
    subprocess.run([sys.executable, "visualize_all_areas.py"])


def run_realtime_visualization():
    """Run real-time visualization."""
    print("\n" + "="*60)
    print("Launching Real-time Viewer...")
    print("="*60)
    print()
    subprocess.run([sys.executable, "visualize_realtime.py"])


def run_test_capture():
    """Run quick test capture."""
    print("\n" + "="*60)
    print("Quick Test Capture")
    print("="*60)
    print()

    from interactive_setup import load_or_setup_game_area, quick_test_capture

    # Get game area
    area = load_or_setup_game_area(force_setup=False, save_to_cache=True)

    if area:
        quick_test_capture(area)
    else:
        print("\n❌ Setup cancelled.")

    input("\nPress ENTER to continue...")


def main():
    """Main entry point."""
    print()
    print("="*60)
    print("GAME AUTOMATION VISUALIZATION")
    print("="*60)
    print()
    print("Welcome! This tool helps you visualize and debug")
    print("your game automation setup for windowed browser tabs.")
    print()
    print("HOW IT WORKS:")
    print("  1. Each tool will ask you to mark window corners")
    print("  2. Move your mouse to the top-left of the GAME AREA")
    print("  3. Press ENTER")
    print("  4. Move mouse to bottom-right of GAME AREA")
    print("  5. Press ENTER")
    print("  6. The tool will run using those coordinates")
    print()
    print("If the window hasn't moved, you can reuse saved coords.")
    print("="*60)

    input("\nPress ENTER to continue...")

    while True:
        print_menu()
        choice = input("Enter choice (1-4): ").strip()

        if choice == "1":
            run_static_visualization()
        elif choice == "2":
            run_realtime_visualization()
        elif choice == "3":
            run_test_capture()
        elif choice == "4":
            print("\nGoodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-4.")
            input("\nPress ENTER to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
