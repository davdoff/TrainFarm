#!/usr/bin/env python3
"""
Crafting Tree Navigator

Handles navigating through crafting recipes by:
1. Finding resources you don't have (red text/amounts)
2. Clicking on them to see their recipe
3. Recursively gathering all base materials
4. Using X button to go back up the tree
"""

import pyautogui
import time
from template_matcher import find_template_on_screen, find_all_matches
from pathlib import Path


class CraftingTreeNavigator:
    def __init__(self, templates_dir="templates"):
        """
        Initialize the navigator with template images.

        Templates needed:
        - red_resource.png: Template for red (missing) resource text/number
        - x_button.png: Template for the X button to go back
        - craft_button.png: Template for the craft/make button
        """
        self.templates_dir = Path(templates_dir)
        self.recipe_stack = []  # Stack to track where we are in the tree
        self.required_resources = {}  # Final list of base resources needed

    def find_missing_resources(self, confidence=0.8):
        """
        Find all red (missing) resources on screen.
        Returns list of coordinates for clickable red resources.
        """
        red_template = self.templates_dir / "red_resource.png"
        matches = find_all_matches(str(red_template), threshold=confidence)

        print(f"Found {len(matches)} missing resources")
        return matches

    def click_resource(self, match):
        """Click on a resource to view its recipe."""
        pyautogui.click(match['x'], match['y'])
        time.sleep(0.5)  # Wait for UI to update
        print(f"Clicked resource at ({match['x']}, {match['y']})")

    def go_back(self):
        """Click the X button to go back one recipe level."""
        x_button = self.templates_dir / "x_button.png"
        match = find_template_on_screen(str(x_button))

        if match:
            pyautogui.click(match['x'], match['y'])
            time.sleep(0.5)
            print("Went back one level")
            return True
        else:
            print("Warning: X button not found!")
            return False

    def is_base_resource(self):
        """
        Check if current resource is a base resource (can't be crafted).
        This could check for:
        - Absence of red resources (everything is available)
        - Specific text like "Gather" instead of "Craft"
        - Or any other indicator
        """
        # Check if there are any missing resources
        missing = self.find_missing_resources()
        return len(missing) == 0

    def explore_recipe_tree(self, max_depth=10, current_depth=0):
        """
        Recursively explore the crafting tree to find all base resources.

        Args:
            max_depth: Maximum recursion depth to prevent infinite loops
            current_depth: Current recursion level

        Returns:
            Dictionary of base resources and quantities needed
        """
        if current_depth >= max_depth:
            print(f"Max depth {max_depth} reached, stopping recursion")
            return

        # Find all missing (red) resources on current screen
        missing_resources = self.find_missing_resources()

        if not missing_resources:
            print(f"[Depth {current_depth}] No missing resources - this is a base resource!")
            # TODO: Add logic here to read the resource name and quantity
            return

        print(f"[Depth {current_depth}] Found {len(missing_resources)} missing resources")

        # For each missing resource, click it and explore deeper
        for i, resource in enumerate(missing_resources):
            print(f"\n[Depth {current_depth}] Exploring resource {i+1}/{len(missing_resources)}")

            # Click on the red resource
            self.click_resource(resource)
            self.recipe_stack.append(resource)

            # Recursively explore this resource's recipe
            self.explore_recipe_tree(max_depth, current_depth + 1)

            # Go back to previous level
            if self.go_back():
                self.recipe_stack.pop()
            else:
                print("ERROR: Couldn't go back! Navigation might be broken")
                break

        print(f"[Depth {current_depth}] Finished exploring all {len(missing_resources)} resources")

    def get_crafting_path(self, target_item_template):
        """
        Get the full crafting path for a target item.

        Usage:
            navigator = CraftingTreeNavigator()
            # First, click on the item you want to craft
            navigator.explore_recipe_tree()
        """
        print("Starting crafting tree exploration...")
        print("=" * 50)

        self.explore_recipe_tree()

        print("\n" + "=" * 50)
        print("Exploration complete!")
        return self.required_resources


def simple_navigation_example():
    """
    Simple example: Navigate one level deep and back.
    """
    print("Simple Navigation Example")
    print("Make sure you have the crafting UI open!")
    input("Press ENTER to start...")

    navigator = CraftingTreeNavigator()

    # Find missing resources
    missing = navigator.find_missing_resources()

    if missing:
        print(f"\nFound {len(missing)} missing resources")
        print("Clicking the first one...")
        navigator.click_resource(missing[0])

        time.sleep(2)
        print("Going back...")
        navigator.go_back()
    else:
        print("No missing resources found!")


def full_tree_exploration():
    """
    Full recursive tree exploration.
    """
    print("Full Crafting Tree Explorer")
    print("=" * 50)
    print("Instructions:")
    print("1. Open the game and navigate to the item you want to craft")
    print("2. Make sure the recipe is visible")
    print("3. Press ENTER to start exploration")
    print("=" * 50)
    input("Press ENTER when ready...")

    navigator = CraftingTreeNavigator()
    navigator.explore_recipe_tree(max_depth=10)

    print("\nExploration complete!")


if __name__ == "__main__":
    # Run the simple example
    # simple_navigation_example()

    # Or run full exploration
    full_tree_exploration()
