#!/usr/bin/env python3
"""
Test Train Status OCR Detection

This tool helps you test and debug the OCR-based train status detection.
It captures the train status text region and shows you what text is detected.

Usage:
    1. Start a task or material generation to show the train status text
    2. Run this script
    3. Review the OCR output and adjust the region if needed

Prerequisites:
    - Configure TRAIN_STATUS_TEXT_* values in src/config/detection_config.py
    - Use tools/configure_regions.py to define the region precisely
"""

import cv2
import numpy as np
import pyautogui
import pytesseract
import time
from pathlib import Path

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.detection_config import (
    TRAIN_STATUS_TEXT_LEFT,
    TRAIN_STATUS_TEXT_TOP,
    TRAIN_STATUS_TEXT_RIGHT,
    TRAIN_STATUS_TEXT_BOTTOM,
    TRAIN_STATUS_MATCH_THRESHOLD
)
from src.core.train_dispatcher import TrainDispatcher


def visualize_train_status_region():
    """Capture and visualize the train status text region with OCR results."""
    print("\n" + "="*60)
    print("Train Status OCR Test")
    print("="*60)
    print("\nThis tool will:")
    print("1. Capture the train status text region")
    print("2. Show OCR results from multiple preprocessing methods")
    print("3. Display the region with detected text")
    print()

    # Get screen size
    screen_width, screen_height = pyautogui.size()

    # Calculate pixel coordinates
    x1 = int(screen_width * TRAIN_STATUS_TEXT_LEFT)
    y1 = int(screen_height * TRAIN_STATUS_TEXT_TOP)
    x2 = int(screen_width * TRAIN_STATUS_TEXT_RIGHT)
    y2 = int(screen_height * TRAIN_STATUS_TEXT_BOTTOM)

    print(f"Screen size: {screen_width}x{screen_height}")
    print(f"Region config (percentages):")
    print(f"  LEFT: {TRAIN_STATUS_TEXT_LEFT:.4f}")
    print(f"  TOP: {TRAIN_STATUS_TEXT_TOP:.4f}")
    print(f"  RIGHT: {TRAIN_STATUS_TEXT_RIGHT:.4f}")
    print(f"  BOTTOM: {TRAIN_STATUS_TEXT_BOTTOM:.4f}")
    print()
    print(f"Region coordinates (pixels): ({x1}, {y1}) to ({x2}, {y2})")
    print(f"Region size: {x2-x1}x{y2-y1}")
    print()

    input("Position game to show train status text, then press ENTER...")

    print("\nSwitching to game in 2 seconds...")
    time.sleep(2)

    # Capture screenshot
    print("Capturing screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Extract region
    roi = screenshot[y1:y2, x1:x2]

    # Save original ROI
    cv2.imwrite("train_status_region_original.png", roi)
    print("✓ Saved train_status_region_original.png")

    # Preprocess for OCR
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Try multiple preprocessing techniques
    print("\n" + "="*60)
    print("OCR Results from Different Preprocessing Methods")
    print("="*60)

    methods = []

    # 1. Original grayscale
    methods.append(("Original Grayscale", gray))

    # 2. Simple threshold
    _, thresh1 = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    methods.append(("Simple Threshold (150)", thresh1))

    # 3. Adaptive threshold
    thresh2 = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    methods.append(("Adaptive Threshold", thresh2))

    # 4. Otsu's threshold
    _, thresh3 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    methods.append(("Otsu Threshold", thresh3))

    # 5. Inverted (white text on black background)
    inverted = cv2.bitwise_not(gray)
    methods.append(("Inverted", inverted))

    all_texts = []

    for i, (name, img) in enumerate(methods):
        # Save preprocessed image
        filename = f"train_status_region_{i}_{name.replace(' ', '_').lower()}.png"
        cv2.imwrite(filename, img)

        try:
            # OCR with config optimized for text
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(img, config=custom_config)
            text = text.strip()

            print(f"\n{i+1}. {name}:")
            print(f"   File: {filename}")
            if text:
                print(f"   Text: '{text}'")
                all_texts.append(text)
            else:
                print("   Text: (empty)")

        except Exception as e:
            print(f"   Error: {e}")

    # Test with TrainDispatcher
    print("\n" + "="*60)
    print("Testing with TrainDispatcher")
    print("="*60)

    dispatcher = TrainDispatcher()

    print("\n1. Reading status text:")
    status_text = dispatcher._read_train_status_text()
    if status_text:
        print(f"   Detected: '{status_text}'")
    else:
        print("   No text detected")

    print("\n2. Checking if trains available:")
    trains_available = dispatcher.check_trains_available_by_text()
    print(f"   Result: {'AVAILABLE' if trains_available else 'NOT AVAILABLE'}")

    print("\n3. Checking if all trains used:")
    all_used = dispatcher.check_all_trains_used()
    print(f"   Result: {'ALL USED' if all_used else 'TRAINS AVAILABLE'}")

    # Analysis
    print("\n" + "="*60)
    print("Analysis")
    print("="*60)

    if all_texts:
        # Find longest text (usually most complete)
        best_text = max(all_texts, key=len)
        print(f"Best OCR result: '{best_text}'")

        # Check for expected strings
        expected_available = "TAP THE TRAIN TO"
        expected_used = "PLEASE WAIT UNTIL"

        if expected_available.upper() in best_text.upper():
            print(f"✓ Contains '{expected_available}' - Trains available!")
        elif expected_used.upper() in best_text.upper():
            print(f"✓ Contains '{expected_used}' - All trains used!")
        else:
            print("⚠️  Text doesn't clearly match expected patterns")
            print(f"   Expected: '{expected_available}' or '{expected_used}'")
    else:
        print("❌ No text detected in any method!")
        print()
        print("Troubleshooting:")
        print("1. Check if region coordinates are correct")
        print("2. Use tools/configure_regions.py to reconfigure the region")
        print("3. Ensure the text is visible on screen when capturing")
        print("4. Check the saved images to see what was captured")

    # Create visualization
    print("\n" + "="*60)
    print("Creating Visualization")
    print("="*60)

    # Draw rectangle on full screenshot
    vis_screenshot = screenshot.copy()
    cv2.rectangle(vis_screenshot, (x1, y1), (x2, y2), (0, 255, 0), 3)

    # Add label
    label = "Train Status Region"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(vis_screenshot, label, (x1, y1 - 10),
               font, 1, (0, 255, 0), 2)

    # Save
    cv2.imwrite("train_status_visualization.png", vis_screenshot)
    print("✓ Saved train_status_visualization.png")

    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Total images saved: {len(methods) + 2}")
    print("\nFiles created:")
    print("  - train_status_region_original.png")
    for i, (name, _) in enumerate(methods):
        filename = f"train_status_region_{i}_{name.replace(' ', '_').lower()}.png"
        print(f"  - {filename}")
    print("  - train_status_visualization.png")

    if all_texts:
        print("\n✅ OCR working! Review the detected text above.")
    else:
        print("\n⚠️  OCR not detecting text. Review saved images and reconfigure region.")

    print("\nNext steps:")
    print("1. Review the saved images")
    print("2. If region is wrong, use: python tools/configure_regions.py")
    print("3. Copy the generated TRAIN_STATUS_TEXT_* values to detection_config.py")
    print()


def main():
    """Main entry point."""
    visualize_train_status_region()


if __name__ == "__main__":
    main()
