#!/usr/bin/env python3
"""
Game Area Configuration Cache
Saves and loads game area coordinates so you don't have to set them up every time.
"""

import json
from pathlib import Path
from typing import Optional, Dict


CONFIG_FILE = Path(__file__).parent / "game_area_config.json"


def load_config() -> dict:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"last_used": None, "saved_configs": {}}


def save_config(config: dict):
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def save_game_area(x: int, y: int, width: int, height: int, name: str = "default"):
    """
    Save game area coordinates.

    Args:
        x, y: Top-left corner of game area
        width, height: Game area dimensions
        name: Configuration name (default: "default")
    """
    config = load_config()

    area_config = {
        "x": x,
        "y": y,
        "width": width,
        "height": height
    }

    config["saved_configs"][name] = area_config
    config["last_used"] = name

    save_config(config)
    print(f"✅ Game area saved as '{name}'")


def load_last_game_area() -> Optional[Dict[str, int]]:
    """
    Load the last used game area configuration.

    Returns:
        Dictionary with keys: x, y, width, height, or None if not found
    """
    config = load_config()
    last_name = config.get("last_used")

    if last_name and last_name in config["saved_configs"]:
        return config["saved_configs"][last_name]

    return None


def list_saved_configs() -> Dict[str, dict]:
    """List all saved configurations."""
    config = load_config()
    return config.get("saved_configs", {})


def delete_config(name: str):
    """Delete a saved configuration."""
    config = load_config()
    if name in config.get("saved_configs", {}):
        del config["saved_configs"][name]
        if config.get("last_used") == name:
            config["last_used"] = None
        save_config(config)
        print(f"✅ Configuration '{name}' deleted")
    else:
        print(f"❌ Configuration '{name}' not found")


def print_config(area_config: dict):
    """Pretty print a game area configuration."""
    print(f"  X:      {area_config['x']}")
    print(f"  Y:      {area_config['y']}")
    print(f"  Width:  {area_config['width']}")
    print(f"  Height: {area_config['height']}")
