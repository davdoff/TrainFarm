#!/usr/bin/env python3
"""
Debug Task Detection
Shows what the system is finding for tasks.
"""

import time
import cv2
import numpy as np
import pyautogui
from template_matcher import find_template_on_screen, find_all_matches
from pathlib import Path


def main():
    print("="*60)
    print("Debug Task Detection")
    print("="*60)
    print()
    print("This will show what the system detects:")
    print("1. Task button position")
    print("2. 'Available trains' text locations")
    print("3. 'EN ROUTE' text locations")
    print("4. Where it would click")
    print()

    input("Open the task menu in game, then press ENTER...")

    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    print("\n" + "="*60)
    print("SCANNING")
    print("="*60 + "\n")

    # Find Task button
    print("1. Finding Task button...")
    task_match = find_template_on_screen("Templates/task.png", threshold=0.7)
    if task_match:
        print(f"   ✅ Task button at ({task_match['x']}, {task_match['y']})")
    else:
        print(f"   ❌ Task button NOT found")

    # Find Available trains
    print("\n2. Finding 'Available trains' text...")
    available_matches = find_all_matches("Templates/BottomTaskAvailableTrains.png", threshold=0.7)
    if available_matches:
        print(f"   ✅ Found {len(available_matches)} 'Available trains' text(s):")
        for i, match in enumerate(available_matches):
            print(f"      {i+1}. at ({match['x']}, {match['y']}) - {match['confidence']:.2%} confidence")
    else:
        print(f"   ❌ No 'Available trains' found")
        print(f"   Trying lower threshold (0.5)...")
        available_matches = find_all_matches("Templates/BottomTaskAvailableTrains.png", threshold=0.5)
        if available_matches:
            print(f"   ✅ Found {len(available_matches)} with lower threshold:")
            for i, match in enumerate(available_matches):
                print(f"      {i+1}. at ({match['x']}, {match['y']}) - {match['confidence']:.2%} confidence")

    # Find EN ROUTE
    print("\n3. Finding 'EN ROUTE' text...")
    enroute_matches = find_all_matches("Templates/BottomTaskEnRoute.png", threshold=0.7)
    if enroute_matches:
        print(f"   ✅ Found {len(enroute_matches)} 'EN ROUTE' text(s):")
        for i, match in enumerate(enroute_matches):
            print(f"      {i+1}. at ({match['x']}, {match['y']}) - {match['confidence']:.2%} confidence")
    else:
        print(f"   ❌ No 'EN ROUTE' found")
        print(f"   Trying lower threshold (0.5)...")
        enroute_matches = find_all_matches("Templates/BottomTaskEnRoute.png", threshold=0.5)
        if enroute_matches:
            print(f"   ✅ Found {len(enroute_matches)} with lower threshold:")
            for i, match in enumerate(enroute_matches):
                print(f"      {i+1}. at ({match['x']}, {match['y']}) - {match['confidence']:.2%} confidence")

    # Calculate where it would click
    print("\n4. Calculating click position...")
    if available_matches:
        leftmost = min(available_matches, key=lambda m: m['x'])
        available_x = leftmost['x']
        available_y = leftmost['y']

        # Try different offsets
        print(f"\n   'Available trains' found at ({available_x}, {available_y})")
        print(f"   Possible click positions:")
        print(f"      Option 1: ({available_x}, {available_y - 300}) [300px above]")
        print(f"      Option 2: ({available_x}, {available_y - 250}) [250px above]")
        print(f"      Option 3: ({available_x}, {available_y - 200}) [200px above]")
        print(f"      Option 4: ({available_x}, {available_y - 350}) [350px above]")

    # Create visualization
    print("\n5. Creating visualization...")
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Draw Task button
    if task_match:
        cv2.circle(screenshot, (task_match['x'], task_match['y']), 10, (255, 0, 0), -1)
        cv2.putText(screenshot, "TASK", (task_match['x'] - 30, task_match['y'] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # Draw Available trains
    for match in available_matches:
        cv2.circle(screenshot, (match['x'], match['y']), 10, (0, 255, 0), -1)
        cv2.putText(screenshot, "AVAILABLE", (match['x'] - 50, match['y'] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw potential click positions
        for offset in [200, 250, 300, 350]:
            click_y = match['y'] - offset
            cv2.circle(screenshot, (match['x'], click_y), 5, (0, 255, 255), -1)

    # Draw EN ROUTE
    for match in enroute_matches:
        cv2.circle(screenshot, (match['x'], match['y']), 10, (0, 0, 255), -1)
        cv2.putText(screenshot, "EN ROUTE", (match['x'] - 50, match['y'] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    Path("visualizeTries").mkdir(exist_ok=True)
    viz_path = "visualizeTries/task_detection_debug.png"
    cv2.imwrite(viz_path, screenshot)
    print(f"   ✅ Saved to: {viz_path}")
    print("\n   Legend:")
    print("      🔵 Blue circle = Task button")
    print("      🟢 Green circle = 'Available trains' text")
    print("      🟡 Yellow small circles = Possible click positions")
    print("      🔴 Red circle = 'EN ROUTE' text")

    print("\n" + "="*60)
    print("Debug Complete!")
    print("="*60)
    print(f"\nCheck {viz_path} to see what was detected")


if __name__ == "__main__":
    main()
