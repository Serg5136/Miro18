"""Utility for loading SVG icons as Tkinter-compatible images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image, ImageTk


class IconLoader:
    """Load and cache SVG icons for use with Tkinter widgets."""

    def __init__(self, icon_dir: Path | None = None, size: int = 28) -> None:
        self.icon_dir = icon_dir or Path(__file__).resolve().parents[2] / "assets" / "icons"
        self.size = size
        self._cache: dict[str, ImageTk.PhotoImage] = {}

    def get(self, name: str) -> ImageTk.PhotoImage:
        """Return a PhotoImage for the given icon name (without extension)."""

        if name in self._cache:
            return self._cache[name]

        svg_path = self.icon_dir / f"{name}.svg"
        if not svg_path.exists():
            raise FileNotFoundError(f"Icon not found: {svg_path}")

        png_bytes = cairosvg.svg2png(
            url=str(svg_path),
            output_width=self.size,
            output_height=self.size,
        )
        image = Image.open(BytesIO(png_bytes)).convert("RGBA")
        photo = ImageTk.PhotoImage(image)
        self._cache[name] = photo
        return photo
