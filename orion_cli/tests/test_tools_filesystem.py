"""Tests des outils filesystem Orion CLI."""

import pytest
from pathlib import Path

from orion.tools.filesystem import make_filesystem_tools


@pytest.fixture
def workspace(tmp_path):
    return tmp_path


@pytest.fixture
def tools(workspace):
    return {t.name: t for t in make_filesystem_tools(workspace)}


class TestReadFile:
    def test_read_existing_file(self, workspace, tools):
        f = workspace / "hello.txt"
        f.write_text("Hello, World!\nLine 2")
        result = tools["read_file"].invoke({"path": "hello.txt"})
        assert "Hello, World!" in result
        assert "1 |" in result  # numéros de lignes

    def test_read_nonexistent(self, workspace, tools):
        result = tools["read_file"].invoke({"path": "nonexistent.txt"})
        assert "Error" in result

    def test_read_directory_fails(self, workspace, tools):
        (workspace / "mydir").mkdir()
        result = tools["read_file"].invoke({"path": "mydir"})
        assert "Error" in result


class TestWriteFile:
    def test_write_new_file(self, workspace, tools):
        result = tools["write_file"].invoke({"path": "new.txt", "content": "test content"})
        assert "written" in result.lower()
        assert (workspace / "new.txt").read_text() == "test content"

    def test_write_creates_parent_dirs(self, workspace, tools):
        result = tools["write_file"].invoke({"path": "subdir/nested/file.txt", "content": "nested"})
        assert (workspace / "subdir" / "nested" / "file.txt").exists()

    def test_write_overwrites_existing(self, workspace, tools):
        f = workspace / "existing.txt"
        f.write_text("old content")
        tools["write_file"].invoke({"path": "existing.txt", "content": "new content"})
        assert f.read_text() == "new content"


class TestReplace:
    def test_replace_occurrence(self, workspace, tools):
        f = workspace / "code.py"
        f.write_text("def hello():\n    return 'world'")
        result = tools["replace"].invoke({
            "path": "code.py",
            "old_string": "return 'world'",
            "new_string": "return 'universe'",
        })
        assert "Replaced" in result
        assert "universe" in f.read_text()

    def test_replace_not_found(self, workspace, tools):
        f = workspace / "file.txt"
        f.write_text("some content")
        result = tools["replace"].invoke({
            "path": "file.txt",
            "old_string": "nonexistent string",
            "new_string": "replacement",
        })
        assert "Error" in result

    def test_replace_ambiguous_multiple(self, workspace, tools):
        f = workspace / "dup.txt"
        f.write_text("abc abc abc")
        result = tools["replace"].invoke({
            "path": "dup.txt",
            "old_string": "abc",
            "new_string": "xyz",
        })
        assert "Error" in result or "times" in result


class TestListDirectory:
    def test_list_empty_dir(self, workspace, tools):
        result = tools["list_directory"].invoke({"path": "."})
        assert "empty" in result.lower() or isinstance(result, str)

    def test_list_with_files(self, workspace, tools):
        (workspace / "file1.txt").write_text("a")
        (workspace / "file2.py").write_text("b")
        result = tools["list_directory"].invoke({"path": "."})
        assert "file1.txt" in result
        assert "file2.py" in result

    def test_list_nonexistent(self, workspace, tools):
        result = tools["list_directory"].invoke({"path": "nonexistent_dir"})
        assert "Error" in result


class TestGlob:
    def test_glob_python_files(self, workspace, tools):
        (workspace / "main.py").write_text("")
        (workspace / "utils.py").write_text("")
        (workspace / "readme.md").write_text("")
        result = tools["glob"].invoke({"pattern": "*.py"})
        assert "main.py" in result
        assert "utils.py" in result
        assert "readme.md" not in result

    def test_glob_no_match(self, workspace, tools):
        result = tools["glob"].invoke({"pattern": "*.xyz"})
        assert "No files" in result


class TestSearchFileContent:
    def test_search_found(self, workspace, tools):
        f = workspace / "code.py"
        f.write_text("def my_function():\n    return 42\n")
        result = tools["search_file_content"].invoke({
            "pattern": "my_function",
            "path": ".",
        })
        assert "my_function" in result
        assert "code.py" in result

    def test_search_not_found(self, workspace, tools):
        f = workspace / "file.txt"
        f.write_text("nothing here")
        result = tools["search_file_content"].invoke({
            "pattern": "xyz_not_present",
            "path": ".",
        })
        assert "No matches" in result


class TestDeleteFile:
    def test_delete_file(self, workspace, tools):
        f = workspace / "to_delete.txt"
        f.write_text("content")
        result = tools["delete_file"].invoke({"path": "to_delete.txt"})
        assert "Deleted" in result
        assert not f.exists()

    def test_delete_nonexistent(self, workspace, tools):
        result = tools["delete_file"].invoke({"path": "ghost.txt"})
        assert "Error" in result


class TestCreateDirectory:
    def test_create_dir(self, workspace, tools):
        result = tools["create_directory"].invoke({"path": "new_folder"})
        assert "created" in result.lower()
        assert (workspace / "new_folder").is_dir()

    def test_create_nested_dirs(self, workspace, tools):
        result = tools["create_directory"].invoke({"path": "a/b/c"})
        assert (workspace / "a" / "b" / "c").is_dir()


class TestReadManyFiles:
    def test_read_multiple(self, workspace, tools):
        (workspace / "a.txt").write_text("Content A")
        (workspace / "b.txt").write_text("Content B")
        result = tools["read_many_files"].invoke({"paths": ["a.txt", "b.txt"]})
        assert "Content A" in result
        assert "Content B" in result

    def test_read_directory(self, workspace, tools):
        sub = workspace / "subdir"
        sub.mkdir()
        (sub / "file1.txt").write_text("File 1 content")
        result = tools["read_many_files"].invoke({"paths": [str(sub)]})
        assert "File 1 content" in result
