# TrainFarm Project Architecture & File Guide

> **Purpose:** This file helps Claude (and developers) quickly navigate the codebase, understand file importance, and know where to make changes.

**Last Updated:** 2026-01-29

---

## 📋 Quick Reference

| Task | Primary File(s) | Notes |
|------|----------------|-------|
| Run the automation | `main.py` | Always run from project root |
| Change detection thresholds | `src/config/detection_config.py` | Central config for all detection zones |
| Fix template matching | `src/detectors/template_matcher.py` | Core matching algorithm |
| Modify task workflow | `src/core/task_automation.py` | Main orchestrator (~1200 lines) |
| Add new UI elements | `src/config/ui_config.py` | Define templates and paths |
| Debug/test templates | `tools/diagnose_matching.py` | Template testing tool |
| Test freebies | `test_freebie_advanced.py` | Freebie template testing |

---

## 🎯 File Importance Rankings

### ⭐⭐⭐ CRITICAL (Core Functionality)

These files are essential to the automation. Changes here affect everything.

#### Entry Point
- **`main.py`** - Main entry point, starts automation loop
  - Imports: `src.core.task_automation.main`
  - **Always run this file, never run src/ files directly**

#### Core Automation
- **`src/core/task_automation.py`** (~1200 lines) - Main workflow orchestrator
  - Handles: Task menu, material scanning, train dispatching, material generation
  - Most complex file in project
  - Contains: `TaskAutomation` class with `run_full_workflow()`

- **`src/detectors/template_matcher.py`** - Template matching engine
  - Functions: `find_template_on_screen()`, `find_all_matches()`, `get_scale_factor()`
  - Handles Retina/HiDPI displays
  - Used by ALL detection modules

#### Configuration
- **`src/config/detection_config.py`** - Centralized detection settings
  - Card positions, zones, thresholds
  - All values are **window-relative percentages** (0.0-1.0)
  - Calibrate using tools in `tools/` folder

### ⭐⭐ IMPORTANT (Major Features)

These files implement major features. Changes affect specific workflows.

#### Automation Components
- **`src/core/train_dispatcher.py`** - Train dispatch logic
  - Finds Dispatch button, checks completion status
  - Used for both tasks and material generation

- **`src/core/resource_collector.py`** - Collect button detection
  - Finds and clicks "Collect" buttons for completed resources
  - Works in both task and operator contexts

- **`src/core/resource_generator.py`** - Factory/Mine handler
  - Detects location type (factory vs mine)
  - Handles material crafting in factories

- **`src/core/freebie_collector.py`** - Freebie whistle collector
  - Collects freebies during idle time
  - **Takes fresh screenshot each iteration** (freebies move!)

#### Detectors
- **`src/detectors/task_card_detector.py`** - Task card detection
  - Finds task cards, checks availability (completing/locked)
  - Handles scrolling to find available tasks

- **`src/detectors/color_detector.py`** - Color-based detection
  - Detects red/black text for material status
  - Used for insufficient material detection

#### Configuration & Utils
- **`src/config/ui_config.py`** - UI element definitions
  - Template paths for buttons (task, storage, etc.)
  - **Templates are in `Templates/` subdirectories** (ui/, tasks/, Materials/, buttons/)

- **`src/utils/window_manager.py`** - Window/screen management
  - Handles fullscreen vs windowed mode
  - Currently using fullscreen only

### ⭐ UTILITY (Supporting)

These files provide support functionality.

- **`src/config/game_area_cache.py`** - Saves game window bounds
  - **Currently unused** (fullscreen mode only)
  - Would be used for windowed mode

- **`src/detectors/material_scanner.py`** - Material icon detection
  - Finds empty click areas on task cards

### 🛠️ TOOLS (Development & Testing)

Place all testing, debugging, and development tools here.

#### Template Testing
- **`tools/diagnose_matching.py`** - Template matching diagnostic
  - Tests template quality, shows confidence scores
  - Creates visualizations

- **`tools/test_template_matching.py`** - Interactive template tester
  - Full-featured template testing UI
  - Adjust thresholds, regions, etc.

- **`test_freebie_advanced.py`** ⚠️ **MOVE TO tools/**
  - Advanced freebie testing (currently in root)
  - **TODO: Relocate to tools/ folder**

- **`test_freebie_debug.py`** - Quick freebie debug script
  - Compares `find_template_on_screen` vs `find_all_matches`

#### Setup & Calibration
- **`tools/interactive_setup.py`** - Game area setup wizard
  - **Currently unused** (fullscreen mode)

- **`tools/example_template_test.py`** - Template testing example

#### Documentation
- **`tools/TEMPLATE_TESTER_GUIDE.md`** - Guide for template testing tools

### 📦 TEMPLATES (Assets)

All template images organized by category:

```
Templates/
├── ui/                      # UI elements (task button, storage, etc.)
├── tasks/                   # Task-related (locked icon, completing, etc.)
├── Materials/               # Material icons (Coal, Steel, etc.)
└── buttons/                 # Buttons (Dispatch, Collect, Confirm, etc.)
```

**Naming Convention:**
- Use descriptive names: `DispatchButton.png`, `TaskCompleting.png`
- PascalCase for multi-word names
- No spaces in filenames

### 📄 DOCUMENTATION

- **`README.md`** - Project overview and quick start
- **`HOW_TO_RUN.md`** - Detailed run instructions
- **`FIX_IDE_IMPORTS.md`** - IDE configuration guide
- **`IMPORT_FIXES.md`** - Import cleanup summary
- **`FINAL_FIXES.md`** - Recent fixes summary
- **`TEMPLATE_MATCHING_AUDIT.md`** - Template matching analysis
- **`BLUE_BUTTON_DETECTION_EXPLAINED.md`** - Blue button detection docs
- **`BLUE_BUTTON_REGION_REFERENCE.md`** - Blue button region reference

### 🗑️ DEPRECATED/REDUNDANT FILES

These files are **no longer used** and can be deleted:

#### Old Root-Level Files (Moved to src/)
- ❌ `color_detector.py` → Use `src/detectors/color_detector.py`
- ❌ `detection_config.py` → Use `src/config/detection_config.py`
- ❌ `game_area_cache.py` → Use `src/config/game_area_cache.py`
- ❌ `interactive_setup.py` → Use `tools/interactive_setup.py`
- ❌ `material_scanner.py` → Use `src/detectors/material_scanner.py`
- ❌ `resource_collector.py` → Use `src/core/resource_collector.py`
- ❌ `resource_generator.py` → Use `src/core/resource_generator.py`
- ❌ `task_automation.py` → Use `src/core/task_automation.py`
- ❌ `task_card_detector.py` → Use `src/detectors/task_card_detector.py`
- ❌ `template_matcher.py` → Use `src/detectors/template_matcher.py`
- ❌ `train_dispatcher.py` → Use `src/core/train_dispatcher.py`
- ❌ `ui_config.py` → Use `src/config/ui_config.py`
- ❌ `window_manager.py` → Use `src/utils/window_manager.py`

#### Old Visualization Scripts
- ❌ `visualize.py` → Use tools in `tools/` or `visualizeTries/`
- ❌ `visualize_all_areas.py`
- ❌ `visualize_realtime.py`

#### Git Conflicts
- ⚠️ `ui_coordinates.json` - Has merge conflicts (UU status)
  - Can be deleted (regenerates automatically)

---

## 🏗️ Project Structure

```
TrainFarm/
├── main.py                          ⭐⭐⭐ Entry point
├── requirements.txt                  📦 Dependencies
│
├── src/                             ⭐⭐⭐ Main source code
│   ├── core/                        ⭐⭐⭐ Core automation logic
│   │   ├── task_automation.py       ⭐⭐⭐ Main orchestrator
│   │   ├── train_dispatcher.py      ⭐⭐ Train dispatch
│   │   ├── resource_collector.py    ⭐⭐ Collect buttons
│   │   ├── resource_generator.py    ⭐⭐ Factory/Mine
│   │   └── freebie_collector.py     ⭐⭐ Freebie collection
│   │
│   ├── detectors/                   ⭐⭐⭐ Detection modules
│   │   ├── template_matcher.py      ⭐⭐⭐ Core matching
│   │   ├── task_card_detector.py    ⭐⭐ Task cards
│   │   ├── color_detector.py        ⭐⭐ Color detection
│   │   └── material_scanner.py      ⭐ Material icons
│   │
│   ├── config/                      ⭐⭐⭐ Configuration
│   │   ├── detection_config.py      ⭐⭐⭐ Detection zones
│   │   ├── ui_config.py            ⭐⭐ UI elements
│   │   └── game_area_cache.py      ⭐ Window bounds
│   │
│   └── utils/                       ⭐⭐ Utilities
│       └── window_manager.py        ⭐⭐ Screen management
│
├── tools/                           🛠️ Development tools
│   ├── diagnose_matching.py         🛠️ Template diagnostics
│   ├── test_template_matching.py    🛠️ Template tester
│   ├── interactive_setup.py         🛠️ Setup wizard
│   └── ...
│
├── Templates/                       📦 Template images
│   ├── ui/                         📦 UI elements
│   ├── tasks/                      📦 Task-related
│   ├── Materials/                  📦 Material icons
│   └── buttons/                    📦 Buttons
│
├── visualizeTries/                  🖼️ Debug visualizations
│   └── (generated debug images)
│
└── venv/                           🐍 Virtual environment
    └── (Python packages)
```

---

## 📝 Development Conventions

### Where to Add New Files

| File Type | Location | Example |
|-----------|----------|---------|
| **Core automation logic** | `src/core/` | `src/core/my_new_automator.py` |
| **Detection algorithms** | `src/detectors/` | `src/detectors/my_detector.py` |
| **Configuration** | `src/config/` | `src/config/my_config.py` |
| **Utilities** | `src/utils/` | `src/utils/my_helper.py` |
| **Testing scripts** | `tools/` | `tools/test_my_feature.py` |
| **Debug scripts** | `tools/` | `tools/debug_something.py` |
| **Templates** | `Templates/<category>/` | `Templates/ui/MyButton.png` |
| **Documentation** | Project root | `MY_GUIDE.md` |

### Naming Conventions

**Python Files:**
- `snake_case.py` for modules
- `PascalCase` for class names
- Functions: `verb_noun()` (e.g., `find_template`, `click_button`)

**Template Images:**
- `PascalCase.png` for multi-word (e.g., `DispatchButton.png`)
- Descriptive names (what it is, not what it does)
- No spaces, use camelCase or underscores

**Config Variables:**
- `SCREAMING_SNAKE_CASE` for constants
- Percentages use `0.0-1.0` range (not 0-100)

### Import Standards

**All imports at the top of file:**
```python
# Standard library
import time
import cv2

# Third-party
import numpy as np

# Project imports
from src.core.something import MyClass
from src.config.detection_config import MY_CONSTANT
```

**Never import inside functions!** ❌

### Template Matching Best Practices

1. **Capture templates:**
   - Same resolution as automation will run
   - Fullscreen mode (F11)
   - Crop tightly around element

2. **Test templates immediately:**
   ```bash
   python tools/diagnose_matching.py Templates/ui/MyTemplate.png
   ```

3. **Threshold guidelines:**
   - Buttons (large, distinct): `0.7`
   - Icons (small): `0.6`
   - Text: `0.5`
   - Start high, lower if needed

---

## 🔧 Common Tasks Guide

### 1. Fix Template Matching Issue

1. Test template with diagnostic:
   ```bash
   python tools/diagnose_matching.py Templates/path/to/template.png
   ```

2. Check confidence score in output
3. If < 0.6, recapture template
4. Adjust threshold in code if needed

### 2. Add New UI Element

1. Capture template screenshot
2. Save to `Templates/ui/ElementName.png`
3. Add to `src/config/ui_config.py`:
   ```python
   "element_name": UIElement(
       name="element_name",
       template_path=str(TEMPLATES_DIR / "ui" / "ElementName.png")
   )
   ```
4. Use in code:
   ```python
   self.locate_and_click("element_name", threshold=0.7)
   ```

### 3. Modify Detection Zone

1. Open `src/config/detection_config.py`
2. Find the relevant zone (e.g., `MATERIAL_ZONE_START`)
3. Adjust percentage (0.0-1.0 range)
4. Test with visualization tools

### 4. Debug Workflow Issue

Add debug text files explaining new module only if asked

### 5. Add Testing Script

1. Create in `tools/test_my_feature.py`
2. Use project imports:
   ```python
   from src.core.my_module import MyClass
   ```
3. Run from project root:
   ```bash
   python tools/test_my_feature.py
   ```

---

## ⚠️ Common Pitfalls

### 1. Running Wrong File
❌ `python src/core/task_automation.py` → `ModuleNotFoundError`
✅ `python main.py` → Works!

### 2. Imports Inside Functions
❌ `def my_func(): import cv2` → Yellow underlines
✅ `import cv2` at top of file → Clean!

### 3. Wrong Template Path
❌ `Templates/task.png` → FileNotFoundError
✅ `Templates/ui/task.png` → Works!

### 4. Threshold Too High
❌ `threshold=0.8` → No matches
✅ `threshold=0.6` → Finds templates

### 5. Freebies Not Collecting
❌ Take 1 screenshot, find all, click all
✅ Loop: screenshot → find one → click → repeat

---

## 🎯 Quick Wins for Optimization

1. **Lower default thresholds** in `task_automation.py` from 0.8 → 0.7
2. **Delete deprecated files** listed in "Redundant Files" section
3. **Move test files** from root to `tools/` folder
4. **Add more debug output** in `task_automation.py` workflow
5. **Create visualization** for task card detection

---

## 📊 Codebase Stats

- **Total Python files:** ~30+
- **Core modules:** 5 (task_automation, train_dispatcher, etc.)
- **Detectors:** 4 (template_matcher, task_card_detector, etc.)
- **Config files:** 3
- **Testing tools:** 5+
- **Deprecated files:** 13+ (can be deleted)

---

## 🚀 For Future Claude Sessions

**Read this file first to:**
1. Understand project structure quickly
2. Know which files to prioritize
3. Find where to add new code
4. Avoid deprecated files
5. Follow established conventions

**Most Edited Files (by priority):**
1. `src/core/task_automation.py` - Main workflow
2. `src/config/detection_config.py` - Tune detection
3. `src/detectors/template_matcher.py` - Fix matching
4. `tools/diagnose_matching.py` - Debug templates

**Never Edit:**
- Files in `venv/` (virtual environment)
- Files in `__pycache__/` (Python cache)
- Deprecated files listed above

---

**END OF ARCHITECTURE GUIDE**

*Last verified: 2026-01-29*
*Next review: When adding major features*
