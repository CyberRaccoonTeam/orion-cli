"""Outil d'exécution de commandes shell — équivalent run_shell_command."""

import os
import subprocess
import threading
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


def make_shell_tool(workspace: Path, shell: str = "bash", timeout: int = 30, confirm_fn=None):
    """Crée le tool shell lié au workspace."""

    @tool
    def run_shell_command(
        command: Annotated[str, "Commande shell à exécuter"],
        working_dir: Annotated[str, "Dossier d'exécution (défaut: workspace)"] = "",
    ) -> str:
        """Exécute une commande shell dans le workspace.
        Retourne stdout + stderr. Timeout: 30s.
        """
        cwd = Path(working_dir).resolve() if working_dir else workspace

        # Confirmation pour commandes destructrices
        dangerous_keywords = ["rm ", "rmdir", "dd ", "mkfs", "format", "shutdown", "reboot", "> /dev"]
        is_dangerous = any(kw in command for kw in dangerous_keywords)

        if confirm_fn and is_dangerous:
            if not confirm_fn("run_shell_command", f"Execute shell command:", command):
                return "Aborted by user."

        env = os.environ.copy()
        env["ORION_CLI"] = "1"

        try:
            result = subprocess.run(
                command,
                shell=True,
                executable=shell,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=timeout,
                env=env,
            )
            output = []
            
            # Build clear status message
            if result.returncode == 0:
                status_prefix = "✓ Command succeeded"
            else:
                status_prefix = f"✗ Command failed (exit code {result.returncode})"
            
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout.rstrip()}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr.rstrip()}")
            
            # Always show exit status clearly at the start
            if output:
                return f"{status_prefix}\n\n" + "\n".join(output)
            else:
                return f"{status_prefix}\n(No output produced)"
                
        except subprocess.TimeoutExpired:
            return f"✗ Error: Command timed out after {timeout}s"
        except Exception as e:
            return f"✗ Error executing command: {e}"

    return run_shell_command
