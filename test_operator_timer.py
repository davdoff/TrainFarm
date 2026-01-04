#!/usr/bin/env python3
"""
Test the operator timer reading functionality.
"""

import time
from operator_checker import OperatorChecker

def test_timer_reading():
    """Test reading the operator timer."""
    print("="*60)
    print("Operator Timer Reading Test")
    print("="*60)

    checker = OperatorChecker()

    print("\nMake sure the game is visible and operators are occupied")
    input("Press ENTER when ready...")

    print("\nCountdown:")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # Test reading the timer
    print("\n=== Reading Operator Timer ===")
    wait_time = checker.read_next_operator_timer()

    if wait_time:
        minutes = wait_time // 60
        seconds = wait_time % 60
        print(f"\n✅ Successfully read timer!")
        print(f"   Time until next operator: {minutes}m {seconds}s")
        print(f"   Total seconds: {wait_time}s")
    else:
        print("\n❌ Could not read timer")
        print("   Check visualizeTries/operator_timer.png to debug")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_timer_reading()
