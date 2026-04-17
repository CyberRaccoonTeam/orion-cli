"""Gestionnaire de mémoire hiérarchique — équivalent GEMINI.md."""

from datetime import datetime
from pathlib import Path


MEMORY_FILE_NAME = "ORION.md"
TODOS_SECTION = "## Todos"
MEMORY_SECTION = "## Memory"


class MemoryManager:
    """
    Gère la mémoire persistante via les fichiers ORION.md.

    Hiérarchie (comme Gemini CLI avec GEMINI.md) :
    1. ~/.config/orion/ORION.md  (mémoire globale)
    2. <workspace>/ORION.md      (mémoire projet)
    3. Sous-dossiers ORION.md    (mémoire locale — chargées si dans le contexte)
    """

    def __init__(self, workspace: Path, global_dir: Path | None = None):
        self.workspace = workspace
        self.global_dir = global_dir or (Path.home() / ".config" / "orion")
        self.global_memory_file = self.global_dir / MEMORY_FILE_NAME
        self.local_memory_file = workspace / MEMORY_FILE_NAME
        self._todos: list[str] = []

    def load_context(self) -> str:
        """Charge et fusionne toute la mémoire disponible en un contexte string."""
        sections = []

        # Mémoire globale
        if self.global_memory_file.exists():
            content = self.global_memory_file.read_text(encoding="utf-8")
            if content.strip():
                sections.append(f"# Global Memory (from ~/.config/orion/ORION.md)\n\n{content}")

        # Mémoire projet
        if self.local_memory_file.exists():
            content = self.local_memory_file.read_text(encoding="utf-8")
            if content.strip():
                sections.append(f"# Project Memory (from {self.workspace.name}/ORION.md)\n\n{content}")

        return "\n\n---\n\n".join(sections) if sections else ""

    def add_memory(self, content: str, scope: str = "local") -> None:
        """Ajoute une entrée mémoire dans ORION.md."""
        target = self.local_memory_file if scope == "local" else self.global_memory_file
        target.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n- [{timestamp}] {content}"

        existing = target.read_text(encoding="utf-8") if target.exists() else ""

        if MEMORY_SECTION in existing:
            # Insère après la section Memory
            idx = existing.index(MEMORY_SECTION) + len(MEMORY_SECTION)
            new_content = existing[:idx] + entry + existing[idx:]
        else:
            # Crée la section
            new_content = existing.rstrip() + f"\n\n{MEMORY_SECTION}\n{entry}\n"

        target.write_text(new_content, encoding="utf-8")

    def write_todos(self, todos: list[str], clear: bool = False) -> None:
        """Met à jour la liste de todos dans ORION.md local."""
        self._todos = todos if clear else self._todos + todos
        target = self.local_memory_file
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_text(encoding="utf-8") if target.exists() else ""

        todos_block = f"{TODOS_SECTION}\n" + "\n".join(f"- [ ] {t}" for t in self._todos) + "\n"

        if TODOS_SECTION in existing:
            # Remplace la section existante
            import re
            new_content = re.sub(
                rf"{re.escape(TODOS_SECTION)}\n(.*?)(\n## |\Z)",
                todos_block + r"\2",
                existing,
                flags=re.DOTALL,
            )
        else:
            new_content = existing.rstrip() + f"\n\n{todos_block}"

        target.write_text(new_content, encoding="utf-8")

    def get_todos(self) -> list[str]:
        return list(self._todos)

    def show(self) -> str:
        """Retourne la mémoire complète formatée pour affichage."""
        context = self.load_context()
        return context if context else "(No memory loaded)"

    def init_project_memory(self, project_name: str = "") -> str:
        """Initialise un fichier ORION.md pour le projet courant."""
        if self.local_memory_file.exists():
            return f"ORION.md already exists at {self.local_memory_file}"

        name = project_name or self.workspace.name
        content = f"""# {name} — Orion Memory

This file contains persistent context for Orion CLI in this project.
Edit it to add instructions, notes, or context for future sessions.

## Project Context

- Project: {name}
- Workspace: {self.workspace}

## Memory

## Todos

"""
        self.local_memory_file.write_text(content, encoding="utf-8")
        return str(self.local_memory_file)
