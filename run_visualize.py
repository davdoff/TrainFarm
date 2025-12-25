#!/usr/bin/env python3
"""
Quick script to run template matching with a 5 second delay
"""

import time
from pathlib import Path
from template_matcher import visualize_match, find_template_on_screen

# Create visualizeTries folder if it doesn't exist
output_dir = Path("visualizeTries")
output_dir.mkdir(exist_ok=True)

# Wait for user to press Enter
input("Press ENTER to start (you'll have 5 seconds to set up your screen)...")

print("Starting in 5 seconds...")
for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

print("Taking screenshot and matching...")

# Run the visualization
template_path = "task.png"
output_path = output_dir / "match_result.png"

# First find the match and display info
match = find_template_on_screen(template_path, threshold=0.8)

if match:
    print("\n✓ MATCH FOUND!")
    print(f"  Center coordinates: ({match['x']}, {match['y']})")
    print(f"  Top-left corner: {match['top_left']}")
    print(f"  Bottom-right corner: {match['bottom_right']}")
    print(f"  Confidence: {match['confidence']:.2%}")
    print(f"  Size: {match['width']}x{match['height']} pixels")
else:
    print("\n✗ No match found")
    print("  The template might not be visible on screen")

# Create the visualization
visualize_match(template_path, threshold=0.8, save_path=str(output_path))
print(f"\nVisualization saved to: {output_path}")
