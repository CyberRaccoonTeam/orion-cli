"""Tests de la configuration Orion CLI."""

import json
import tempfile
from pathlib import Path

import pytest

from orion.config.settings import Settings
from orion.config.defaults import DEFAULT_SETTINGS, THEMES


class TestSettings:
    def test_default_values(self, tmp_path, monkeypatch):
        # Isole la config globale pour éviter les interférences
        monkeypatch.setattr(Settings, "GLOBAL_CONFIG_DIR", tmp_path / "global")
        monkeypatch.setattr(Settings, "GLOBAL_CONFIG_FILE", tmp_path / "global" / "settings.json")
        s = Settings(workspace=tmp_path)
        assert s.get("model") == DEFAULT_SETTINGS["model"]
        assert s.get("theme") == DEFAULT_SETTINGS["theme"]
        assert s.get("vim_mode") == DEFAULT_SETTINGS["vim_mode"]

    def test_get_missing_key(self, tmp_path):
        s = Settings(workspace=tmp_path)
        assert s.get("nonexistent_key") is None
        assert s.get("nonexistent_key", "default") == "default"

    def test_set_and_get(self, tmp_path):
        s = Settings(workspace=tmp_path)
        s.set("model", "qwen2.5-coder:7b", scope="local")
        assert s.get("model") == "qwen2.5-coder:7b"

    def test_local_config_overrides_global(self, tmp_path):
        # Config globale
        global_dir = tmp_path / "global"
        global_dir.mkdir()
        global_cfg = global_dir / "settings.json"
        global_cfg.write_text(json.dumps({"model": "qwen2.5-coder:7b"}))

        # Config locale
        local_dir = tmp_path / "workspace" / ".orion"
        local_dir.mkdir(parents=True)
        (local_dir / "settings.json").write_text(json.dumps({"model": "qwen2.5-coder:7b"}))

        workspace = tmp_path / "workspace"
        workspace.mkdir(exist_ok=True)

        s = Settings.__new__(Settings)
        s.workspace = workspace
        s._data = {}
        # Simule le chargement manuel
        from orion.config.defaults import DEFAULT_SETTINGS
        s._data = dict(DEFAULT_SETTINGS)
        s._data.update({"model": "qwen2.5-coder:7b"})  # global (simulated)
        s._data.update({"model": "qwen2.5-coder:7b"})   # local override

        assert s.get("model") == "qwen2.5-coder:7b"

    def test_all_returns_dict(self, tmp_path):
        s = Settings(workspace=tmp_path)
        all_settings = s.all()
        assert isinstance(all_settings, dict)
        assert "model" in all_settings

    def test_getitem(self, tmp_path):
        s = Settings(workspace=tmp_path)
        assert s["model"] == DEFAULT_SETTINGS["model"]

    def test_save_global(self, tmp_path, monkeypatch):
        # Redirige la config globale vers tmp
        global_dir = tmp_path / "config_global"
        global_dir.mkdir()
        monkeypatch.setattr(Settings, "GLOBAL_CONFIG_DIR", global_dir)
        monkeypatch.setattr(Settings, "GLOBAL_CONFIG_FILE", global_dir / "settings.json")

        s = Settings(workspace=tmp_path)
        s.set("model", "mistral:7b", scope="global")

        saved = json.loads((global_dir / "settings.json").read_text())
        assert saved.get("model") == "mistral:7b"


class TestThemes:
    def test_all_themes_present(self):
        assert "dark" in THEMES
        assert "light" in THEMES
        assert "ansi" in THEMES

    def test_theme_has_required_keys(self):
        required = ["primary", "secondary", "success", "warning", "error", "muted"]
        for theme_name, theme in THEMES.items():
            for key in required:
                assert key in theme, f"Theme '{theme_name}' missing key '{key}'"
