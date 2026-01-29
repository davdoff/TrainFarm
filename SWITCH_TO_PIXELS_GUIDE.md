# Switch Task Card Detector to Absolute Pixels

## Current Situation

- Your screen: **1440x900**
- Old pixel values were for: **1920x1080**
- Current percentages scale down too much!

## Option A: Recalibrate Percentages (Recommended ⭐)

**Keep percentage system, adjust for YOUR screen:**

1. **Run visualization:**
   ```bash
   python tools/visualize_all_areas.py
   ```

2. **Check if blue task card borders align with actual game UI**

3. **If misaligned, measure actual positions** in your game

4. **Update `src/config/detection_config.py`:**
   ```python
   # Example adjustments for 1440x900
   CARD_WIDTH = 0.26      # Adjust until it matches
   CARD_HEIGHT = 0.68     # Adjust until it matches
   CARD_START_X = 0.08    # Adjust until it matches
   CARD_START_Y = 0.22    # Adjust until it matches
   CARD_SPACING = 0.275   # Adjust until it matches
   ```

5. **Re-run visualization until borders align perfectly**

**Benefits:**
- ✅ Works on any screen size
- ✅ Only config changes, no code changes
- ✅ Easy to tweak

---

## Option B: Use Absolute Pixels (Your Old Values)

**WARNING:** This locks you to your current screen resolution!

### Step 1: Add Pixel Mode to detection_config.py

```python
# At top of detection_config.py, add:
USE_PERCENTAGE_MODE = False  # Set to False for pixel mode

# Old pixel values (for 1440x900 or measure your own)
CARD_WIDTH_PX = 280      # Measure actual width in your game
CARD_HEIGHT_PX = 508     # Measure actual height
CARD_START_X_PX = 86     # Measure actual X position
CARD_START_Y_PX = 162    # Measure actual Y position
CARD_SPACING_PX = 298    # Measure actual spacing

# Keep percentages for other screens
CARD_WIDTH_PCT = 0.195
CARD_HEIGHT_PCT = 0.565
# ... etc

# Use the appropriate mode
if USE_PERCENTAGE_MODE:
    CARD_WIDTH = CARD_WIDTH_PCT
    CARD_HEIGHT = CARD_HEIGHT_PCT
    CARD_START_X = CARD_START_X_PCT
    CARD_START_Y = CARD_START_Y_PCT
    CARD_SPACING = CARD_SPACING_PCT
else:
    # In pixel mode, export pixel values directly
    CARD_WIDTH = CARD_WIDTH_PX
    CARD_HEIGHT = CARD_HEIGHT_PX
    CARD_START_X = CARD_START_X_PX
    CARD_START_Y = CARD_START_Y_PX
    CARD_SPACING = CARD_SPACING_PX
```

### Step 2: Modify task_card_detector.py

Change lines 68-72 from:
```python
# OLD (multiplies by window size - expects percentages)
card_width = int(CARD_WIDTH * self.window_width)
card_height = int(CARD_HEIGHT * self.window_height)
start_x = int(CARD_START_X * self.window_width)
start_y = int(CARD_START_Y * self.window_height)
spacing = int(CARD_SPACING * self.window_width)
```

To:
```python
# NEW (checks mode)
from src.config.detection_config import USE_PERCENTAGE_MODE

if USE_PERCENTAGE_MODE:
    card_width = int(CARD_WIDTH * self.window_width)
    card_height = int(CARD_HEIGHT * self.window_height)
    start_x = int(CARD_START_X * self.window_width)
    start_y = int(CARD_START_Y * self.window_height)
    spacing = int(CARD_SPACING * self.window_width)
else:
    # Pixel mode - use values directly
    card_width = CARD_WIDTH
    card_height = CARD_HEIGHT
    start_x = CARD_START_X
    start_y = CARD_START_Y
    spacing = CARD_SPACING
```

### Step 3: Measure Your Actual Values

Since your screen is different (1440x900), you need to measure where task cards actually are in YOUR game:

1. Run visualization to see current guess
2. Take a screenshot of your game with tasks visible
3. Use an image editor to measure pixel positions
4. Update the `_PX` values in detection_config.py

**Downsides:**
- ❌ Breaks if you change screen resolution
- ❌ Breaks if you resize game window
- ❌ More code changes needed
- ❌ Harder to maintain

---

## My Recommendation

**Use Option A** (recalibrate percentages):

1. It's simpler (just config changes)
2. More flexible for future
3. You just need to tweak the percentage values until they match your screen

Want me to help you recalibrate the percentages? I can guide you through measuring and calculating the right values.
