"""Market Pulse presentation layer.

All UI-only code (CSS injection, background rendering, component helpers)
lives here. Backend modules do not import from `src.ui`.
"""

from src.ui.theme import inject_theme
from src.ui.backgrounds import render_background
from src.ui import components

__all__ = ["inject_theme", "render_background", "components"]
