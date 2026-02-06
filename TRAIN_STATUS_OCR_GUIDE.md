# Train Status OCR Detection Guide

## Overview

The train dispatcher now uses **OCR-based text detection** instead of unstable template matching to determine if trains are available for dispatch.

## How It Works

### Text States

The train status region displays different text depending on availability:

1. **Trains Available**
   - Text: `"TAP THE TRAIN TO"` (+ additional text about destination)
   - Means: You can dispatch more trains

2. **All Trains Used**
   - Text: `"PLEASE WAIT UNTIL THE TRAINS REACH THEIR DESTINATION"`
   - Means: All trains are dispatched, must wait

### Detection Method

- **OCR**: Reads text from a configured screen region
- **Fuzzy Matching**: Handles OCR errors with 70% threshold
- **Multiple Preprocessing**: Tries 4 different image processing methods for best accuracy
- **Fallback**: Uses template matching if OCR completely fails

## Setup Instructions

### Step 1: Configure the Region

Use the region configuration tool to precisely define where the train status text appears:

```bash
python tools/configure_regions.py
```

1. Start a task or material generation to show the train status text
2. Run the tool
3. Draw a rectangle around the text area
4. Press **'n'** and name it: `TRAIN_STATUS_TEXT`
5. Press **'g'** to generate code
6. Copy the generated values to `src/config/detection_config.py`

**Example values to update:**
```python
TRAIN_STATUS_TEXT_LEFT = 0.30      # Your value here
TRAIN_STATUS_TEXT_TOP = 0.70       # Your value here
TRAIN_STATUS_TEXT_RIGHT = 0.70     # Your value here
TRAIN_STATUS_TEXT_BOTTOM = 0.80    # Your value here
```

### Step 2: Test the OCR Detection

Run the test tool to verify OCR is working:

```bash
python tools/test_train_status_ocr.py
```

**What the test does:**
1. Captures the configured region
2. Tries multiple OCR preprocessing methods
3. Shows detected text from each method
4. Tests the actual dispatcher logic
5. Saves debug images for review

**Expected output:**
```
OCR Results:
  1. Original Grayscale: 'TAP THE TRAIN TO DELIVER COAL'
  2. Simple Threshold: 'TAP THE TRAIN TO'
  ...

Testing with TrainDispatcher:
  Detected: 'TAP THE TRAIN TO DELIVER COAL'
  Result: AVAILABLE

✅ OCR working!
```

### Step 3: Review Debug Images

The test creates several images:
- `train_status_region_original.png` - Raw captured region
- `train_status_region_*_*.png` - Various preprocessing methods
- `train_status_visualization.png` - Full screenshot with region highlighted

**Check these images to verify:**
- Region captures the text completely
- Text is clearly visible
- No extra UI elements in the region

### Step 4: Adjust if Needed

If OCR isn't working well:

1. **Region too small/wrong**: Reconfigure with `configure_regions.py`
2. **Text not clear**: Ensure game is in fullscreen (F11)
3. **Wrong preprocessing**: The dispatcher tries all methods automatically
4. **Threshold too strict**: Lower `TRAIN_STATUS_MATCH_THRESHOLD` in `detection_config.py`

## Configuration Options

### detection_config.py Settings

```python
# Region coordinates (percentages 0.0-1.0)
TRAIN_STATUS_TEXT_LEFT = 0.30
TRAIN_STATUS_TEXT_TOP = 0.70
TRAIN_STATUS_TEXT_RIGHT = 0.70
TRAIN_STATUS_TEXT_BOTTOM = 0.80

# Fuzzy matching threshold (0.0-1.0)
# At least 70% of important text must match
TRAIN_STATUS_MATCH_THRESHOLD = 0.70
```

### Adjusting Match Threshold

- **Default: 0.70** (70% match required)
- **More strict: 0.80-0.90** (fewer false positives, may miss some valid text)
- **More lenient: 0.50-0.60** (catches more OCR errors, may have false positives)

## How It Integrates

The OCR detection is used in `TrainDispatcher.check_all_trains_used()`:

```python
# Called during train dispatch loop
if self.check_all_trains_used():
    print("All trains dispatched!")
    break

# Dispatch next train
self.dispatch_train()
```

**Workflow:**
1. Click first train
2. Check status text with OCR
3. If "TAP THE TRAIN TO" → Click Dispatch button
4. If "PLEASE WAIT" → Stop dispatching (all trains used)
5. Repeat until all trains dispatched

## Troubleshooting

### Issue: No text detected

**Symptoms:**
```
⚠️  No text detected in train status region
```

**Solutions:**
1. Verify region coordinates with `test_train_status_ocr.py`
2. Check if text is visible when capturing
3. Reconfigure region with `configure_regions.py`
4. Ensure game is in fullscreen mode

### Issue: Wrong text detected

**Symptoms:**
```
OCR Text: 'GARBAGE TEXT'
⚠️  Status unclear from OCR
```

**Solutions:**
1. Region may include extra UI elements
2. Make region smaller/more precise
3. Check debug images to see what's being captured
4. Try different Tesseract config (advanced)

### Issue: False positives/negatives

**Symptoms:**
- Thinks trains are available when they're not
- Thinks all trains used when more available

**Solutions:**
1. Adjust `TRAIN_STATUS_MATCH_THRESHOLD`
2. Check if text format changed in game update
3. Review debug images from test tool
4. Update expected text strings in `train_dispatcher.py` if game text changed

### Issue: OCR too slow

**Symptoms:**
- Noticeable delay between train dispatches

**Solutions:**
1. Normal - OCR takes ~0.5-1 second
2. Multiple preprocessing methods ensure accuracy
3. Speed vs accuracy tradeoff (currently optimized for accuracy)

## Technical Details

### OCR Processing Pipeline

1. **Capture** region screenshot
2. **Convert** to grayscale
3. **Preprocess** with 4 methods:
   - Original grayscale
   - Simple threshold (150)
   - Adaptive threshold
   - Otsu threshold
4. **OCR** each version
5. **Select** longest text (most complete)
6. **Match** against expected strings with fuzzy matching

### Fuzzy Matching Algorithm

Uses `difflib.SequenceMatcher` for similarity comparison:
- Normalizes text (uppercase, trim spaces)
- Calculates ratio (0.0-1.0)
- Also checks for exact substring matches
- Returns True if ratio ≥ threshold OR substring found

### Fallback Behavior

If OCR completely fails:
1. Tries template matching as backup
2. If that fails too, assumes trains available (conservative)
3. Logs warnings for debugging

## Best Practices

1. **Configure region precisely** - Extra UI elements confuse OCR
2. **Test after configuration** - Always run `test_train_status_ocr.py`
3. **Keep region minimal** - Just the text, nothing else
4. **Use fullscreen mode** - Ensures consistent text size/position
5. **Review debug images** - Check what OCR actually sees

## Advanced: Modifying Expected Text

If game updates change the text, update these in `train_dispatcher.py`:

```python
# In check_all_trains_used():
if self._fuzzy_text_match(text, "PLEASE WAIT UNTIL", threshold):
    # All trains used

if self._fuzzy_text_match(text, "TAP THE TRAIN TO", threshold):
    # Trains available
```

Change the strings to match new game text.

## Files Modified

- `src/core/train_dispatcher.py` - Added OCR methods and updated logic
- `src/config/detection_config.py` - Added region config and threshold
- `tools/test_train_status_ocr.py` - New test tool
- `tools/configure_regions.py` - Existing tool (use for region setup)

## Summary

✅ **More stable** than template matching
✅ **Handles OCR errors** with fuzzy matching (70% threshold)
✅ **Multiple preprocessing** methods for accuracy
✅ **Easy to configure** with visual tools
✅ **Easy to test** with dedicated test script
✅ **Fallback safety** if OCR fails completely

## Quick Command Reference

```bash
# Configure the region
python tools/configure_regions.py

# Test OCR detection
python tools/test_train_status_ocr.py

# Run automation (uses new OCR automatically)
python main.py
```
