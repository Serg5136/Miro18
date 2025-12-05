import json
import os
from typing import Dict

CONFIG_FILENAME = "_mini_miro_config.json"

THEMES: Dict[str, Dict[str, str]] = {
    "light": {
        "bg": "#ffffff",
        "grid": "#f0f0f0",
        "card_default": "#fff9b1",
        "card_outline": "#444444",
        "frame_bg": "#f5f5f5",
        "frame_outline": "#888888",
        "frame_collapsed_bg": "#e0e0ff",
        "frame_collapsed_outline": "#aaaaaa",
        "text": "#000000",
        "connection": "#555555",
        "connection_label": "#333333",
        "minimap_bg": "#ffffff",
        "minimap_card_outline": "#888888",
        "minimap_frame_outline": "#aaaaaa",
        "minimap_viewport": "#ff0000",
    },
    "dark": {
        "bg": "#222222",
        "grid": "#333333",
        "card_default": "#444444",
        "card_outline": "#dddddd",
        "frame_bg": "#333333",
        "frame_outline": "#aaaaaa",
        "frame_collapsed_bg": "#444466",
        "frame_collapsed_outline": "#cccccc",
        "text": "#ffffff",
        "connection": "#dddddd",
        "connection_label": "#eeeeee",
        "minimap_bg": "#222222",
        "minimap_card_outline": "#aaaaaa",
        "minimap_frame_outline": "#888888",
        "minimap_viewport": "#ff6666",
    },
}


def load_theme_name(themes: Dict[str, Dict[str, str]] = THEMES, filename: str = CONFIG_FILENAME) -> str:
    """Load the selected theme name from config file if valid."""
    theme_name = "light"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            saved_theme = cfg.get("theme")
            if saved_theme in themes:
                theme_name = saved_theme
        except Exception:
            pass
    return theme_name


def save_theme_name(theme_name: str, filename: str = CONFIG_FILENAME) -> None:
    """Persist the selected theme name to config file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"theme": theme_name}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
