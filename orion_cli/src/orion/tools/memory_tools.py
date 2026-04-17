"""Outils de mémoire et de planification — save_memory, write_todos."""

from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


def make_memory_tools(memory_manager):
    """Crée les tools mémoire liés au MemoryManager."""

    @tool
    def save_memory(
        content: Annotated[str, "Information importante à mémoriser pour les sessions futures"],
    ) -> str:
        """Sauvegarde une information importante dans ORION.md (mémoire persistante)."""
        try:
            memory_manager.add_memory(content)
            return f"Memory saved: {content[:100]}{'...' if len(content) > 100 else ''}"
        except Exception as e:
            return f"Error saving memory: {e}"

    @tool
    def write_todos(
        todos: Annotated[list[str], "Liste de tâches à planifier"],
        clear_existing: Annotated[bool, "Effacer les tâches existantes"] = False,
    ) -> str:
        """Gère la liste de tâches pour planifier des opérations complexes."""
        try:
            memory_manager.write_todos(todos, clear=clear_existing)
            items = "\n".join(f"  - {t}" for t in todos)
            return f"Todos updated ({len(todos)} tasks):\n{items}"
        except Exception as e:
            return f"Error writing todos: {e}"

    return [save_memory, write_todos]
