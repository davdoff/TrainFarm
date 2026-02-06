#!/usr/bin/env python3
"""
Detection Configuration
Centralized configuration for task card borders and material detection zones.
All coordinates are now WINDOW-RELATIVE PERCENTAGES (0.0 to 1.0).
Adjust these values when calibrating for different devices.
"""

# ============================================================================
# TASK CARD BORDER SETTINGS (WINDOW-RELATIVE PERCENTAGES)
# ============================================================================
# These define where task cards are located within the game window.
# Values are percentages of window width/height (0.0 = left/top, 1.0 = right/bottom)
# Calibrate using: python calibrate_borders.py
#
# OLD VALUES (for reference if clicks fail):
#   CARD_WIDTH = 374 px
#   CARD_HEIGHT = 610 px
#   CARD_START_X = 115 px
#   CARD_START_Y = 195 px
#   CARD_SPACING = 397 px
#   Assumed screen width: ~1920 px, height: ~1080 px

# Detection mode for task cards
USE_DYNAMIC_CARD_DETECTION = True  # True = detect rectangles dynamically, False = use fixed positions

# Card dimensions (used in both modes)
CARD_WIDTH = 0.260        # Width of each task card (26.0% of window width, 374px @ 1440px)
CARD_HEIGHT = 0.678       # Height of each task card (67.8% of window height, 610px @ 900px)

# Fixed position mode settings (only used if USE_DYNAMIC_CARD_DETECTION = False)
CARD_START_X = 0.080      # X position of first card's left edge (8.0% from window left, 115px @ 1440px)
CARD_START_Y = 0.217      # Y position of cards' top edge (21.7% from window top, 195px @ 900px)
CARD_SPACING = 0.276      # Horizontal distance between card centers (27.6% of window width, 397px @ 1440px)                                                                                                                                                                                         
# ============================================================================
# MATERIAL DETECTION ZONE SETTINGS
# ============================================================================
# These define where to look for material numbers within a task card.
# Values are percentages of card height from the top (0.0 = top, 1.0 = bottom)
# Calibrate using: python test_complete_detection.py

MATERIAL_ZONE_START = 0.38  # Start detection at 38% from top (below title/progress)
MATERIAL_ZONE_END = 0.46   # End detection at 46% from top (above DELIVER section)

# ============================================================================
# DELIVER AMOUNT DETECTION ZONE SETTINGS
# ============================================================================
# These define where to look for DELIVER numbers (amount needed for task).
# Vertical values are percentages of card height from the top (0.0 = top, 1.0 = bottom)
# Horizontal values are percentages of card width from the left (0.0 = left, 1.0 = right)
# Calibrate using: python test_deliver_detection.py

DELIVER_ZONE_START = 0.44   # Start detection at 44% from top (below material icons)
DELIVER_ZONE_END = 0.53     # End detection at 53% from top (DELIVER number area, avoid progress line)
DELIVER_ZONE_LEFT = 0.5     # Start detection at 50% from left (right side of card)
DELIVER_ZONE_RIGHT = 1.0    # End detection at 100% from left (right edge of card)

# ============================================================================
# TRAIN CAPACITY DETECTION ZONE SETTINGS
# ============================================================================
# These define where to look for train capacity numbers (how much each train can carry).
# We detect up to 4 train slots. First slot position is defined, others are offset by gap.
# Values are percentages of screen size (0.0 = top/left edge, 1.0 = bottom/right edge)
# Calibrate using: python test_train_capacity.py

# First train slot position (leftmost)
TRAIN_CAPACITY_ZONE_TOP = 0.81      # Top edge of capacity number zone
TRAIN_CAPACITY_ZONE_BOTTOM = 0.85    # Bottom edge of capacity number zone
TRAIN_CAPACITY_ZONE_LEFT = 0.08      # Left edge of first train slot
TRAIN_CAPACITY_ZONE_RIGHT = 0.12     # Right edge of first train slot

# Horizontal gap between train slots (percentage of screen width)
TRAIN_CAPACITY_GAP = 0.275            # Gap between each train slot (23% of screen width)

# ============================================================================
# TRAIN DISPATCHING SETTINGS
# ============================================================================
# Average train capacity for material generation
# Instead of reading each train's capacity with OCR, use this average value
# Adjust based on typical train capacities in your game (usually 20-50)
AVERAGE_TRAIN_CAPACITY = 30     # Average capacity per train

# ============================================================================
# TRAIN STATUS TEXT DETECTION ZONE
# ============================================================================
# Region where train status text appears (e.g., "TAP THE TRAIN TO..." or "PLEASE WAIT...")
# This text appears when starting to send trains (tasks or resource generation)
# Values are percentages of screen size (0.0 = top/left edge, 1.0 = bottom/right edge)
# Configured using: python tools/configure_regions.py
#
# Expected text states:
#   - "TAP THE TRAIN TO" = Trains available for dispatch
#   - "PLEASE WAIT UNTIL THE TRAINS REACH THEIR DESTINATION" = All trains used
#
# Region: TEXT_TRAIN_DISPATCHING_CONTEXT
# Pixel coordinates: (1375, 1321) to (2725, 1391)
# Size: 1350x70 px
TRAIN_STATUS_TEXT_LEFT = 0.4774      # Left edge of status text region
TRAIN_STATUS_TEXT_TOP = 0.7339       # Top edge of status text region
TRAIN_STATUS_TEXT_RIGHT = 0.9462     # Right edge of status text region
TRAIN_STATUS_TEXT_BOTTOM = 0.7728    # Bottom edge of status text region

# Fuzzy matching threshold for OCR text (0.0-1.0)
# At least 70% of the important text should match to handle OCR errors
TRAIN_STATUS_MATCH_THRESHOLD = 0.70

# ============================================================================
# OPERATOR COUNT DETECTION ZONE SETTINGS
# ============================================================================
# These define where to look for the operator count text (x/y format)
# after clicking the operator button.
# The text appears to the right of the operator icon showing "x/y" where:
# x = operators in use, y = total operators available
# Calibrate using: python test_operator_count.py

# Horizontal offset from operator icon (percentage of screen width)
OPERATOR_COUNT_OFFSET_X = 0.05   # Start text detection 5% of screen width to the right of icon

# Detection zone width (percentage of screen width)
OPERATOR_COUNT_ZONE_WIDTH = 0.08  # Width of text detection area (8% of screen)

# Vertical offset from operator icon center (percentage of screen height)
OPERATOR_COUNT_OFFSET_Y = 0.0     # Text is at same vertical level as icon center

# Detection zone height (percentage of screen height)
OPERATOR_COUNT_ZONE_HEIGHT = 0.04  # Height of text detection area (4% of screen)

# ============================================================================
# MATERIAL NUMBER DETECTION SETTINGS
# ============================================================================
# Fine-tune how numbers are detected and clicked

# Text color detection ranges
BLACK_TEXT_MAX = 80         # Maximum grayscale value for black text (0-255)

# Number size filters (pixels - these are relative to captured regions, not window)
NUMBER_MIN_WIDTH = 10       # Minimum width of detected numbers
NUMBER_MAX_WIDTH = 60       # Maximum width of detected numbers
NUMBER_MIN_HEIGHT = 10      # Minimum height of detected numbers
NUMBER_MAX_HEIGHT = 30      # Maximum height of detected numbers

# Click offset (WINDOW-RELATIVE PERCENTAGE)
# OLD VALUE: CLICK_OFFSET_Y = -50 px (negative = up, ~50px above @ 1080px height)
CLICK_OFFSET_Y = -0.046     # Percentage offset above number (4.6% of window height, ~50px @ 1080px)

# ============================================================================
# NOTES FOR CALIBRATION
# ============================================================================
# 1. Run: python calibrate_borders.py
#    - Adjust CARD_* values until borders align with cards
#
# 2. Run: python test_complete_detection.py
#    - Adjust MATERIAL_ZONE_* values until cyan box covers material numbers
#    - Check that yellow dots appear on material numbers
#    - Check that magenta circles are on material icons
#
# 3. If numbers not detected:
#    - Increase BLACK_TEXT_MAX to catch lighter text
#    - Adjust NUMBER_* size filters
#
# 4. If clicks are off:
#    - Adjust CLICK_OFFSET_Y (make more negative to click higher)
