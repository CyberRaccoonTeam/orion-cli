"""Outils de système de fichiers — équivalent Gemini CLI file tools."""

import fnmatch
import os
import shutil
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


def _resolve_path(path: str, workspace: Path) -> Path:
    """Résout un chemin relatif au workspace."""
    p = Path(path)
    if not p.is_absolute():
        p = workspace / p
    return p.resolve()


def _is_safe_path(path: Path, workspace: Path) -> bool:
    """Vérifie que le chemin est dans le workspace ou home."""
    try:
        path.resolve().relative_to(workspace.resolve())
        return True
    except ValueError:
        # Autorise aussi ~/ et /tmp
        try:
            path.resolve().relative_to(Path.home().resolve())
            return True
        except ValueError:
            return str(path).startswith("/tmp")


def make_filesystem_tools(workspace: Path, confirm_fn=None, checkpoint_manager=None):
    """Crée les outils filesystem liés au workspace donné."""

    @tool
    def read_file(path: Annotated[str, "Chemin du fichier à lire"]) -> str:
        """Lit le contenu d'un fichier."""
        p = _resolve_path(path, workspace)
        if not p.exists():
            return f"Error: File not found: {path}"
        if not p.is_file():
            return f"Error: Not a file: {path}"
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            # Ajoute numéros de lignes pour contexte
            numbered = "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
            return f"File: {path} ({len(lines)} lines)\n\n{numbered}"
        except OSError as e:
            return f"Error reading file: {e}"

    @tool
    def write_file(
        path: Annotated[str, "Chemin du fichier à créer/écraser"],
        content: Annotated[str, "Contenu à écrire"],
    ) -> str:
        """Crée ou écrase un fichier avec le contenu donné."""
        p = _resolve_path(path, workspace)
        if not _is_safe_path(p, workspace):
            return f"Error: Path outside workspace: {path}"
        if confirm_fn:
            if not confirm_fn("write_file", f"Write file: {path}", content[:300]):
                if checkpoint_manager:
                    checkpoint_manager.discard_pending()
                return "Aborted by user."
        if checkpoint_manager:
            checkpoint_manager.snapshot_file(p, tool="write_file")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            if checkpoint_manager:
                checkpoint_manager.commit_checkpoint(f"write_file: {path}")
            return f"File written: {path} ({len(content)} bytes)"
        except OSError as e:
            if checkpoint_manager:
                checkpoint_manager.discard_pending()
            return f"Error writing file: {e}"

    @tool
    def replace(
        path: Annotated[str, "Chemin du fichier à éditer"],
        old_string: Annotated[str, "Texte exact à remplacer"],
        new_string: Annotated[str, "Texte de remplacement"],
    ) -> str:
        """Remplace une occurrence exacte dans un fichier (édition précise)."""
        p = _resolve_path(path, workspace)
        if not p.exists():
            return f"Error: File not found: {path}"
        if not _is_safe_path(p, workspace):
            return f"Error: Path outside workspace: {path}"
        try:
            content = p.read_text(encoding="utf-8")
            if old_string not in content:
                return f"Error: String not found in {path}"
            count = content.count(old_string)
            if count > 1:
                return f"Error: String found {count} times in {path}. Be more specific."
            new_content = content.replace(old_string, new_string, 1)
            if confirm_fn:
                diff_preview = f"- {old_string[:100]}\n+ {new_string[:100]}"
                if not confirm_fn("replace", f"Edit file: {path}", diff_preview):
                    return "Aborted by user."
            if checkpoint_manager:
                checkpoint_manager.snapshot_file(p, tool="replace")
            p.write_text(new_content, encoding="utf-8")
            if checkpoint_manager:
                checkpoint_manager.commit_checkpoint(f"replace: {path}")
            return f"Replaced in {path}: 1 occurrence."
        except OSError as e:
            if checkpoint_manager:
                checkpoint_manager.discard_pending()
            return f"Error: {e}"

    @tool
    def list_directory(
        path: Annotated[str, "Chemin du dossier à lister"] = ".",
        show_hidden: Annotated[bool, "Afficher les fichiers cachés"] = False,
    ) -> str:
        """Liste les fichiers et dossiers d'un répertoire."""
        p = _resolve_path(path, workspace)
        if not p.exists():
            return f"Error: Directory not found: {path}"
        if not p.is_dir():
            return f"Error: Not a directory: {path}"
        try:
            entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            lines = []
            for entry in entries:
                if not show_hidden and entry.name.startswith("."):
                    continue
                icon = "" if entry.is_dir() else ""
                size = ""
                if entry.is_file():
                    try:
                        size = f" ({entry.stat().st_size} bytes)"
                    except OSError:
                        pass
                lines.append(f"{icon} {entry.name}{size}")
            return f"Directory: {path}\n" + "\n".join(lines) if lines else f"Directory {path} is empty."
        except OSError as e:
            return f"Error: {e}"

    @tool
    def glob(
        pattern: Annotated[str, "Pattern glob (ex: **/*.py, src/*.ts)"],
        path: Annotated[str, "Dossier de base"] = ".",
    ) -> str:
        """Trouve des fichiers correspondant à un pattern glob."""
        base = _resolve_path(path, workspace)
        try:
            matches = list(base.glob(pattern))
            if not matches:
                return f"No files matching: {pattern}"
            result = []
            for m in sorted(matches)[:100]:  # Limite à 100 résultats
                rel = m.relative_to(workspace) if m.is_relative_to(workspace) else m
                result.append(str(rel))
            suffix = f"\n... ({len(matches) - 100} more)" if len(matches) > 100 else ""
            return "\n".join(result) + suffix
        except Exception as e:
            return f"Error: {e}"

    @tool
    def search_file_content(
        pattern: Annotated[str, "Texte ou regex à chercher"],
        path: Annotated[str, "Dossier ou fichier à fouiller"] = ".",
        file_pattern: Annotated[str, "Filtre de fichiers (ex: *.py)"] = "*",
    ) -> str:
        """Cherche du texte dans les fichiers (grep-like)."""
        import re
        base = _resolve_path(path, workspace)
        results = []
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"Invalid regex: {e}"
        try:
            if base.is_file():
                files = [base]
            else:
                files = [f for f in base.rglob(file_pattern) if f.is_file()]
            for fp in files[:200]:
                try:
                    lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
                    for i, line in enumerate(lines, 1):
                        if regex.search(line):
                            rel = fp.relative_to(workspace) if fp.is_relative_to(workspace) else fp
                            results.append(f"{rel}:{i}: {line.strip()}")
                except OSError:
                    continue
            if not results:
                return f"No matches for: {pattern}"
            return "\n".join(results[:500])
        except Exception as e:
            return f"Error: {e}"

    @tool
    def delete_file(
        path: Annotated[str, "Chemin du fichier ou dossier à supprimer"],
        recursive: Annotated[bool, "Supprimer récursivement (dossiers)"] = False,
    ) -> str:
        """Supprime un fichier ou un dossier."""
        p = _resolve_path(path, workspace)
        if not _is_safe_path(p, workspace):
            return f"Error: Path outside workspace: {path}"
        if not p.exists():
            return f"Error: Not found: {path}"
        if confirm_fn:
            if not confirm_fn("delete_file", f"DELETE: {path}", "This action cannot be undone."):
                return "Aborted by user."
        try:
            if p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                else:
                    p.rmdir()
            else:
                p.unlink()
            return f"Deleted: {path}"
        except OSError as e:
            return f"Error: {e}"

    @tool
    def create_directory(
        path: Annotated[str, "Chemin du dossier à créer"],
    ) -> str:
        """Crée un répertoire (et ses parents si nécessaire)."""
        p = _resolve_path(path, workspace)
        if not _is_safe_path(p, workspace):
            return f"✗ Error: Path outside workspace: {path}"
        
        existed_before = p.exists()
        
        try:
            p.mkdir(parents=True, exist_ok=True)
            
            # Verify creation
            if p.exists() and p.is_dir():
                if existed_before:
                    return f"✓ Directory already exists: {path}"
                else:
                    return f"✓ Directory created: {path}"
            else:
                return f"✗ Error: Directory creation reported success but path does not exist: {path}"
        except OSError as e:
            return f"✗ Error creating directory: {e}"

    @tool
    def read_many_files(
        paths: Annotated[list[str], "Liste de chemins de fichiers ou dossiers"],
    ) -> str:
        """Lit plusieurs fichiers ou un dossier entier."""
        results = []
        for path in paths:
            p = _resolve_path(path, workspace)
            if p.is_dir():
                for fp in sorted(p.rglob("*"))[:50]:
                    if fp.is_file() and not any(part.startswith(".") for part in fp.parts):
                        try:
                            content = fp.read_text(encoding="utf-8", errors="replace")
                            rel = fp.relative_to(workspace) if fp.is_relative_to(workspace) else fp
                            results.append(f"\n=== {rel} ===\n{content}")
                        except OSError:
                            continue
            elif p.is_file():
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                    results.append(f"\n=== {path} ===\n{content}")
                except OSError as e:
                    results.append(f"\n=== {path} ===\nError: {e}")
            else:
                results.append(f"\n=== {path} ===\nError: Not found")
        return "".join(results) if results else "No files found."

    return [
        read_file,
        write_file,
        replace,
        list_directory,
        glob,
        search_file_content,
        delete_file,
        create_directory,
        read_many_files,
    ]
