# Template Matching Tester - User Guide

Interactive tool for testing and tuning template matching accuracy.

## Quick Start

```bash
python -m tools.test_template_matching
```

## Step-by-Step Usage

### 1. Screenshot Capture

```
Screenshot delay in seconds [3]:
```

- Default: 3 seconds
- Gives you time to switch to game window
- Screenshot captures entire screen

**Example:**
```
Screenshot delay in seconds [3]: 5
Taking screenshot in 5 seconds...
Switch to your game window now!
  5...
  4...
  3...
  2...
  1...
✓ Screenshot captured!
```

---

### 2. Template Selection

The tool shows all available templates organized by category:

```
Available Templates:

Buttons:
  [0] CollectButtonTask.png
  [1] CollectButtonTasks.png
  [2] ConfirmButton.png
  [3] DispatchButton.png

Tasks:
  [4] AlltrainsUsed.png
  [5] BottomTaskAvailableTrains.png
  [6] LockedTaskIcon.png
  [7] TaskCompleting.png

UI:
  [8] DeliverTextLeftOfTheAmountNeeded.png
  [9] Storage.png
  [10] task.png

Materials:
  [11] Coal.png
  [12] IronOre.png
  [13] Steel.png
  ...
```

**Options:**
- Enter a number (e.g., `3` for DispatchButton.png)
- Enter a custom path (e.g., `my_template.png`)

**Example:**
```
Enter template number (or path to custom template): 3
✓ Template loaded: DispatchButton.png
  Size: 120x45 pixels
```

---

### 3. Search Region Selection

```
Search Region Options:
1. Full screen
2. Top half
3. Bottom half
4. Left half
5. Right half
6. Center 50%
7. Bottom-left corner (20% x 20%)
8. Custom region (enter coordinates)
```

**Why this matters:**
- Smaller regions = **faster** matching
- Targeted regions = **fewer false positives**
- Full screen = **slowest** but most thorough

**Examples:**

For Dispatch button (bottom-left):
```
Enter choice [1]: 7
✓ Bottom-left corner: (0, 1728, 432, 432)
```

For Task buttons (left side):
```
Enter choice [1]: 4
✓ Left half: (0, 0, 1080, 2160)
```

For custom region:
```
Enter choice [1]: 8
Enter custom region:
  X (left): 100
  Y (top): 200
  Width: 500
  Height: 300
✓ Custom region: (100, 200, 500, 300)
```

---

### 4. Matching Threshold

```
Matching Threshold
Higher = more strict (fewer false positives)
Lower = more lenient (more matches)
Typical values: 0.6 - 0.9

Enter threshold [0.8]:
```

**Guidelines:**
- `0.9` - Very strict (exact match required)
- `0.8` - Default (good balance)
- `0.7` - Moderate (more forgiving)
- `0.6` - Lenient (may get false positives)

**When to adjust:**
- Template not found? → **Lower** threshold (0.7, 0.6)
- Too many false matches? → **Raise** threshold (0.85, 0.9)

**Example:**
```
Enter threshold [0.8]: 0.7
✓ Threshold set to: 0.7
```

---

### 5. Matching Mode

```
Matching Mode:
1. Find best match only
2. Find all matches

Enter choice [1]:
```

**When to use each:**
- **Best match only** - When you only need one button (Dispatch, Confirm)
- **Find all matches** - When searching for multiple items (materials, tasks)

---

### 6. Results

**Single match example:**
```
Running Template Matching...
Template: DispatchButton.png
Region: (0, 1728, 432, 432)
Threshold: 0.7
Mode: Find best match

✓ Found match!
  Position: (216, 1890)
  Confidence: 87.34%
```

**Multiple matches example:**
```
Running Template Matching...
Template: Coal.png
Region: Full screen
Threshold: 0.6
Mode: Find all matches

✓ Found 3 match(es)
```

---

### 7. Visualization

The tool creates a visual representation:

**Saved to:** `template_match_result.png`

**Visual elements:**
- 🟦 **Blue rectangle** - Search region boundary
- 🟢 **Green box** - High confidence match (≥80%)
- 🟡 **Yellow box** - Medium confidence match (60-80%)
- 🔴 **Red box** - Low confidence match (<60%)
- 🟣 **Purple dot** - Center point of match
- **Label** - Match number and confidence percentage

**Example output:**
```
✓ Visualization saved to: template_match_result.png

Press any key in the image window to close...
```

---

### 8. Retry Options

After viewing results:

```
Options:
1. Adjust threshold and retry
2. Change search region and retry
3. Try different template
4. Exit

Enter choice [4]:
```

**Use cases:**
- **Option 1** - Fine-tune threshold without changing anything else
- **Option 2** - Test different search regions for performance
- **Option 3** - Test another template with same settings
- **Option 4** - Done testing

---

## Common Use Cases

### Testing a New Template

1. Create template image (screenshot of button/icon)
2. Save to `Templates/buttons/` (or appropriate folder)
3. Run tester
4. Select your new template
5. Start with full screen, threshold 0.8
6. Adjust threshold until it finds the match
7. Test smaller search regions for performance

### Finding Optimal Threshold

1. Take screenshot with target visible
2. Select template
3. Use full screen initially
4. Try threshold 0.8
5. If not found, lower to 0.7, 0.6
6. If too many false matches, raise to 0.85, 0.9
7. Find the sweet spot

### Optimizing Search Region

1. Find template with full screen first
2. Note where matches appear
3. Test progressively smaller regions
4. Compare speed vs. accuracy
5. Use smallest region that reliably finds target

### Debugging Template Issues

**Template not found?**
- Lower threshold (try 0.6)
- Use full screen
- Check template matches screenshot exactly
- Try edge detection mode (future feature)

**Too many false positives?**
- Raise threshold (try 0.85)
- Use smaller, targeted search region
- Improve template (more distinctive features)

**Inconsistent matches?**
- Check if UI changes (colors, lighting)
- Template might be too small/too large
- Try multiple screenshots at different times

---

## Pro Tips

1. **Always test on actual game screen** - Don't use cached screenshots
2. **Screenshot delay** - Give yourself enough time to show the UI element
3. **Start conservative** - Begin with full screen + high threshold
4. **Iterate** - Lower threshold or expand region as needed
5. **Save good templates** - Keep working templates for reuse
6. **Document thresholds** - Note what threshold works for each template
7. **Test edge cases** - Test with different UI states (day/night, different backgrounds)

---

## Performance Benchmarks

Approximate matching times on typical hardware:

| Search Region | Template Size | Time |
|--------------|---------------|------|
| Full screen (2160x3840) | 100x50 | ~500ms |
| Half screen | 100x50 | ~250ms |
| Quarter screen | 100x50 | ~125ms |
| 20% corner | 100x50 | ~50ms |

**Key takeaway:** Smaller regions = dramatically faster!

---

## Troubleshooting

### "Template image not found"
- Check file path is correct
- Ensure template is in Templates/ folder
- Use tab completion or copy/paste path

### "No match found"
- Lower threshold
- Expand search region to full screen
- Verify template matches current game state
- Check if UI element is actually visible in screenshot

### "Image window won't open"
- Headless environment (SSH/remote)
- Check saved file instead: `template_match_result.png`
- Use image viewer to open saved file

### "Import errors"
- Run from project root directory
- Ensure virtual environment is activated
- Check all dependencies installed

---

## Advanced Usage

### Batch Testing Multiple Templates

Create a script to test multiple templates:

```python
from tools.test_template_matching import TemplateMatchingTester

tester = TemplateMatchingTester()
tester.take_screenshot(delay=5)

templates = [
    "Templates/buttons/DispatchButton.png",
    "Templates/buttons/ConfirmButton.png",
    "Templates/tasks/TaskCompleting.png"
]

for template_path in templates:
    tester.select_template(template_path)
    tester.search_region = (0, 1728, 432, 432)  # Bottom-left
    tester.threshold = 0.7
    tester.run_matching(find_all=False)
    tester.visualize_results(f"result_{Path(template_path).stem}.png")
```

### Automated Threshold Finding

Test multiple thresholds to find optimal value:

```python
for threshold in [0.9, 0.85, 0.8, 0.75, 0.7]:
    tester.threshold = threshold
    if tester.run_matching():
        print(f"✓ Found match at threshold {threshold}")
        break
```
