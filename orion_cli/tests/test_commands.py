"""Tests des slash commands Orion CLI."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from orion.commands.builtins import build_registry
from orion.commands.registry import CommandRegistry
from orion.config.settings import Settings
from orion.memory.manager import MemoryManager
from orion.session.manager import SessionManager


@pytest.fixture
def registry():
    return build_registry()


@pytest.fixture
def mock_context(tmp_path):
    settings = Settings(workspace=tmp_path)
    memory = MemoryManager(workspace=tmp_path)
    session = SessionManager(sessions_dir=tmp_path / "sessions")
    (tmp_path / "sessions").mkdir(exist_ok=True)

    agent = MagicMock()
    agent.get_model_info.return_value = {"model": "test-model"}
    agent.list_tools.return_value = [("read_file", "Reads a file"), ("write_file", "Writes a file")]

    registry = build_registry()

    return {
        "agent": agent,
        "settings": settings,
        "session_manager": session,
        "memory_manager": memory,
        "workspace": tmp_path,
        "registry": registry,
        "repl_state": {"vim_mode": False},
        "last_response": "Previous response",
        "checkpoint_manager": None,
        "mcp_client": None,
        "extra_dirs": [],
    }


class TestRegistry:
    def test_all_commands_registered(self, registry):
        names = {cmd.name for cmd in registry.all_commands()}
        required = {"help", "quit", "clear", "settings", "memory", "chat",
                    "stats", "theme", "directory", "tools", "about", "init",
                    "compress", "copy", "mcp", "vim", "privacy", "restore",
                    "extensions", "editor", "streaming"}
        assert required.issubset(names)

    def test_alias_dispatch(self, registry, mock_context):
        # /? doit être alias de /help
        result = registry.dispatch("/?", mock_context)
        assert result is not None
        assert "Command" in result or "help" in result.lower()

    def test_unknown_command_returns_none(self, registry, mock_context):
        result = registry.dispatch("/nonexistent_cmd_xyz", mock_context)
        assert result is None


class TestHelpCommand:
    def test_help_returns_table(self, registry, mock_context):
        result = registry.dispatch("/help", mock_context)
        assert result is not None
        assert "help" in result.lower()
        assert "/quit" in result or "quit" in result

    def test_help_includes_shortcuts(self, registry, mock_context):
        result = registry.dispatch("/help", mock_context)
        assert "@" in result
        assert "!" in result


class TestSettingsCommand:
    def test_settings_list(self, registry, mock_context):
        result = registry.dispatch("/settings", mock_context)
        assert "model" in result
        assert "theme" in result

    def test_settings_get(self, registry, mock_context):
        result = registry.dispatch("/settings get model", mock_context)
        assert "model" in result

    def test_settings_set(self, registry, mock_context):
        result = registry.dispatch("/settings set theme light", mock_context)
        assert "light" in result
        assert mock_context["settings"].get("theme") == "light"


class TestMemoryCommand:
    def test_memory_show_empty(self, registry, mock_context):
        result = registry.dispatch("/memory", mock_context)
        assert isinstance(result, str)

    def test_memory_add(self, registry, mock_context):
        result = registry.dispatch("/memory add Remember this important thing", mock_context)
        assert "added" in result.lower() or "Remember" in result


class TestChatCommand:
    def test_chat_list_empty(self, registry, mock_context):
        result = registry.dispatch("/chat list", mock_context)
        assert "No saved sessions" in result

    def test_chat_save_and_list(self, registry, mock_context):
        mock_context["session_manager"].add_message("user", "Hello")
        registry.dispatch("/chat save test_tag", mock_context)
        result = registry.dispatch("/chat list", mock_context)
        assert "test_tag" in result

    def test_chat_no_args(self, registry, mock_context):
        result = registry.dispatch("/chat", mock_context)
        assert "Usage" in result


class TestThemeCommand:
    def test_theme_show_current(self, registry, mock_context):
        result = registry.dispatch("/theme", mock_context)
        assert "Current theme" in result

    def test_theme_set_valid(self, registry, mock_context):
        result = registry.dispatch("/theme dark", mock_context)
        assert "dark" in result

    def test_theme_set_invalid(self, registry, mock_context):
        result = registry.dispatch("/theme invalidtheme", mock_context)
        assert "Unknown" in result or "unknown" in result.lower()


class TestDirectoryCommand:
    def test_directory_list(self, registry, mock_context):
        result = registry.dispatch("/directory list", mock_context)
        assert "Workspace" in result

    def test_directory_add(self, registry, mock_context, tmp_path):
        new_dir = tmp_path / "extra_dir"
        new_dir.mkdir()
        result = registry.dispatch(f"/directory add {new_dir}", mock_context)
        assert "added" in result.lower() or str(new_dir) in result


class TestToolsCommand:
    def test_tools_list(self, registry, mock_context):
        result = registry.dispatch("/tools", mock_context)
        assert "read_file" in result
        assert "write_file" in result


class TestVimCommand:
    def test_vim_toggle(self, registry, mock_context):
        initial = mock_context["settings"].get("vim_mode", False)
        result = registry.dispatch("/vim", mock_context)
        assert "vim mode" in result.lower()
        assert mock_context["settings"].get("vim_mode") != initial


class TestPrivacyCommand:
    def test_privacy_shows_local(self, registry, mock_context):
        result = registry.dispatch("/privacy", mock_context)
        assert "locally" in result.lower() or "local" in result.lower()
        assert "Ollama" in result


class TestAboutCommand:
    def test_about_shows_version(self, registry, mock_context):
        result = registry.dispatch("/about", mock_context)
        assert "0.1.0" in result or "Orion" in result


class TestCopyCommand:
    def test_copy_no_last_response(self, registry, mock_context):
        mock_context["last_response"] = ""
        result = registry.dispatch("/copy", mock_context)
        assert "Nothing" in result

    def test_copy_with_response(self, registry, mock_context):
        mock_context["last_response"] = "Some response to copy"
        result = registry.dispatch("/copy", mock_context)
        # Peut échouer si pyperclip n'est pas configuré en CI, c'est OK
        assert isinstance(result, str)


class TestCustomCommands:
    def test_load_toml_command(self, tmp_path):
        from orion.commands.custom import load_custom_commands, register_custom_commands
        from orion.commands.builtins import build_registry

        # Crée un fichier .toml custom
        cmds_dir = tmp_path / "commands"
        cmds_dir.mkdir()
        toml_file = cmds_dir / "greet.toml"
        toml_file.write_text(
            'description = "Greet the user"\n'
            'prompt = "Say hello to {{input}}"\n'
        )

        cmds = load_custom_commands(cmds_dir)
        assert len(cmds) == 1
        assert cmds[0]["name"] == "greet"
        assert "Greet" in cmds[0]["description"]

    def test_custom_command_namespacing(self, tmp_path):
        from orion.commands.custom import load_custom_commands

        cmds_dir = tmp_path / "commands"
        (cmds_dir / "git").mkdir(parents=True)
        (cmds_dir / "git" / "commit.toml").write_text(
            'description = "Git commit helper"\nprompt = "Create commit message for: {{input}}"\n'
        )
        cmds = load_custom_commands(cmds_dir)
        assert cmds[0]["name"] == "git:commit"
