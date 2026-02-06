# Region Configuration Tool Guide

## Overview

The **Region Configuration Tool** (`configure_regions.py`) is an interactive visual tool that helps you precisely define detection zones and lookup areas for your automation code.

## Features

- **Visual Selection**: Click and drag to draw rectangular regions
- **Pixel-Perfect Precision**: Exact pixel coordinates displayed
- **Percentage Conversion**: Automatically converts to 0.0-1.0 range for code
- **Code Generation**: Generates ready-to-use Python code for `detection_config.py`
- **Multiple Regions**: Define and save multiple regions in one session
- **JSON Export**: Save regions to a file for later use
- **Real-time Feedback**: See all saved regions overlaid on the screenshot

## Quick Start

### 1. Run the Tool

```bash
python tools/configure_regions.py
```

### 2. Position Game Window

After running, you have 2 seconds to switch to your game window before the screenshot is captured.

### 3. Select Regions

Click and drag on the screenshot to draw a rectangle around the area you want to configure.

### 4. Save Region

Press **'n'** to name and save the selected region. You'll be prompted to enter a name (e.g., `MATERIAL_ZONE_LEFT`).

### 5. Generate Code

Press **'g'** to generate Python code for all saved regions.

## Controls

| Key | Action |
|-----|--------|
| **Click & Drag** | Draw a rectangular region |
| **N** | Name and save the current selection |
| **C** | Clear current selection without saving |
| **D** | Delete the last saved region |
| **S** | Save all regions to `region_config.json` |
| **G** | Generate Python code for `detection_config.py` |
| **R** | Retake screenshot (if game state changed) |
| **Q** | Quit the tool |

## Workflow Example

### Example: Defining a Material Detection Zone

1. **Run the tool**
   ```bash
   python tools/configure_regions.py
   ```

2. **Switch to game** (you have 2 seconds)

3. **Draw the region**
   - Click at the top-left corner of the material zone
   - Drag to the bottom-right corner
   - Release the mouse button

4. **Review coordinates** (displayed in terminal)
   ```
   ✓ Region selected: (150, 200) to (350, 280)
     Press 'n' to name and save, or 'c' to clear
   ```

5. **Name the region**
   - Press **'n'**
   - Enter name: `MATERIAL_ZONE`
   - Press Enter

6. **Repeat** for other regions (e.g., `DELIVER_ZONE`, `TRAIN_CAPACITY_ZONE`)

7. **Generate code**
   - Press **'g'**
   - Code is displayed and saved to `region_config_code.py`

8. **Copy to detection_config.py**
   ```python
   # MATERIAL_ZONE
   # Pixel coordinates: (150, 200) to (350, 280)
   # Size: 200x80 px
   MATERIAL_ZONE_LEFT = 0.0781
   MATERIAL_ZONE_TOP = 0.1852
   MATERIAL_ZONE_RIGHT = 0.1823
   MATERIAL_ZONE_BOTTOM = 0.2593
   ```

## Output Files

### region_config.json
Complete region data in JSON format:
```json
{
  "screen_width": 1920,
  "screen_height": 1080,
  "regions": [
    {
      "name": "MATERIAL_ZONE",
      "x1": 150,
      "y1": 200,
      "x2": 350,
      "y2": 280,
      "x1_pct": 0.0781,
      "y1_pct": 0.1852,
      ...
    }
  ]
}
```

### region_config_code.py
Ready-to-use Python code:
```python
# Auto-generated region configuration
# Screen size: 1920x1080

# MATERIAL_ZONE
MATERIAL_ZONE_LEFT = 0.0781
MATERIAL_ZONE_TOP = 0.1852
MATERIAL_ZONE_RIGHT = 0.1823
MATERIAL_ZONE_BOTTOM = 0.2593
```

## Tips for Precise Selection

### 1. Use Zoom If Needed
If the display is scaled down, coordinates are automatically scaled back to original resolution.

### 2. Naming Conventions
Follow the existing naming pattern from `detection_config.py`:
- `ZONE_NAME_LEFT` - Left boundary percentage
- `ZONE_NAME_TOP` - Top boundary percentage
- `ZONE_NAME_RIGHT` - Right boundary percentage
- `ZONE_NAME_BOTTOM` - Bottom boundary percentage

### 3. Common Regions to Define

**Task Card Regions:**
- Material numbers area
- Deliver amount area
- Train capacity area

**UI Element Regions:**
- Button search areas
- Icon detection zones
- Text OCR regions

**Game State Zones:**
- Operator timer area
- Freebie spawn areas
- Resource collection zones

### 4. Retake Screenshot
If you need to change the game state (e.g., open a menu), press **'r'** to retake the screenshot without losing your saved regions.

### 5. Multiple Sessions
You can run the tool multiple times. Just append the generated code to your `detection_config.py` file.

## Integration with Code

### Using Percentage Coordinates

The generated percentages work with your existing window manager:

```python
from src.config.detection_config import (
    MATERIAL_ZONE_LEFT,
    MATERIAL_ZONE_TOP,
    MATERIAL_ZONE_RIGHT,
    MATERIAL_ZONE_BOTTOM
)

# Convert to pixel coordinates
screen_width, screen_height = pyautogui.size()
x1 = int(screen_width * MATERIAL_ZONE_LEFT)
y1 = int(screen_height * MATERIAL_ZONE_TOP)
x2 = int(screen_width * MATERIAL_ZONE_RIGHT)
y2 = int(screen_height * MATERIAL_ZONE_BOTTOM)

# Use for detection
roi = screenshot[y1:y2, x1:x2]
```

### With WindowManager

```python
info = self.window_manager.get_window_info()
x1 = int(info['width'] * MATERIAL_ZONE_LEFT)
y1 = int(info['height'] * MATERIAL_ZONE_TOP)
# ...
```

## Troubleshooting

### Screenshot is blank
- Make sure the game window is visible when the screenshot is captured
- Try increasing the delay (edit the `time.sleep(2)` in the code)

### Coordinates are off
- Ensure the game is in the same screen mode (fullscreen/windowed) as when regions were defined
- HiDPI/Retina displays are automatically handled

### Can't see the selection
- The current selection is drawn in **green**
- Saved regions are drawn in **blue**
- Make sure you're dragging the mouse to create a rectangle

### Region name conflicts
- Check `detection_config.py` for existing variable names
- Use unique, descriptive names for each region

## Advanced Usage

### Loading Saved Regions

You can create a script to load regions from `region_config.json`:

```python
import json

with open('region_config.json', 'r') as f:
    data = json.load(f)

for region in data['regions']:
    print(f"{region['name']}: {region['x1']}, {region['y1']}")
```

### Batch Definition

For complex setups, define all regions in one session:
1. Open all relevant game menus
2. Take screenshots with 'r'
3. Define all regions
4. Generate complete code with 'g'

## See Also

- `src/config/detection_config.py` - Main detection configuration
- `tools/visualize.py` - Visualize detection zones
- `tools/test_template_matching.py` - Test template matching in regions
