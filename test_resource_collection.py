#!/usr/bin/env python3
"""
Quick Test - Resource Collection Only
Tests just the operator resource collection feature.
"""

import time
from resource_collector import ResourceCollector


def main():
    print("="*60)
    print("Quick Test - Resource Collection")
    print("="*60)
    print()
    print("This will test ONLY the resource collection feature.")
    print()
    print("Instructions:")
    print("1. Make sure your game is open")
    print("2. Make sure the operator button is visible")
    print("3. (Optional) Make it yellow by waiting for trains to collect")
    print("4. Press ENTER when ready")
    print("5. You'll have 5 seconds to switch to the game")
    print()
    print("REMEMBER: Move mouse to top-left corner to emergency stop!")
    print("="*60)

    input("Press ENTER to start the 5-second countdown...")

    # 5 second countdown
    for i in range(5, 0, -1):
        print(f"\nStarting in {i} seconds... (switch to game now!)")
        time.sleep(1)

    print("\n" + "="*60)
    print("TESTING RESOURCE COLLECTION NOW!")
    print("="*60 + "\n")

    # Create resource collector
    collector = ResourceCollector()

    # Run the collection check
    result = collector.check_and_collect_resources()

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)

    if result:
        print("\n✅ SUCCESS: Resources were collected!")
    else:
        print("\n⚠️  No resources collected")
        print("   This is normal if:")
        print("   - Operator button was blue (no resources ready)")
        print("   - No Collect buttons were found")

    print("\nCheck the console output above to see what happened.")
    print()


if __name__ == "__main__":
    main()
