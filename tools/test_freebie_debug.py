#!/usr/bin/env python3
"""
Quick test to compare find_template_on_screen vs find_all_matches
"""

import time
from src.detectors.template_matcher import find_template_on_screen, find_all_matches

template_path = "Templates/ui/Freebie.png"

print("="*60)
print("FREEBIE MATCHING DEBUG TEST")
print("="*60)
print(f"Template: {template_path}")
print("\nSwitch to game window with freebies visible...")
print("Testing in 3 seconds...\n")

for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

print("\n--- Testing find_template_on_screen (single match) ---")
thresholds = [0.8, 0.7, 0.6, 0.5, 0.4]

for threshold in thresholds:
    match = find_template_on_screen(template_path, threshold=threshold)
    if match:
        print(f"✓ Threshold {threshold}: FOUND at ({match['x']}, {match['y']}) - confidence {match['confidence']:.3f}")
    else:
        print(f"✗ Threshold {threshold}: NOT FOUND")

print("\n--- Testing find_all_matches (multiple matches) ---")

for threshold in thresholds:
    matches = find_all_matches(template_path, threshold=threshold)
    if matches:
        print(f"✓ Threshold {threshold}: FOUND {len(matches)} match(es)")
        for i, m in enumerate(matches, 1):
            print(f"    Match {i}: ({m['x']}, {m['y']}) - confidence {m['confidence']:.3f}")
    else:
        print(f"✗ Threshold {threshold}: NOT FOUND")

print("\n" + "="*60)
print("If find_template_on_screen works but find_all_matches doesn't,")
print("there's a bug in find_all_matches implementation.")
print("="*60)
