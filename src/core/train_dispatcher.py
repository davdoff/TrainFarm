#!/usr/bin/env python3
"""
Train Dispatcher
Dispatches trains after a task is started.
"""

import time
import pyautogui
import cv2
import numpy as np
import pytesseract
from typing import Optional
from difflib import SequenceMatcher
from src.detectors.template_matcher import find_template_on_screen
from src.config.detection_config import (
    TRAIN_STATUS_TEXT_LEFT,
    TRAIN_STATUS_TEXT_TOP,
    TRAIN_STATUS_TEXT_RIGHT,
    TRAIN_STATUS_TEXT_BOTTOM,
    TRAIN_STATUS_MATCH_THRESHOLD
)


class TrainDispatcher:
    """Handles train dispatching after task start."""

    def __init__(self):
        self.dispatch_template = "Templates/buttons/DispatchButton.png"
        # Train positions are estimated based on screen layout
        # First train is typically at 1/6 of screen width from left
        self.screen_width, self.screen_height = pyautogui.size()

    def _fuzzy_text_match(self, text: str, target: str, threshold: float = 0.70) -> bool:
        """
        Check if text contains target string with fuzzy matching.
        Uses partial ratio to handle OCR errors.

        Args:
            text: The OCR text to search in
            target: The target string to find
            threshold: Minimum match ratio (0.0-1.0)

        Returns:
            True if match ratio >= threshold
        """
        if not text or not target:
            return False

        # Normalize both strings (uppercase, remove extra spaces)
        text = ' '.join(text.upper().split())
        target = ' '.join(target.upper().split())

        # Calculate similarity ratio
        ratio = SequenceMatcher(None, text, target).ratio()

        # Also check if target is substring (for partial matches)
        if target in text:
            return True

        # Check similarity with threshold
        return ratio >= threshold

    def _read_train_status_text(self) -> str:
        """
        Read the train status text using OCR from the configured region.

        Returns:
            The OCR text found, or empty string if nothing detected
        """
        # Capture screenshot
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Calculate pixel coordinates from percentages
        x1 = int(self.screen_width * TRAIN_STATUS_TEXT_LEFT)
        y1 = int(self.screen_height * TRAIN_STATUS_TEXT_TOP)
        x2 = int(self.screen_width * TRAIN_STATUS_TEXT_RIGHT)
        y2 = int(self.screen_height * TRAIN_STATUS_TEXT_BOTTOM)

        # Extract region
        roi = screenshot[y1:y2, x1:x2]

        # Preprocess for OCR
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Try multiple preprocessing techniques
        # 1. Simple threshold
        _, thresh1 = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # 2. Adaptive threshold
        thresh2 = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # 3. Otsu's threshold
        _, thresh3 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Try OCR on all versions and combine results
        texts = []
        for img in [gray, thresh1, thresh2, thresh3]:
            try:
                # Use Tesseract with config optimized for text
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(img, config=custom_config)
                if text.strip():
                    texts.append(text.strip())
            except Exception as e:
                print(f"  OCR error: {e}")
                continue

        # Return the longest text (usually most complete)
        if texts:
            result = max(texts, key=len)
            return result
        return ""

    def check_trains_available_by_text(self) -> bool:
        """
        Check if trains are available by reading status text with OCR.

        Returns:
            True if "TAP THE TRAIN TO" text is detected (trains available)
            False if "PLEASE WAIT" text is detected (all trains used) or text unclear
        """
        text = self._read_train_status_text()

        if not text:
            print("  ⚠️  No text detected in train status region")
            return False

        print(f"  OCR Text: '{text}'")

        # Check for "trains available" text
        if self._fuzzy_text_match(text, "TAP THE TRAIN TO", TRAIN_STATUS_MATCH_THRESHOLD):
            print("  ✓ Trains available (TAP THE TRAIN TO detected)")
            return True

        # Check for "all trains used" text
        if self._fuzzy_text_match(text, "PLEASE WAIT UNTIL", TRAIN_STATUS_MATCH_THRESHOLD):
            print("  ✓ All trains used (PLEASE WAIT detected)")
            return False

        # If neither matches clearly, be conservative
        print("  ⚠️  Train status unclear from OCR")
        return False

    def find_dispatch_button(self) -> Optional[tuple]:
        """
        Find the Dispatch button on screen.

        Returns:
            (x, y) coordinates of Dispatch button, or None if not found
        """
        match = find_template_on_screen(self.dispatch_template, threshold=0.7)
        if match:
            return (match['x'], match['y'])
        return None

    def check_all_trains_used(self) -> bool:
        """
        Check if all trains are used by reading the status text with OCR.

        Uses OCR to read the train status text region and checks for:
        - "TAP THE TRAIN TO" = Trains available (returns False)
        - "PLEASE WAIT UNTIL THE TRAINS REACH THEIR DESTINATION" = All trains used (returns True)

        IMPORTANT: Moves mouse away from progress bar to avoid clicking it (uses gems!)

        Returns:
            True if all trains are used (PLEASE WAIT text detected)
            False if trains are available (TAP THE TRAIN TO text detected)
        """
        # Read status text
        text = self._read_train_status_text()

        if not text:
            print("  ⚠️  No status text detected - trying template fallback")
            # Fall back to template matching as last resort
            all_trains_template = "Templates/tasks/AlltrainsUsed.png"
            match = find_template_on_screen(all_trains_template, threshold=0.6)
            if match:
                print("✓ All trains used (template match)")
                # Move mouse to safe position
                safe_x = int(self.screen_width / 2)
                safe_y = int(self.screen_height / 2)
                pyautogui.moveTo(safe_x, safe_y)
                return True
            return False

        print(f"  OCR Text: '{text}'")

        # Check for "all trains used" text
        if self._fuzzy_text_match(text, "PLEASE WAIT UNTIL", TRAIN_STATUS_MATCH_THRESHOLD):
            print("✓ All trains used (PLEASE WAIT detected)")

            # CRITICAL: Move mouse away from the progress bar immediately!
            # Clicking the progress bar uses gems, which we want to avoid
            safe_x = int(self.screen_width / 2)
            safe_y = int(self.screen_height / 2)
            pyautogui.moveTo(safe_x, safe_y)
            print(f"   Moved mouse to safe position ({safe_x}, {safe_y})")

            return True

        # Check for "trains available" text
        if self._fuzzy_text_match(text, "TAP THE TRAIN TO", TRAIN_STATUS_MATCH_THRESHOLD):
            print("  Trains still available (TAP THE TRAIN TO detected)")
            return False

        # If text is unclear, assume trains might still be available
        print("  ⚠️  Status unclear from OCR - assuming trains available")
        return False

    def click_first_train(self):
        """
        Click on the first train position.
        Trains appear at the bottom of the screen after starting a task.
        """
        # First train is typically at ~1/6 of screen width from left
        # Bottom area of screen
        train_x = int(self.screen_width / 6)
        train_y = int(self.screen_height * 0.85)  # Near bottom

        print(f"Clicking first train at estimated position ({train_x}, {train_y})")
        pyautogui.click(train_x, train_y)
        time.sleep(0.3)

    def dispatch_train(self) -> bool:
        """
        Click the Dispatch button.
        Retries up to 3 times if not found immediately.

        Returns:
            True if dispatch button found and clicked, False otherwise
        """
        # Try up to 3 times with short delays
        for attempt in range(3):
            dispatch_coords = self.find_dispatch_button()

            if dispatch_coords:
                print(f"Found Dispatch button at ({dispatch_coords[0]}, {dispatch_coords[1]})")
                pyautogui.click(dispatch_coords[0], dispatch_coords[1])
                time.sleep(0.5)
                return True
            else:
                if attempt < 2:
                    print(f"⚠️  Dispatch button not found, retrying ({attempt+1}/3)...")
                    time.sleep(0.5)

        print("❌ Dispatch button not found after 3 attempts")
        return False

    def check_task_complete(self) -> bool:
        """
        Check if the task shows a timer in the top-left corner (task complete).
        Uses template matching to detect if task is now completing.

        Returns:
            True if task is complete (timer visible), False otherwise
        """
        from src.detectors.template_matcher import find_template_on_screen

        # Try to find the TaskCompleting template
        completing_template = "Templates/tasks/TaskCompleting.png"
        match = find_template_on_screen(completing_template, threshold=0.7)

        if match:
            print("✓ Task is now completing (timer detected)")
            return True
        return False

    def dispatch_trains_for_task(self, num_operators: int = None) -> bool:
        """
        Dispatch trains until the "all trains used" progress bar appears.
        After each dispatch, the train disappears and the next one slides into place.

        Args:
            num_operators: Optional hint for max operators (ignored, kept for compatibility)

        Returns:
            True if all trains dispatched successfully
        """
        print(f"\n=== Dispatching Trains (until all trains used) ===")

        success_count = 0
        train_position = None  # Store the first train click position
        max_dispatches = 10  # Safety limit to prevent infinite loop

        for i in range(max_dispatches):
            print(f"\n📍 Attempting to dispatch train {i+1}:")

            # First train: click at estimated position
            # Subsequent trains: click at same position (train slides into place)
            if i == 0:
                # Click first train and remember the position
                train_x = int(self.screen_width / 6)
                train_y = int(self.screen_height * 0.85)
                train_position = (train_x, train_y)
                print(f"Clicking first train at ({train_x}, {train_y})")
            else:
                # Click same position where next train should have slid in
                print(f"Clicking next train at same position ({train_position[0]}, {train_position[1]})")

            pyautogui.click(train_position[0], train_position[1])
            time.sleep(0.5)  # Wait for train details to appear

            # Check if "all trains used" progress bar is showing
            if self.check_all_trains_used():
                print(f"\n✅ All trains have been dispatched!")
                print(f"   Total trains dispatched: {success_count}")
                break

            # Try to click dispatch button
            if self.dispatch_train():
                print(f"✅ Train {i+1} dispatched successfully")
                success_count += 1

                # Wait for next train to slide into position
                print("   Waiting 1s for next train to appear...")
                time.sleep(1.0)

                # Check again if all trains are now used
                if self.check_all_trains_used():
                    print(f"\n✅ All trains have been dispatched!")
                    print(f"   Total trains dispatched: {success_count}")
                    break

                # Also check if task is complete (timer visible)
                if self.check_task_complete():
                    print(f"\n✅ Task is complete!")
                    print(f"   Total trains dispatched: {success_count}")
                    break
            else:
                print(f"❌ Dispatch button not found")
                # Check if it's because all trains are used
                if self.check_all_trains_used():
                    print("   All trains already used!")
                    break
                # Or if task is complete
                if self.check_task_complete():
                    print("   Task already complete!")
                    break
                print("   Stopping dispatch attempts.")
                break

        print(f"\n{'='*60}")
        print(f"Dispatch Summary: {success_count} trains dispatched")
        print(f"{'='*60}")

        # After all trains dispatched, go back to main screen
        if success_count > 0:
            print("\n=== Returning to Main Screen ===")
            print("Pressing ESC to go back...")
            pyautogui.press('esc')
            time.sleep(0.5)
            pyautogui.press('esc')
            time.sleep(0.5)
            print("✅ Returned to task list/main screen")

        # Return True if at least one train was dispatched
        return success_count > 0


def test_train_dispatcher():
    """Test the train dispatcher."""
    print("="*60)
    print("Train Dispatcher Test")
    print("="*60)

    print("\nStart a task manually and wait for trains to appear")
    input("Press ENTER when trains are visible at the bottom...")

    import time
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    dispatcher = TrainDispatcher()

    # Test dispatching 1 train
    print("\nTesting dispatch for 1 operator:")
    success = dispatcher.dispatch_trains_for_task(num_operators=1)

    if success:
        print("\n✅ Test successful!")
    else:
        print("\n❌ Test failed")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    test_train_dispatcher()
