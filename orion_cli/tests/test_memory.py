"""Tests du gestionnaire de mémoire ORION.md."""

import pytest
from pathlib import Path

from orion.memory.manager import MemoryManager, MEMORY_SECTION, TODOS_SECTION


class TestMemoryManager:
    def test_init_creates_no_file(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        assert not (tmp_path / "ORION.md").exists()

    def test_load_context_empty(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        ctx = mm.load_context()
        assert ctx == ""

    def test_add_memory_creates_file(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        mm.add_memory("Test memory entry", scope="local")
        assert (tmp_path / "ORION.md").exists()

    def test_add_memory_content(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        mm.add_memory("Remember this important fact", scope="local")
        content = (tmp_path / "ORION.md").read_text()
        assert "Remember this important fact" in content
        assert MEMORY_SECTION in content

    def test_add_multiple_memories(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        mm.add_memory("First memory", scope="local")
        mm.add_memory("Second memory", scope="local")
        content = (tmp_path / "ORION.md").read_text()
        assert "First memory" in content
        assert "Second memory" in content

    def test_write_todos(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        mm.write_todos(["Task 1", "Task 2", "Task 3"])
        content = (tmp_path / "ORION.md").read_text()
        assert TODOS_SECTION in content
        assert "Task 1" in content
        assert "Task 2" in content

    def test_get_todos(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        todos = ["A", "B", "C"]
        mm.write_todos(todos)
        assert mm.get_todos() == todos

    def test_init_project_memory(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        result = mm.init_project_memory("TestProject")
        assert (tmp_path / "ORION.md").exists()
        content = (tmp_path / "ORION.md").read_text()
        assert "TestProject" in content

    def test_init_project_memory_no_overwrite(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        (tmp_path / "ORION.md").write_text("# Existing content")
        result = mm.init_project_memory("TestProject")
        # Doit dire que le fichier existe déjà
        assert "already exists" in result
        # Contenu inchangé
        assert (tmp_path / "ORION.md").read_text() == "# Existing content"

    def test_load_context_with_local_file(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        (tmp_path / "ORION.md").write_text("# My project context\nSome important info")
        ctx = mm.load_context()
        assert "Some important info" in ctx

    def test_show_returns_string(self, tmp_path):
        mm = MemoryManager(workspace=tmp_path)
        result = mm.show()
        assert isinstance(result, str)
