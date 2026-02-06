# TrainFarm Automation

Automated task completion system for the TrainFarm game.

## Project Structure

```
TrainFarm/
├── main.py                     # Main entry point - run this!
├── src/                        # Main source code
│   ├── core/                   # Core automation logic
│   │   ├── task_automation.py  # Main workflow orchestrator
│   │   ├── resource_collector.py  # Collect button handler
│   │   ├── resource_generator.py  # Mine/Factory handler
│   │   └── train_dispatcher.py    # Train dispatch logic
│   │
│   ├── detectors/              # Detection modules
│   │   ├── task_card_detector.py  # Task card detection
│   │   ├── material_scanner.py    # Material icon detection
│   │   ├── color_detector.py      # Color-based detection
│   │   └── template_matcher.py    # Image template matching
│   │
│   ├── config/                 # Configuration
│   │   ├── detection_config.py    # Detection settings
│   │   ├── ui_config.py           # UI element configurations
│   │   └── game_area_cache.py     # Game area cache
│   │
│   └── utils/                  # Utilities
│       └── window_manager.py      # Window management
│
├── tools/                      # Development tools
│   ├── interactive_setup.py    # Setup wizard
│   ├── visualize.py            # Visualization tool
│   ├── visualize_all_areas.py  # Area visualization
│   └── visualize_realtime.py   # Real-time visualization
│
└── Templates/                  # Template images
    ├── buttons/                # Button templates
    ├── tasks/                  # Task-related templates
    └── ui/                     # UI element templates
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set game to fullscreen mode (F11)**

3. **Run the automation:**
   ```bash
   python main.py
   ```

3. **Run visualization tools:**
   ```bash
   python -m tools.visualize              # General visualization
   python -m tools.visualize_realtime     # Real-time visualization
   python -m tools.test_template_matching # Test template matching accuracy
   python tools/configure_regions.py      # Configure detection regions interactively
   ```

## How It Works

1. **Opens Task Menu** - Clicks the task button
2. **Finds Available Task** - Scans for non-completing, non-locked tasks
3. **Analyzes Materials** - Detects black/red numbers (inventory/warehouse)
4. **Generates Materials** - Dispatches trains or crafts in factory if needed
5. **Dispatches Trains** - Completes the task
6. **Repeats** - Checks every 5 seconds for new tasks

## Configuration

- **Fullscreen mode only** - Game must be in fullscreen (F11)
- Detection thresholds in `src/config/detection_config.py`
- Template paths in `Templates/` folder
- Polling interval: 5 seconds (configurable in `task_automation.py`)

## Template Matching Tester

Interactive tool to test and tune template matching accuracy:

```bash
python -m tools.test_template_matching
```

**Features:**
- Select any template from Templates/ folder
- Define custom search regions (full screen, halves, corners, custom)
- Adjust matching threshold (0.0 - 1.0)
- Find single best match or all matches
- Visual results with bounding boxes and confidence scores
- Save visualization to file

**Usage:**
1. Run the tool
2. Take a screenshot (switches to game window)
3. Select a template to search for
4. Define the search region
5. Set matching threshold
6. View results with confidence scores

Perfect for:
- Testing new templates before using them
- Finding optimal threshold values
- Debugging template matching issues
- Understanding search region impact on performance

## Region Configuration Tool

Interactive visual tool to precisely define detection zones and lookup areas:

```bash
python tools/configure_regions.py
```

**Features:**
- Click and drag to draw rectangular regions
- Visual overlay of all saved regions
- Automatic conversion to percentage coordinates (0.0-1.0)
- Generate ready-to-use Python code for detection_config.py
- Save/load regions from JSON
- Real-time coordinate display

**Controls:**
- Click & Drag: Draw region
- N: Name and save region
- C: Clear current selection
- D: Delete last region
- S: Save all to file
- G: Generate Python code
- R: Retake screenshot
- Q: Quit

**Perfect for:**
- Defining new detection zones
- Calibrating OCR regions
- Setting up template search areas
- Precise coordinate configuration

See `tools/REGION_CONFIGURATION_GUIDE.md` for detailed usage.

## Emergency Stop

Move your mouse to the **top-left corner** to emergency stop the automation.
