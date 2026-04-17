"""Gestion de la configuration Orion CLI."""

import json
import os
from pathlib import Path
from typing import Any

from .defaults import DEFAULT_SETTINGS


class Settings:
    """Gestionnaire de configuration centralisé."""

    GLOBAL_CONFIG_DIR = Path.home() / ".config" / "orion"
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "settings.json"
    LOCAL_CONFIG_DIR_NAME = ".orion"
    LOCAL_CONFIG_FILE_NAME = "settings.json"

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Charge les settings en fusionnant global + local (local prioritaire)."""
        self._data = dict(DEFAULT_SETTINGS)

        # 1. Config globale (~/.config/orion/settings.json)
        if self.GLOBAL_CONFIG_FILE.exists():
            try:
                with open(self.GLOBAL_CONFIG_FILE) as f:
                    global_cfg = json.load(f)
                self._data.update(global_cfg)
            except (json.JSONDecodeError, OSError):
                pass

        # 2. Config locale (.orion/settings.json dans le workspace)
        local_cfg_file = self.workspace / self.LOCAL_CONFIG_DIR_NAME / self.LOCAL_CONFIG_FILE_NAME
        if local_cfg_file.exists():
            try:
                with open(local_cfg_file) as f:
                    local_cfg = json.load(f)
                self._data.update(local_cfg)
            except (json.JSONDecodeError, OSError):
                pass

        # 3. Variables d'environnement (ORION_MODEL, ORION_WORKSPACE, ...)
        for key in DEFAULT_SETTINGS:
            env_key = f"ORION_{key.upper()}"
            if env_key in os.environ:
                self._data[key] = os.environ[env_key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, scope: str = "global") -> None:
        """Modifie un paramètre et le persiste."""
        self._data[key] = value
        if scope == "global":
            self._save_global()
        elif scope == "local":
            self._save_local()

    def _save_global(self) -> None:
        self.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.GLOBAL_CONFIG_FILE, "w") as f:
            # Ne sauvegarde que les clés non-default ou modifiées
            overrides = {k: v for k, v in self._data.items() if v != DEFAULT_SETTINGS.get(k)}
            json.dump(overrides, f, indent=2)

    def _save_local(self) -> None:
        local_dir = self.workspace / self.LOCAL_CONFIG_DIR_NAME
        local_dir.mkdir(parents=True, exist_ok=True)
        local_file = local_dir / self.LOCAL_CONFIG_FILE_NAME
        existing = {}
        if local_file.exists():
            with open(local_file) as f:
                existing = json.load(f)
        # Fusion
        existing.update({k: v for k, v in self._data.items() if v != DEFAULT_SETTINGS.get(k)})
        with open(local_file, "w") as f:
            json.dump(existing, f, indent=2)

    def all(self) -> dict[str, Any]:
        return dict(self._data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)
