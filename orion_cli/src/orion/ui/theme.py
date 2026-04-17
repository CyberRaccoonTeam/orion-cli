"""Gestion des thèmes visuels Orion CLI."""

from rich.console import Console
from rich.theme import Theme

from orion.config.defaults import THEMES

_current_theme_name = "dark"
_console: Console | None = None


def get_theme_name() -> str:
    return _current_theme_name


def set_theme(name: str) -> bool:
    global _current_theme_name, _console
    if name not in THEMES:
        return False
    _current_theme_name = name
    _console = None  # Reset pour recréer avec nouveau thème
    return True


def get_theme_colors() -> dict:
    return THEMES.get(_current_theme_name, THEMES["dark"])


def get_console() -> Console:
    global _console
    if _console is None:
        colors = get_theme_colors()
        theme = Theme({
            "orion.primary": colors["primary"],
            "orion.secondary": colors["secondary"],
            "orion.success": colors["success"],
            "orion.warning": colors["warning"],
            "orion.error": colors["error"],
            "orion.muted": colors["muted"],
            "orion.tool": colors["tool_color"],
            "orion.assistant": colors["assistant_color"],
            "orion.user": colors["user_color"],
        })
        _console = Console(theme=theme, highlight=True)
    return _console


def available_themes() -> list[str]:
    return list(THEMES.keys())
