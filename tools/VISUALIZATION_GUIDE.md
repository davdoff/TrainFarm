# Visualization Tools Guide

## Quick Start ⚡

**Want to see all detection zones? Run this:**

```bash
cd /Users/davidbotosineanu/Documents/GitHub/TrainFarm
python tools/visualize_all_areas.py
```

1. Script counts down 3 seconds
2. Switch to your game window (fullscreen F11)
3. Screenshot taken automatically
4. Check result: `visualizeTries/all_detection_zones.png`

**That's it!** No setup, no config needed.

---

## Overview

These tools help you visualize detection zones, task cards, and automation areas.

**All fixed and ready to use!** ✅

---

## How to Run

**Always run from project root:**

```bash
cd /Users/davidbotosineanu/Documents/GitHub/TrainFarm

# Run any visualization tool
python tools/visualize_all_areas.py
python tools/visualize_realtime.py
python tools/visualize.py
```

Or with venv:
```bash
./venv/bin/python tools/visualize_all_areas.py
```

---

## Available Tools

### 1. `visualize_all_areas.py` - Complete Overview ⭐ SIMPLIFIED

**Super simple - just shows all zones!**

Shows ALL detection zones on one screenshot:
- Task card positions (4 cards)
- Material detection zones (within each card)
- Deliver amount zones (within each card)
- Train capacity zones (4 trains at bottom)
- Click offset indicators (where automation clicks)

**When to use:**
- Check if detection zones align with game UI
- Verify after changing `detection_config.py`
- Debug position/sizing issues

**How it works:**
1. Waits 3 seconds (switch to game!)
2. Takes fullscreen screenshot
3. Draws all zones with colors
4. Saves to `visualizeTries/all_detection_zones.png`

**Run:**
```bash
python tools/visualize_all_areas.py

# Then check the image:
open visualizeTries/all_detection_zones.png
```

**No setup required!** Just run and it captures your screen.

---

### 2. `visualize_realtime.py` - Live Preview

Shows real-time detection as you move/play:
- Live task card detection
- Updates continuously
- Press 'q' to quit

**When to use:**
- Test detection in different game states
- See how zones adapt to scrolling
- Debug dynamic detection issues

**Run:**
```bash
python tools/visualize_realtime.py
```

**Controls:**
- Press `q` to quit
- Window updates every frame

---

### 3. `visualize.py` - Menu System

Interactive menu to launch visualization tools.

**Run:**
```bash
python tools/visualize.py
```

---

## What Each Tool Shows

### Color Legend

| Color | Meaning |
|-------|---------|
| 🟦 **Blue** | Task card boundaries |
| 🟩 **Green** | Material detection zones |
| 🟨 **Yellow** | Deliver amount zones |
| 🟥 **Red** | Important markers (click offsets) |
| 🟪 **Purple** | Train/operator zones |

### Labeled Zones

- **Task Card 1, 2, 3** - Individual task card positions
- **Material Zone** - Where material numbers are detected
- **Deliver Zone** - Where "deliver amount" text is found
- **Train Zone** - Where train capacity numbers are
- **Click Offset** - Where automation clicks (above/below numbers)

---

## Troubleshooting

### "No module named 'src'"

✅ **Fixed!** All scripts now add project root to sys.path.

Just make sure you run from project root:
```bash
cd /Users/davidbotosineanu/Documents/GitHub/TrainFarm
python tools/visualize_all_areas.py
```

### "Window not found" or blank visualization

Make sure:
1. Game is open and in fullscreen (F11)
2. You've run the automation at least once
3. Game area is set up correctly

### Zones don't align with UI

1. Check `src/config/detection_config.py`
2. Adjust percentage values (0.0-1.0 range)
3. Re-run visualization to verify
4. Repeat until aligned

---

## Adjusting Detection Zones

If visualization shows zones are misaligned:

1. **Open:** `src/config/detection_config.py`

2. **Find the zone:** (e.g., `MATERIAL_ZONE_START`)

3. **Adjust percentage:**
   ```python
   MATERIAL_ZONE_START = 0.38  # 38% from top of card
   # Change to:
   MATERIAL_ZONE_START = 0.40  # 40% from top
   ```

4. **Test:** Run visualization again
   ```bash
   python tools/visualize_all_areas.py
   ```

5. **Repeat** until zones align perfectly

---

## Example Workflow

**Calibrating Material Detection:**

1. Run visualization:
   ```bash
   python tools/visualize_all_areas.py
   ```

2. Check if green "Material Zone" box covers the numbers

3. If too high/low, edit `detection_config.py`:
   ```python
   MATERIAL_ZONE_START = 0.40  # Adjust this
   MATERIAL_ZONE_END = 0.48    # And this
   ```

4. Re-run visualization

5. Repeat until perfect alignment

6. Test automation to verify it works

---

## Tips

- **Take screenshots** of visualizations for reference
- **Compare before/after** when adjusting config
- **Use real-time mode** to see detection during gameplay
- **Check multiple game states** (different tasks, materials, etc.)
- **Save working configs** before experimenting

---

## Files Modified

✅ `tools/visualize_all_areas.py` - Fixed imports, added sys.path
✅ `tools/visualize_realtime.py` - Fixed imports, added sys.path
✅ `tools/visualize.py` - Already working (no imports needed)

All scripts can now be run from project root without errors!

---

**Happy Visualizing!** 🎨
