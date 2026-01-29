#!/usr/bin/env python3
"""
UI Configuration Manager
Stores and manages UI element locations, coordinates, and offsets.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class UIElement:
    """Represents a UI element with its template and calculated coordinates."""
    name: str
    template_path: str
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    confidence: Optional[float] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class UIOffset:
    """Represents an offset from a reference UI element."""
    reference_element: str
    offset_x: int
    offset_y: int
    description: str = ""


class UIConfig:
    """Manages UI element configurations and coordinates."""

    # Template paths
    # Get project root (go up from src/config/ to project root)
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    TEMPLATES_DIR = PROJECT_ROOT / "Templates"

    # UI Element definitions
    ELEMENTS = {
        "task_button": UIElement(
            name="task_button",
            template_path=str(TEMPLATES_DIR / "ui" / "task.png")
        ),
        "full_task": UIElement(
            name="full_task",
            template_path=str(TEMPLATES_DIR / "tasks" / "BottomTaskAvailableTrains.png")
        ),
        "material_icon": UIElement(
            name="material_icon",
            template_path=str(TEMPLATES_DIR / "Materials" / "Coal.png")
        ),
        "storage": UIElement(
            name="storage",
            template_path=str(TEMPLATES_DIR / "ui" / "Storage.png")
        ),
    }

    # Offsets from reference elements
    OFFSETS = {
        # FullTask is positioned relative to task_button
        "full_task_from_task": UIOffset(
            reference_element="task_button",
            offset_x=0,  # Will be calibrated
            offset_y=100,  # Will be calibrated
            description="FullTask location relative to Task button"
        ),

        # Material number is below the material icon
        "material_number_from_icon": UIOffset(
            reference_element="material_icon",
            offset_x=0,
            offset_y=30,  # Approximate, will be calibrated
            description="Material count number below material icon"
        ),
    }

    def __init__(self, config_file: str = "ui_coordinates.json"):
        self.config_file = Path(config_file)
        self.load_config()

    def load_config(self):
        """Load saved coordinates from JSON file."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                for name, element_data in data.get('elements', {}).items():
                    if name in self.ELEMENTS:
                        element = UIElement.from_dict(element_data)
                        self.ELEMENTS[name] = element

    def save_config(self):
        """Save current coordinates to JSON file."""
        data = {
            'elements': {name: elem.to_dict() for name, elem in self.ELEMENTS.items()}
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_element(self, name: str, match_data: Dict):
        """Update element coordinates from template matching result."""
        if name in self.ELEMENTS:
            elem = self.ELEMENTS[name]
            elem.x = match_data['x']
            elem.y = match_data['y']
            elem.width = match_data['width']
            elem.height = match_data['height']
            elem.confidence = match_data['confidence']
            self.save_config()

    def get_element(self, name: str) -> Optional[UIElement]:
        """Get UI element by name."""
        return self.ELEMENTS.get(name)

    def get_coordinates(self, name: str) -> Optional[Tuple[int, int]]:
        """Get (x, y) coordinates of an element."""
        elem = self.get_element(name)
        if elem and elem.x is not None and elem.y is not None:
            return (elem.x, elem.y)
        return None

    def calculate_offset_position(self, offset_name: str) -> Optional[Tuple[int, int]]:
        """Calculate position using an offset from a reference element."""
        if offset_name not in self.OFFSETS:
            return None

        offset = self.OFFSETS[offset_name]
        ref_coords = self.get_coordinates(offset.reference_element)

        if ref_coords is None:
            return None

        return (
            ref_coords[0] + offset.offset_x,
            ref_coords[1] + offset.offset_y
        )

    def calibrate_offset(self, offset_name: str, actual_x: int, actual_y: int):
        """Calibrate an offset based on actual found position vs reference."""
        if offset_name not in self.OFFSETS:
            return

        offset = self.OFFSETS[offset_name]
        ref_coords = self.get_coordinates(offset.reference_element)

        if ref_coords:
            offset.offset_x = actual_x - ref_coords[0]
            offset.offset_y = actual_y - ref_coords[1]
