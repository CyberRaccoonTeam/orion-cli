"""Gestionnaire de sessions — save/resume/list/delete conversations."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class SessionManager:
    """
    Gère les sessions de conversation (équivalent /chat save|resume|list|delete).
    Stocke les historiques dans ~/.config/orion/sessions/<tag>.json

    Si `autosave_path` est fourni, l'historique courant est persisté sur disque
    à chaque message et rechargé automatiquement au démarrage.
    """

    def __init__(
        self,
        sessions_dir: Path | None = None,
        autosave_path: Path | None = None,
    ):
        self.sessions_dir = sessions_dir or (Path.home() / ".config" / "orion" / "sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._autosave_path = autosave_path
        self._current_history: list[dict[str, Any]] = []
        self._session_start = time.time()
        self._token_count = 0
        self._message_count = 0

        # Restore last active conversation if autosave exists
        if self._autosave_path and self._autosave_path.exists():
            try:
                data = json.loads(self._autosave_path.read_text(encoding="utf-8"))
                self._current_history = data.get("messages", [])
                self._message_count = len(self._current_history)
            except (json.JSONDecodeError, OSError):
                self._current_history = []

    def add_message(self, role: str, content: str) -> None:
        """Ajoute un message à l'historique courant et persiste si autosave activé."""
        self._current_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self._message_count += 1
        self._autosave()

    def _autosave(self) -> None:
        """Persiste l'historique courant sur disque (silencieux si erreur)."""
        if not self._autosave_path:
            return
        try:
            self._autosave_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "saved_at": datetime.now().isoformat(),
                "messages": self._current_history,
            }
            self._autosave_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    def get_history(self) -> list[dict[str, Any]]:
        """Retourne l'historique courant (pour LangChain)."""
        return list(self._current_history)

    def get_langchain_messages(self):
        """Convertit l'historique en messages LangChain."""
        from langchain_core.messages import HumanMessage, AIMessage
        messages = []
        for msg in self._current_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages

    def save(self, tag: str) -> str:
        """Sauvegarde la session courante sous un tag."""
        if not tag:
            return "Error: Tag required. Usage: /chat save <tag>"
        session_file = self.sessions_dir / f"{tag}.json"
        data = {
            "tag": tag,
            "created_at": datetime.now().isoformat(),
            "messages": self._current_history,
            "stats": self.get_stats(),
        }
        session_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return f"Session saved as '{tag}' ({len(self._current_history)} messages)"

    def resume(self, tag: str) -> str:
        """Reprend une session sauvegardée."""
        session_file = self.sessions_dir / f"{tag}.json"
        if not session_file.exists():
            return f"Error: Session '{tag}' not found."
        data = json.loads(session_file.read_text(encoding="utf-8"))
        self._current_history = data.get("messages", [])
        self._message_count = len(self._current_history)
        return f"Session '{tag}' resumed ({len(self._current_history)} messages)"

    def list_sessions(self) -> str:
        """Liste toutes les sessions sauvegardées (format texte)."""
        files = sorted(self.sessions_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        files = [f for f in files if f.stem != "_current"]
        if not files:
            return "No saved sessions."
        lines = ["Saved sessions:"]
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                created = data.get("created_at", "unknown")
                n_messages = len(data.get("messages", []))
                lines.append(f"  {f.stem:20s}  {created[:16]}  ({n_messages} messages)")
            except (json.JSONDecodeError, OSError):
                lines.append(f"  {f.stem}  (corrupted)")
        return "\n".join(lines)

    def list_sessions_structured(self) -> list[dict]:
        """Liste toutes les sessions sauvegardées (format JSON structuré)."""
        files = sorted(self.sessions_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        files = [f for f in files if f.stem != "_current"]
        result = []
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                result.append({
                    "tag": f.stem,
                    "created_at": data.get("created_at", ""),
                    "message_count": len(data.get("messages", [])),
                })
            except (json.JSONDecodeError, OSError):
                result.append({"tag": f.stem, "created_at": "", "message_count": 0})
        return result

    def delete(self, tag: str) -> str:
        """Supprime une session sauvegardée."""
        session_file = self.sessions_dir / f"{tag}.json"
        if not session_file.exists():
            return f"Error: Session '{tag}' not found."
        session_file.unlink()
        return f"Session '{tag}' deleted."

    def clear(self) -> None:
        """Efface l'historique courant et supprime le fichier autosave."""
        self._current_history = []
        self._message_count = 0
        if self._autosave_path and self._autosave_path.exists():
            try:
                self._autosave_path.unlink()
            except OSError:
                pass

    def compress(self, summary: str) -> str:
        """Remplace l'historique par un résumé compressé."""
        self._current_history = [{
            "role": "system",
            "content": f"[Compressed context]\n{summary}",
            "timestamp": datetime.now().isoformat(),
        }]
        return "Context compressed."

    def update_token_count(self, count: int) -> None:
        self._token_count += count

    def get_stats(self) -> dict:
        """Retourne les statistiques de session."""
        elapsed = time.time() - self._session_start
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return {
            "Messages": self._message_count,
            "Turns": self._message_count // 2,
            "Tokens (approx)": self._token_count,
            "Duration": duration,
            "Session started": datetime.fromtimestamp(self._session_start).strftime("%H:%M:%S"),
        }
