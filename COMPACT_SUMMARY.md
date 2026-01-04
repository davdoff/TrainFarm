# TrainFarm Automation - Compact Summary

## System Overview
Game automation for train/factory management game. Detects task cards, checks material availability by color, and dispatches trains.

## Core Architecture

### Detection System
- **Card Detection**: Fixed borders at 374x610px starting at (115, 195) with 397px spacing
- **Material Detection**: Text-based detection in zone 38-46% of card height
- **Color Logic**:
  - Black numbers → materials available → click task
  - Red numbers → materials needed → click material icon → click blue button

### Key Files
1. `detection_config.py` - All calibration settings (centralized)
2. `task_automation.py` - Main workflow with material detection
3. `task_card_detector.py` - Card border detection
4. `test_complete_detection.py` - Testing/visualization tool
5. `calibrate_borders.py` - Border calibration tool

## Material Detection Flow

```python
# In task_automation.py
def _find_material_numbers(card_x, card_y, card_w, card_h):
    # 1. Capture material zone (38-46% of card height)
    # 2. Detect black text (grayscale 0-80)
    # 3. Detect red text (HSV red ranges)
    # 4. Filter by size (10-60px wide, 10-30px tall)
    # 5. Return [{x, y, is_red}]
```

### Click Logic
```python
# Black numbers (materials available):
click_y = black_number['y'] + abs(CLICK_OFFSET_Y)  # Click BELOW (+50px)

# Red numbers (materials needed):
click_y = red_number['y'] + CLICK_OFFSET_Y  # Click ABOVE (-50px)
# Then: Find blue button (HSV detection) and click
```

## Configuration (detection_config.py)
```python
# Card Borders
CARD_WIDTH = 374
CARD_HEIGHT = 610
CARD_START_X = 115
CARD_START_Y = 195
CARD_SPACING = 397

# Material Detection Zone
MATERIAL_ZONE_START = 0.38
MATERIAL_ZONE_END = 0.46

# Number Detection
BLACK_TEXT_MAX = 80
NUMBER_MIN_WIDTH = 10
NUMBER_MAX_WIDTH = 60
NUMBER_MIN_HEIGHT = 10
NUMBER_MAX_HEIGHT = 30
CLICK_OFFSET_Y = -50
```

## Blue Button Detection
```python
def _find_and_click_blue_button():
    # 1. Detect blue color (HSV 90-130 hue)
    # 2. Filter by size (>10,000px area)
    # 3. Filter by aspect ratio (>1.5 wider than tall)
    # 4. Click center of largest match
```

## Installation
```bash
# 1. Install Tesseract OCR
brew install tesseract  # macOS
sudo apt-get install tesseract-ocr  # Linux

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Calibrate for your device
python calibrate_borders.py
python test_complete_detection.py
```

## Calibration Process
1. **Borders**: Adjust CARD_* values in detection_config.py until borders align
2. **Detection Zone**: Adjust MATERIAL_ZONE_* until cyan box covers material numbers
3. **Click Offset**: Adjust CLICK_OFFSET_Y if clicks miss icons

## Major Changes Made
1. Replaced template matching with color-based text detection
2. Centralized all settings to detection_config.py
3. Implemented black/red number detection and differential click logic
4. Added blue button detection for material popup
5. Fixed click positions (below for black, above for red)
6. Removed non-existent imports (material_queue, material_capture)
7. Installed Tesseract OCR for number reading

## Current Status
✅ Fully functional automation system
✅ OCR installed and working
✅ All import errors resolved
✅ Material detection working (black/red differentiation)
✅ Blue button clicking working

## TODO
- Implement material generation logic at source (mine/factory) after clicking blue button
- Currently: presses ESC as placeholder

## Running
```bash
python task_automation.py
```
