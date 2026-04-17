"""Système de checkpointing — snapshots de fichiers pour /restore.

Chaque action d'outil sur un fichier crée un snapshot avant modification.
/restore permet de revenir à l'état précédent d'un ou plusieurs fichiers.
"""

import json
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FileSnapshot:
    """Snapshot d'un fichier avant modification."""
    path: str                    # Chemin absolu du fichier
    content: Optional[str]       # Contenu original (None si le fichier n'existait pas)
    existed: bool                # True si le fichier existait avant
    timestamp: float = field(default_factory=time.time)
    tool: str = ""               # Outil qui a déclenché le snapshot


@dataclass
class Checkpoint:
    """Point de restauration complet."""
    id: int
    description: str
    timestamp: float = field(default_factory=time.time)
    snapshots: list[FileSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "timestamp": self.timestamp,
            "snapshots": [
                {
                    "path": s.path,
                    "content": s.content,
                    "existed": s.existed,
                    "timestamp": s.timestamp,
                    "tool": s.tool,
                }
                for s in self.snapshots
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        cp = cls(
            id=data["id"],
            description=data["description"],
            timestamp=data.get("timestamp", 0),
        )
        cp.snapshots = [
            FileSnapshot(
                path=s["path"],
                content=s["content"],
                existed=s["existed"],
                timestamp=s.get("timestamp", 0),
                tool=s.get("tool", ""),
            )
            for s in data.get("snapshots", [])
        ]
        return cp


class CheckpointManager:
    """
    Gestionnaire de checkpoints pour /restore.

    Usage:
    1. Avant d'appeler un outil qui modifie des fichiers, appeler snapshot_file()
    2. Après la modification, appeler commit_checkpoint()
    3. /restore appelle restore() pour revenir en arrière
    """

    MAX_CHECKPOINTS = 50

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._checkpoints: list[Checkpoint] = []
        self._pending_snapshots: list[FileSnapshot] = []
        self._next_id = 1
        self._checkpoints_file = workspace / ".orion" / "checkpoints.json"
        self._load()

    def _load(self) -> None:
        """Charge les checkpoints depuis le disque."""
        if self._checkpoints_file.exists():
            try:
                data = json.loads(self._checkpoints_file.read_text())
                self._checkpoints = [Checkpoint.from_dict(c) for c in data.get("checkpoints", [])]
                self._next_id = data.get("next_id", 1)
            except (json.JSONDecodeError, KeyError):
                self._checkpoints = []

    def _save(self) -> None:
        """Persiste les checkpoints sur le disque."""
        self._checkpoints_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "next_id": self._next_id,
            "checkpoints": [c.to_dict() for c in self._checkpoints[-self.MAX_CHECKPOINTS:]],
        }
        self._checkpoints_file.write_text(json.dumps(data, indent=2))

    def snapshot_file(self, path: str | Path, tool: str = "") -> None:
        """
        Capture l'état actuel d'un fichier avant modification.
        À appeler avant toute écriture/suppression.
        """
        p = Path(path).resolve()
        existed = p.exists()
        content = None
        if existed and p.is_file():
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                content = None

        self._pending_snapshots.append(FileSnapshot(
            path=str(p),
            content=content,
            existed=existed,
            tool=tool,
        ))

    def commit_checkpoint(self, description: str = "") -> Checkpoint | None:
        """
        Crée un checkpoint avec tous les snapshots en attente.
        Retourne None s'il n'y a rien à sauvegarder.
        """
        if not self._pending_snapshots:
            return None

        cp = Checkpoint(
            id=self._next_id,
            description=description or f"Checkpoint #{self._next_id}",
            snapshots=list(self._pending_snapshots),
        )
        self._checkpoints.append(cp)
        self._next_id += 1
        self._pending_snapshots = []
        self._save()
        return cp

    def discard_pending(self) -> None:
        """Annule les snapshots en attente (si l'outil a été annulé)."""
        self._pending_snapshots = []

    def restore(self, checkpoint_id: int | None = None) -> tuple[bool, str]:
        """
        Restaure un checkpoint.
        Si checkpoint_id est None, restaure le dernier.
        Retourne (succès, message).
        """
        if not self._checkpoints:
            return False, "No checkpoints available."

        if checkpoint_id is None:
            cp = self._checkpoints[-1]
        else:
            matches = [c for c in self._checkpoints if c.id == checkpoint_id]
            if not matches:
                return False, f"Checkpoint #{checkpoint_id} not found."
            cp = matches[0]

        restored = []
        errors = []

        for snapshot in cp.snapshots:
            p = Path(snapshot.path)
            try:
                if snapshot.existed and snapshot.content is not None:
                    # Restaure le contenu original
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(snapshot.content, encoding="utf-8")
                    restored.append(f"restored: {snapshot.path}")
                elif not snapshot.existed and p.exists():
                    # Le fichier n'existait pas — on le supprime
                    p.unlink()
                    restored.append(f"deleted: {snapshot.path}")
            except OSError as e:
                errors.append(f"Error restoring {snapshot.path}: {e}")

        # Supprime le checkpoint restauré de la liste
        self._checkpoints = [c for c in self._checkpoints if c.id != cp.id]
        self._save()

        msg_parts = [f"Checkpoint #{cp.id} restored ({cp.description}):"]
        msg_parts.extend(f"  {r}" for r in restored)
        if errors:
            msg_parts.extend(f"  ERROR: {e}" for e in errors)
        return len(errors) == 0, "\n".join(msg_parts)

    def list_checkpoints(self) -> str:
        """Liste tous les checkpoints disponibles."""
        if not self._checkpoints:
            return "No checkpoints available."
        lines = [f"Available checkpoints ({len(self._checkpoints)}):"]
        for cp in reversed(self._checkpoints[-20:]):
            ts = datetime.fromtimestamp(cp.timestamp).strftime("%H:%M:%S")
            n_files = len(cp.snapshots)
            lines.append(f"  #{cp.id:3d}  [{ts}]  {cp.description}  ({n_files} files)")
        return "\n".join(lines)

    def get_pending_count(self) -> int:
        return len(self._pending_snapshots)
