#!/usr/bin/env python3
"""
Advanced freebie matching test - shows WHY it's not matching
"""

import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path

template_path = "Templates/ui/Freebie.png"

print("="*60)
print("ADVANCED FREEBIE MATCHING DEBUG")
print("="*60)

# Check template exists
if not Path(template_path).exists():
    print(f"❌ Template not found: {template_path}")
    exit(1)

# Load and analyze template
template = cv2.imread(template_path)
if template is None:
    print(f"❌ Failed to load template")
    exit(1)

print(f"\n📋 Template Info:")
print(f"   Path: {template_path}")
print(f"   Size: {template.shape[1]}x{template.shape[0]} pixels")
print(f"   Channels: {template.shape[2]}")
print(f"   Type: {template.dtype}")

# Analyze template colors
mean_bgr = template.mean(axis=(0,1))
print(f"   Mean color (BGR): [{mean_bgr[0]:.0f}, {mean_bgr[1]:.0f}, {mean_bgr[2]:.0f}]")

print("\n⏱️  Switch to game window with freebies visible...")
print("Taking screenshot in 3 seconds...\n")

for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# Take screenshot
print("📸 Capturing screenshot...")
screenshot = pyautogui.screenshot()
screenshot_np = np.array(screenshot)
screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

print(f"   Screenshot size: {screenshot_bgr.shape[1]}x{screenshot_bgr.shape[0]}")

# Perform template matching
print("\n🔍 Running template matching...")
result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)

# Find best match
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

print(f"\n📊 Raw Matching Results:")
print(f"   Best confidence: {max_val:.4f} ({max_val*100:.2f}%)")
print(f"   Location: {max_loc}")
print(f"   Worst confidence: {min_val:.4f}")

# Visualize best match
h, w = template.shape[:2]
top_left = max_loc
bottom_right = (top_left[0] + w, top_left[1] + h)

vis = screenshot_bgr.copy()
cv2.rectangle(vis, top_left, bottom_right, (0, 255, 0), 3)
cv2.putText(vis, f"{max_val:.2%}", (top_left[0], top_left[1]-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

cv2.imwrite("freebie_best_match.png", vis)
print(f"\n💾 Saved visualization: freebie_best_match.png")

# Extract matched region for comparison
matched_region = screenshot_bgr[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

if matched_region.shape == template.shape:
    # Side-by-side comparison
    diff = cv2.absdiff(template, matched_region)
    comparison = np.hstack([template, matched_region, diff * 3])  # Amplify diff
    cv2.imwrite("freebie_comparison.png", comparison)
    print(f"💾 Saved comparison: freebie_comparison.png")
    print(f"   (Left: template | Middle: best match | Right: difference)")

    mean_diff = diff.mean()
    print(f"\n📏 Difference metrics:")
    print(f"   Mean pixel difference: {mean_diff:.2f}")

# Check thresholds
print(f"\n🎯 Threshold recommendations:")
thresholds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
for thresh in thresholds:
    if max_val >= thresh:
        print(f"   ✅ {thresh:.1f} - WILL MATCH")
    else:
        print(f"   ❌ {thresh:.1f} - won't match (best is {max_val:.2%})")

# Find all matches above various thresholds
print(f"\n🔍 Finding all matches at different thresholds:")
for thresh in [0.7, 0.6, 0.5, 0.4, 0.3]:
    locations = np.where(result >= thresh)
    count = len(locations[0])
    if count > 0:
        print(f"   Threshold {thresh:.1f}: {count} match(es)")
    else:
        print(f"   Threshold {thresh:.1f}: 0 matches")

print("\n" + "="*60)
print("DIAGNOSIS:")
print("="*60)

if max_val >= 0.8:
    print("✅ Excellent match! Use threshold 0.7-0.8")
elif max_val >= 0.6:
    print("✅ Good match! Use threshold 0.5-0.6")
elif max_val >= 0.4:
    print("⚠️  Weak match. Use threshold 0.3-0.4 (risky)")
    print("   Consider recapturing template")
elif max_val >= 0.2:
    print("❌ Poor match - template likely doesn't match screen")
    print("   Possible issues:")
    print("   - Freebies not visible on screen")
    print("   - Template from different resolution")
    print("   - UI has changed")
else:
    print("❌ No match at all!")
    print("   The template is definitely not on screen, OR")
    print("   There's a major mismatch (resolution/scaling/UI change)")

print("\nCheck the saved images to see what was matched!")
print("="*60)
