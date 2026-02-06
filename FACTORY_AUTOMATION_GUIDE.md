# Factory Automation Guide

## Overview

The **Factory Automation** module handles crafting materials in the game's factory system. It detects missing materials (shown in red text) and can navigate to craft prerequisite materials recursively.

## Files Created

- `src/core/factory_automation.py` - Main factory automation module
- `tools/test_factory_crafting.py` - Test script for factory workflow
- `Templates/Materials/CopperWire.png` - Material template (already existed)
- `Templates/buttons/ConfirmButton.png` - Confirm button template (already existed)
- `Templates/buttons/FactoryIconBlueButton.png` - Factory blue button template (already existed)
- `Templates/ui/TemplateUnderMaterialsNeeded.png` - Marker under materials section (already existed)
- `Templates/ui/RedNumber.png` - Example red number for color sampling (already existed)

## How It Works

### Color Sampling

On initialization, the module:
1. Loads `Templates/ui/RedNumber.png`
2. Converts to HSV and filters out white/background pixels
3. Calculates median HSV values of red pixels
4. Creates detection range with ±15 hue tolerance
5. Handles red hue wrap-around (0-180 boundary) automatically

**Output:**
```
=== Sampling Red Color from Template ===
✓ Sampled red color from template:
  Median HSV: H=3, S=215, V=195
  Total red pixels sampled: 1247
  Range: H=[0, 18], S=[165, 255], V=[145, 255]
```

This ensures red text detection matches the exact color used in your game.

### Workflow

1. **Find Material Icon** - Locates the material (e.g., CopperWire) on screen using template matching
2. **Click Material** - Clicks on the material icon
3. **Click Blue Button** - Uses `find_template_on_screen()` to find FactoryIconBlueButton across entire screen
4. **Wait for Factory UI** - Waits for Confirm button, saves position as `confirm_button_x/y`
5. **Find Requirements Region** - Locates TemplateUnderMaterialsNeeded marker, materials are on horizontal line ABOVE it
6. **Read Text** - Uses OCR with multiple preprocessing methods to read all text in the requirements region
7. **Output Results** - Displays all detected text from different OCR methods

### Text Detection

The module reads all text in the materials requirements region using:
- **Multiple OCR preprocessing methods** - Tries 4 different preprocessing approaches
- **Grayscale** - Original image
- **Binary threshold** - Simple threshold at 127
- **Adaptive threshold** - Gaussian adaptive threshold
- **Inverted** - White text on black background
- **Deduplication** - Only unique results are returned

The OCR output shows all detected text, allowing you to see what materials are needed.

## Usage

### Basic Test

```bash
python tools/test_factory_crafting.py
```

This will test with CopperWire by default.

### Test with Different Material

```bash
python tools/test_factory_crafting.py [MaterialName]
```

Example:
```bash
python tools/test_factory_crafting.py Steel
```

**Note:** The material template must exist in `Templates/Materials/[MaterialName].png`

### Using in Code

```python
from src.core.factory_automation import FactoryAutomation

# Initialize
factory = FactoryAutomation(click_delay=0.5)

# Craft a material
success = factory.craft_material("CopperWire")

if success:
    print("Material crafted or prerequisites detected!")
```

## Configuration

### Adjustable Parameters

#### In `factory_automation.py`:

**Requirements Region Estimation:**
```python
region_width = int(self.screen_width * 0.25)   # 25% of screen width
region_height = int(self.screen_height * 0.08) # 8% of screen height
region_y = confirm_y - int(self.screen_height * 0.15)  # 15% above confirm button
```

**Bottom Portion for Red Text:**
```python
bottom_height = int(height * 0.4)  # Bottom 40% of region
```

**Click Offset:**
```python
offset_y = 30  # Pixels above red text to click (targets material icon)
```

### Making Region Configurable

To make the requirements region configurable (recommended):

1. Use `tools/configure_regions.py` to define the region
2. Add to `src/config/detection_config.py`:

```python
# Factory Material Requirements Region
FACTORY_REQUIREMENTS_LEFT = 0.375    # Configure with tools
FACTORY_REQUIREMENTS_TOP = 0.45
FACTORY_REQUIREMENTS_RIGHT = 0.625
FACTORY_REQUIREMENTS_BOTTOM = 0.53
```

3. Update `find_material_requirements_region()` to use these values

## Debug Output

The test creates several debug images:

### factory_requirements_region.png
Full requirements region captured from screen (original).

### factory_requirements_thresh.png
Binary threshold preprocessing (threshold at 127).

### factory_requirements_adaptive.png
Adaptive threshold preprocessing (Gaussian, block size 11).

### factory_requirements_inverted.png
Inverted image preprocessing (white text on black).

**Review these images to see which preprocessing method works best for your game's text.**

## Current Implementation Status

### ✅ Implemented

- Material icon detection and clicking
- Blue button navigation
- Factory UI detection (Confirm button)
- Requirements region estimation
- Red text detection (HSV color + OCR)
- Click above red text (test)

### 🚧 Next Steps (Not Yet Implemented)

1. **Recursive Crafting** - After clicking red text material, recursively craft prerequisites
2. **Confirm Click** - Click Confirm button when all materials available
3. **Return Navigation** - Press ESC to go back after crafting
4. **Error Handling** - Handle cases where factory is full, not enough base materials, etc.
5. **Configurable Regions** - Use detection_config.py for regions instead of hardcoded estimates

## Testing Checklist

Before running the test:

- [ ] Game is open in fullscreen (F11)
- [ ] You're at the main game view
- [ ] CopperWire (or target material) icon is visible on screen
- [ ] CopperWire template exists: `Templates/Materials/CopperWire.png`
- [ ] ConfirmButton template exists: `Templates/buttons/ConfirmButton.png`

## Expected Output

```
============================================================
Factory Crafting: CopperWire
============================================================

=== Step 1: Find Material Icon ===
Looking for CopperWire icon...
✓ Found CopperWire at (1234, 567)

=== Step 2: Navigate to Factory ===
=== Looking for Blue Button ===
✓ Found 1 blue button(s)
  Clicking highest: at (1440, 720)

=== Step 3: Wait for Factory UI ===
✓ Confirm button found at (1440, 900)

=== Step 4: Find Requirements Region ===
Confirm button at (1440, 900)
✓ Estimated requirements region:
  Position: (1260, 765)
  Size: 360x72

=== Step 5: Detect Missing Materials (Red Text) ===
✓ Found 2 red regions
  Red text 1: '5' at (1300, 800), area=250
  Red text 2: '3' at (1400, 800), area=180

⚠️  Found 2 missing material(s) (red text)

=== Step 6: TEST - Click Above First Red Text ===
Red text: '5' at (1300, 800)
Clicking at: (1300, 770) (offset: -30px)

Test Complete!
Check if clicking above red text navigated to that material.
```

## Troubleshooting

### Issue: Material icon not found

**Solutions:**
- Ensure material template exists in `Templates/Materials/`
- Capture new template if game graphics changed
- Lower threshold in `find_material_icon()` (default: 0.7)

### Issue: Blue button not found

**Solutions:**
- Check if popup actually appeared after clicking material
- Verify blue button color range in code matches game UI
- Increase search region if button is outside 40-70% horizontal range

### Issue: Confirm button not found

**Solutions:**
- Increase timeout in `wait_for_confirm_button()` (default: 5.0 seconds)
- Verify ConfirmButton template is correct
- Check if factory UI loaded correctly

### Issue: No red text detected

**Solutions:**
- Review `factory_requirements_red_mask.png` to see what red was detected
- Adjust HSV red color ranges if game uses different red shade
- Check if requirements region is positioned correctly
- Ensure you're looking at the bottom portion where text appears

### Issue: Click above red text didn't work

**Solutions:**
- Adjust `offset_y` parameter (default: 30 pixels)
- Check debug images to see where red text was detected
- Material icon might be further above the text

## Integration with Main Automation

To integrate factory crafting into the main task automation:

```python
# In task_automation.py, when red numbers detected:

if location_type == 'factory':
    from src.core.factory_automation import FactoryAutomation
    factory_auto = FactoryAutomation()

    # Craft the material
    success = factory_auto.craft_material(material_name)

    if success:
        print("✅ Factory crafting complete!")
```

## Next Steps

1. **Test the current implementation**
   ```bash
   python tools/test_factory_crafting.py
   ```

2. **Review debug images** to verify detection accuracy

3. **If test works**, implement recursive crafting:
   - Detect material type from icon above red text
   - Call `craft_material()` recursively
   - Add depth limit to prevent infinite recursion

4. **Add Confirm click** when no red text (all materials available)

5. **Configure regions** using `tools/configure_regions.py` for accuracy

## Summary

✅ **Factory module created** with full workflow
✅ **Red text detection** using HSV + OCR
✅ **Click above red text** for material navigation
✅ **Debug images** for troubleshooting
✅ **Test script** ready to use
🚧 **Recursive crafting** not yet implemented
🚧 **Confirm click** not yet implemented

Ready to test!
