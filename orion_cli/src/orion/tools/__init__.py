"""Registry des outils Orion CLI."""

from pathlib import Path
from typing import Optional

from .filesystem import make_filesystem_tools
from .shell import make_shell_tool
from .web import web_fetch, web_search
from .memory_tools import make_memory_tools


def build_tools(
    workspace: Path,
    settings,
    memory_manager,
    confirm_fn=None,
    checkpoint_manager=None,
) -> list:
    """Construit et retourne tous les outils disponibles."""
    tools = []

    # Filesystem tools (avec checkpointing si activé)
    tools.extend(make_filesystem_tools(
        workspace,
        confirm_fn=confirm_fn,
        checkpoint_manager=checkpoint_manager,
    ))

    # Shell tool
    tools.append(make_shell_tool(
        workspace=workspace,
        shell=settings.get("shell", "bash"),
        timeout=settings.get("shell_timeout", 30),
        confirm_fn=confirm_fn,
    ))

    # Web tools
    if settings.get("web_fetch_enabled", True):
        tools.append(web_fetch)
    if settings.get("web_search_enabled", True):
        tools.append(web_search)

    # Memory tools
    if memory_manager:
        tools.extend(make_memory_tools(memory_manager))

    return tools
