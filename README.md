# TrainFarm

Game automation system for managing tasks, materials, and train dispatching.

## Setup

1. Install Tesseract OCR (for reading material numbers):
```bash
# macOS
brew install tesseract

# Linux (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. **IMPORTANT: Calibrate borders for your device**
```bash
python calibrate_borders.py
```

This step is critical because different devices/screens have different resolutions and scaling.

## Border Calibration (CRITICAL - Required for New Devices)

**⚠️ IMPORTANT:** The automation uses hardcoded pixel coordinates that are specific to the original device. On a different screen resolution, window size, or scaling setting, the borders WILL be wrong and the automation WILL NOT work.

You **must** manually calibrate borders for your specific setup.

### Why This Matters
Different devices have:
- Different screen resolutions (1920x1080 vs 2560x1440, etc.)
- Different game window sizes
- Different UI scaling settings
- Different pixel densities (Retina vs non-Retina displays)

The pixel coordinates (110, 135, 360, etc.) work on the original setup but need adjustment for yours.

### Step 1: Run Calibration Visualization
```bash
python calibrate_borders.py
```

This shows where the script THINKS task cards are. They will likely be wrong on first run.

### Step 2: Manual Fine-Tuning Process

**All calibration settings are now in `detection_config.py` for easy adjustment!**

Open `detection_config.py` and find the TASK CARD BORDER SETTINGS section:

```python
CARD_WIDTH = 374        # Width of each task card (pixels)
CARD_HEIGHT = 610       # Height of each task card (pixels)
CARD_START_X = 115      # X position of first card's left edge (pixels)
CARD_START_Y = 195      # Y position of cards' top edge (pixels)
CARD_SPACING = 397      # Horizontal distance between card centers (pixels)
```

**How to Adjust (Iterative Process):**

1. **Start with `CARD_START_X` and `CARD_START_Y`** (positioning)
   - Open the game task menu
   - Look at the saved screenshot `visualizeTries/border_calibration.png`
   - If borders are too far **left**: increase `CARD_START_X` (try +10 at a time)
   - If borders are too far **right**: decrease `CARD_START_X` (try -10 at a time)
   - If borders are too **high**: increase `CARD_START_Y` (try +10 at a time)
   - If borders are too **low**: decrease `CARD_START_Y` (try -10 at a time)
   - Re-run `calibrate_borders.py` after each change

2. **Then adjust `CARD_WIDTH` and `CARD_HEIGHT`** (sizing)
   - If border is **narrower** than card: increase `CARD_WIDTH` (+5 at a time)
   - If border is **wider** than card: decrease `CARD_WIDTH` (-5 at a time)
   - If border is **shorter** than card: increase `CARD_HEIGHT` (+10 at a time)
   - If border is **taller** than card: decrease `CARD_HEIGHT` (-10 at a time)
   - **Goal**: Border should tightly fit the card from top title bar to bottom "Available trains" text
   - Re-run `calibrate_borders.py` after each change

3. **Finally adjust `CARD_SPACING`** (gap between cards)
   - Check if Card 2, Card 3, etc. borders align with their cards
   - If cards 2+ are **shifted right**: increase `CARD_SPACING` (+5 at a time)
   - If cards 2+ are **shifted left**: decrease `CARD_SPACING` (-5 at a time)
   - **Note**: `CARD_SPACING` is center-to-center distance, typically `CARD_WIDTH + gap`
   - Re-run `calibrate_borders.py` after each change

**Tips:**
- Make small adjustments (5-10 pixels) and re-test frequently
- The corner markers on the visualization help see alignment precisely
- All 3-4 visible cards should have perfect border alignment when done
- This process takes 5-10 iterations to get perfect

### Step 3: Calibrate Material Detection Zone (Current Inventory)

After borders are perfect, calibrate where to look for material numbers (current inventory):

```bash
python test_complete_detection.py
```

Open `detection_config.py` and find the MATERIAL DETECTION ZONE SETTINGS section:

```python
MATERIAL_ZONE_START = 0.35  # Start detection at 35% from top
MATERIAL_ZONE_END = 0.52    # End detection at 52% from top
```

**What these mean:**
- `0.35` = Start detection at 35% down from the card's top edge
- `0.52` = End detection at 52% down from the card's top edge
- The **cyan box** in the visualization shows this zone

**How to Adjust:**

1. Look at `visualizeTries/complete_detection.png`
2. The **cyan box** should cover:
   - ✅ The material number (e.g., "124" below the material icon)
   - ✅ The "DELIVER" number (e.g., "100" or "25")
   - ❌ NOT the timer numbers under the clock
   - ❌ NOT the reward numbers at bottom

3. Adjust if needed in `detection_config.py`:
   - **Cyan box too high** (missing material numbers): decrease `MATERIAL_ZONE_START` (e.g., 0.35 → 0.30)
   - **Cyan box too low** (starting below materials): increase `MATERIAL_ZONE_START` (e.g., 0.35 → 0.40)
   - **Cyan box not tall enough** (missing DELIVER number): increase `MATERIAL_ZONE_END` (e.g., 0.52 → 0.55)
   - **Cyan box too tall** (catching reward numbers): decrease `MATERIAL_ZONE_END` (e.g., 0.52 → 0.48)

4. **Fine-tune click offset** in `detection_config.py`:
   ```python
   CLICK_OFFSET_Y = -50  # Pixels above the number to click (negative = up)
   ```
   - This determines where to click relative to detected numbers
   - If clicking too high: decrease absolute value (e.g., -50 → -40)
   - If clicking on the number itself: increase absolute value (e.g., -50 → -60)
   - **Goal**: Click on the material icon above the number

5. **Adjust number detection** (if numbers not being detected):
   - `BLACK_TEXT_MAX`: Increase to catch lighter text (default 80)
   - `NUMBER_MIN_WIDTH`, `NUMBER_MAX_WIDTH`: Adjust width range (default 10-60)
   - `NUMBER_MIN_HEIGHT`, `NUMBER_MAX_HEIGHT`: Adjust height range (default 10-30)

### Step 4: Calibrate DELIVER Detection Zone (Amount Needed)

After material zone is calibrated, calibrate where to look for DELIVER numbers (amount needed):

```bash
python test_deliver_detection.py
```

### Step 5: Set Average Train Capacity

The automation uses an average train capacity value instead of reading each train's capacity with OCR.

Open `detection_config.py` and find the TRAIN DISPATCHING SETTINGS section:

```python
# Average train capacity for material generation
AVERAGE_TRAIN_CAPACITY = 30     # Average capacity per train
```

**How to set this value:**

1. Click on a task that needs materials generated
2. Run `python test_train_capacity.py` a few times to see typical train capacities
3. Calculate the average of the capacities you see (usually 20-50)
4. Update `AVERAGE_TRAIN_CAPACITY` in `detection_config.py` with this average
5. The automation will use this value to estimate how many trains to dispatch

**Why average capacity?**
- Faster and more reliable than OCR for each train
- Avoids OCR errors and delays
- Still accurate enough - can go over by one train capacity if needed

**Train zone calibration (optional for testing):**

You can optionally calibrate the train zone for the test script:

```bash
python test_train_capacity.py
```

Open `detection_config.py` and find the TRAIN CAPACITY DETECTION ZONE SETTINGS section:

```python
# First train slot position (leftmost)
TRAIN_CAPACITY_ZONE_TOP = 0.81      # Top edge of capacity number zone
TRAIN_CAPACITY_ZONE_BOTTOM = 0.85    # Bottom edge of capacity number zone
TRAIN_CAPACITY_ZONE_LEFT = 0.08      # Left edge of first train slot
TRAIN_CAPACITY_ZONE_RIGHT = 0.12     # Right edge of first train slot
```

**How the automation works:**
- Checks for and collects any ready materials
- Calculates material needed: deliver_amount - warehouse_stock
- Clicks first train position (center of train zone)
- Dispatches train
- Subtracts average capacity from needed amount
- Repeats until enough material generated or no more trains available

---

**DELIVER Detection Zone Settings:**

Open `detection_config.py` and find the DELIVER AMOUNT DETECTION ZONE SETTINGS section:

```python
DELIVER_ZONE_START = 0.50   # Start detection at 50% from top
DELIVER_ZONE_END = 0.58     # End detection at 58% from top
DELIVER_ZONE_LEFT = 0.5     # Start detection at 50% from left (right side)
DELIVER_ZONE_RIGHT = 1.0    # End detection at 100% from left (right edge)
```

**What these mean:**
- `DELIVER_ZONE_START = 0.50` = Start at 50% down from the card's top edge
- `DELIVER_ZONE_END = 0.58` = End at 58% down from the card's top edge
- `DELIVER_ZONE_LEFT = 0.5` = Start at 50% from left edge (right half of card)
- `DELIVER_ZONE_RIGHT = 1.0` = End at right edge (100% from left)
- The **orange box** in the visualization shows this zone (right side only)

**How to Adjust:**

1. Look at `visualizeTries/deliver_detection.png`
2. The **orange box** should cover:
   - ✅ The DELIVER number (e.g., "100" or "25" next to "DELIVER" text)
   - ❌ NOT the material inventory numbers above
   - ❌ NOT the reward numbers at bottom

3. Adjust if needed in `detection_config.py`:
   - **Vertical adjustments:**
     - Orange box too high: decrease `DELIVER_ZONE_START` (e.g., 0.50 → 0.45)
     - Orange box too low: increase `DELIVER_ZONE_START` (e.g., 0.50 → 0.55)
     - Orange box not tall enough: increase `DELIVER_ZONE_END` (e.g., 0.58 → 0.62)
     - Orange box too tall: decrease `DELIVER_ZONE_END` (e.g., 0.58 → 0.54)
   - **Horizontal adjustments:**
     - Orange box too far left: increase `DELIVER_ZONE_LEFT` (e.g., 0.5 → 0.6)
     - Orange box too far right: decrease `DELIVER_ZONE_LEFT` (e.g., 0.5 → 0.4)
     - Orange box not wide enough: decrease `DELIVER_ZONE_LEFT` or increase `DELIVER_ZONE_RIGHT`

**Current Fine-Tuned Values (in detection_config.py):**
- Card borders: CARD_WIDTH=374, CARD_HEIGHT=610, CARD_START_X=115, CARD_START_Y=195, CARD_SPACING=397
- Material zone (inventory): MATERIAL_ZONE_START=0.38, MATERIAL_ZONE_END=0.46
- DELIVER zone (amount needed):
  - Vertical: DELIVER_ZONE_START=0.50, DELIVER_ZONE_END=0.58
  - Horizontal: DELIVER_ZONE_LEFT=0.5, DELIVER_ZONE_RIGHT=1.0 (right half only)
- Train dispatching: AVERAGE_TRAIN_CAPACITY=30
- Click offset: CLICK_OFFSET_Y=-50
- Text detection: BLACK_TEXT_MAX=80
- Number size: width 10-60px, height 10-30px
- These work on a Retina display MacBook, may need adjustment on other devices

**Note:** All settings are now centralized in `detection_config.py` - just edit that one file!

## Running the Automation

Once calibrated:
```bash
python task_automation.py
```

## Files

### Core System
- `task_automation.py` - Main automation workflow
- `task_card_detector.py` - Detects task cards and availability
- `operator_checker.py` - Checks operator availability
- `train_dispatcher.py` - Handles train dispatching
- `train_capacity_detector.py` - Detects train capacity numbers for optimal dispatching
- `resource_collector.py` - Collects warehouse resources
- `template_matcher.py` - Template matching utilities

### Calibration & Testing
- `calibrate_borders.py` - **Border calibration tool (run first!)**
- `test_complete_detection.py` - Test material inventory number detection
- `test_deliver_detection.py` - Test DELIVER amount detection
- `test_train_capacity.py` - Test train capacity number detection
- `test_material_integration.py` - Test material scanning
- `test_operator_timer.py` - Test operator timer detection

### Configuration
- **`detection_config.py`** - **Centralized calibration settings (edit this for all adjustments!)**
- `requirements.txt` - Python dependencies
- `ui_coordinates.json` - UI element positions
- `Templates/` - Image templates for detection

## Troubleshooting

### Tasks not being detected
1. Run `calibrate_borders.py` and check border alignment
2. Adjust border values in `detection_config.py`: `CARD_WIDTH`, `CARD_HEIGHT`, `CARD_START_X`, `CARD_START_Y`, `CARD_SPACING`

### Material numbers not detected (current inventory)
1. Run `test_complete_detection.py` to see detection zone (yellow/red dots should appear on numbers)
2. Adjust detection zone in `detection_config.py`: `MATERIAL_ZONE_START`, `MATERIAL_ZONE_END`
3. Adjust number size filters: `NUMBER_MIN_WIDTH`, `NUMBER_MAX_WIDTH`, `NUMBER_MIN_HEIGHT`, `NUMBER_MAX_HEIGHT`
4. Adjust text darkness: `BLACK_TEXT_MAX` (increase to catch lighter text)
5. Adjust click position: `CLICK_OFFSET_Y` (more negative = click higher)

### DELIVER numbers not detected (amount needed)
1. Run `test_deliver_detection.py` to see detection zone (blue dots should appear on DELIVER numbers)
2. Adjust detection zone in `detection_config.py`: `DELIVER_ZONE_START`, `DELIVER_ZONE_END`, `DELIVER_ZONE_LEFT`, `DELIVER_ZONE_RIGHT`
3. Check OCR debug images in `visualizeTries/deliver_ocr_debug/` to diagnose OCR issues

### Train capacity numbers not detected
1. Run `test_train_capacity.py` to see detection zone (purple dots should appear on train capacity numbers)
2. Adjust detection zone in `detection_config.py`: `TRAIN_CAPACITY_ZONE_TOP`, `TRAIN_CAPACITY_ZONE_BOTTOM`, `TRAIN_CAPACITY_ZONE_LEFT`, `TRAIN_CAPACITY_ZONE_RIGHT`
3. Check OCR debug images in `visualizeTries/train_ocr_debug/` to diagnose OCR issues

### Wrong positions being clicked
1. Verify scale factor is correct (shown in calibration output)
2. Re-run border calibration after any resolution/scaling changes
