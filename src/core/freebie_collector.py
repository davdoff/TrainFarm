#!/usr/bin/env python3
"""Freebie Collector - Detects and clicks freebie whistles during delays."""

import time
import pyautogui
from pathlib import Path
from src.detectors.template_matcher import find_template_on_screen


class FreebieCollector:
    """Handles freebie whistle detection and collection."""

    def __init__(self, click_delay: float = 0.3):
        self.click_delay = click_delay
        self.template_path = "Templates/ui/Freebie.png"
        self.threshold = 0.5
        pyautogui.FAILSAFE = True

    def collect_freebies(self, max_freebies: int = 4):
        """
        Find and click freebies iteratively (they move after each collection).

        Takes a fresh screenshot for each attempt since freebies move/disappear.
        Clicks up to max_freebies (default 4) before stopping.

        Returns:
            Number of freebies collected
        """
        print("\n=== 🎵 Checking for Freebies ===")

        if not Path(self.template_path).exists():
            print(f"❌ Template not found: {self.template_path}")
            return 0

        collected = 0

        # Try to find and click freebies up to max_freebies times
        for attempt in range(max_freebies):
            # Take a FRESH screenshot each time (freebies move!)
            match = find_template_on_screen(
                self.template_path,
                threshold=self.threshold,
                screenshot_bgr=None  # Force new screenshot
            )

            if not match:
                # No freebie found, stop looking
                if attempt == 0:
                    print("No freebies found")
                else:
                    print(f"No more freebies found after {collected}")
                break

            # Found a freebie! Click it quickly
            x, y = match['x'], match['y']
            print(f"🎵 Freebie {attempt + 1}: Found at ({x}, {y}), clicking...")

            try:
                pyautogui.click(x, y)
                collected += 1
                time.sleep(self.click_delay)  # Brief pause after click
                pyautogui.press('esc')  # Dismiss any popups
                time.sleep(0.1)
            except Exception as e:
                print(f"⚠️  Error clicking freebie: {e}")
                # Continue to next attempt even if this one failed

        if collected > 0:
            print(f"✅ Collected {collected} freebie(s)!")

        return collected

    def collect_during_delay(self, delay_seconds: float, max_freebies: int = 4):
        """Collect freebies during delay, wait for remaining time."""
        start_time = time.time()
        collected = self.collect_freebies(max_freebies)
        elapsed = time.time() - start_time
        remaining = max(0, delay_seconds - elapsed)

        if remaining > 0:
            print(f"⏳ Waiting {remaining:.1f}s more before next check...")
            time.sleep(remaining)

        return collected
