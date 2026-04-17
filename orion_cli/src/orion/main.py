"""Point d'entrée principal d'Orion CLI."""

import sys
from pathlib import Path
from typing import Optional

import typer

from orion.agent import OrionAgent
from orion.config.settings import Settings
from orion.mcp.client import MCPClient
from orion.memory.manager import MemoryManager
from orion.session.manager import SessionManager
from orion.session.checkpoint import CheckpointManager
from orion.ui import renderer
from orion.ui.theme import set_theme

app = typer.Typer(
    name="orion",
    help="Orion CLI — Agent IA local propulsé par Ollama (clone de Gemini CLI)",
    invoke_without_command=True,
    no_args_is_help=False,
)


def _bootstrap(
    workspace: Path,
    model: Optional[str] = None,
    theme: Optional[str] = None,
    vim: bool = False,
    auto_accept: bool = False,
) -> tuple[Settings, MemoryManager, SessionManager, OrionAgent, CheckpointManager | None, MCPClient | None]:
    """Initialise tous les composants Orion."""
    settings = Settings(workspace=workspace)

    # Surcharges CLI
    if model:
        settings.set("model", model, scope="global")
    if theme:
        settings.set("theme", theme, scope="global")
    if vim:
        settings.set("vim_mode", True, scope="global")
    if auto_accept:
        settings.set("auto_accept_edits", True, scope="global")

    # Thème
    set_theme(settings.get("theme", "dark"))

    # Composants core
    memory_manager = MemoryManager(workspace=workspace)
    session_manager = SessionManager()

    # Checkpointing (optionnel)
    checkpoint_manager = None
    if settings.get("checkpointing", False):
        checkpoint_manager = CheckpointManager(workspace=workspace)

    # MCP client (optionnel)
    mcp_client = None
    mcp_config = settings.get("mcp_servers", {})
    if mcp_config:
        mcp_client = MCPClient()
        mcp_client.load_from_settings(mcp_config)
        # Connexion en arrière-plan (non-bloquant)
        try:
            results = mcp_client.connect_all()
            for name, msg in results.items():
                renderer.print_muted(f"MCP {name}: {msg}")
        except Exception:
            pass

    agent = OrionAgent(
        settings=settings,
        workspace=workspace,
        memory_manager=memory_manager,
        session_manager=session_manager,
        mcp_client=mcp_client,
        checkpoint_manager=checkpoint_manager,
    )

    return settings, memory_manager, session_manager, agent, checkpoint_manager, mcp_client


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    workspace: Optional[Path] = typer.Option(
        None, "--workspace", "-w", help="Dossier de travail (défaut: répertoire courant)"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Modèle Ollama à utiliser (ex: qwen2.5-coder:14b)"
    ),
    theme: Optional[str] = typer.Option(
        None, "--theme", help="Thème visuel (dark, light, ansi)"
    ),
    vim: bool = typer.Option(False, "--vim", help="Activer le mode vim"),
    auto_accept: bool = typer.Option(
        False, "--auto-accept", "-y", help="Accepter automatiquement les modifications de fichiers"
    ),
    version: bool = typer.Option(False, "--version", "-v", help="Affiche la version"),
):
    """Lance Orion CLI en mode interactif."""
    if version:
        typer.echo("Orion CLI v0.1.0")
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    ws = (workspace or Path.cwd()).resolve()
    settings, memory_manager, session_manager, agent, checkpoint_manager, mcp_client = _bootstrap(
        workspace=ws,
        model=model,
        theme=theme,
        vim=vim,
        auto_accept=auto_accept,
    )

    # Charge les custom commands
    from orion.commands.builtins import build_registry
    from orion.commands.custom import register_custom_commands

    # Lance le REPL interactif
    from orion.repl import OrionREPL
    repl = OrionREPL(
        settings=settings,
        workspace=ws,
        agent=agent,
        session_manager=session_manager,
        memory_manager=memory_manager,
        checkpoint_manager=checkpoint_manager,
        mcp_client=mcp_client,
    )
    repl.run()


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="Message à envoyer (mode non-interactif)"),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    output_json: bool = typer.Option(False, "--json", help="Output en JSON"),
):
    """Envoie un prompt unique et retourne la réponse (mode headless/non-interactif)."""
    ws = (workspace or Path.cwd()).resolve()
    settings, memory_manager, session_manager, agent, _, _ = _bootstrap(workspace=ws, model=model)

    response = agent.chat(prompt)

    if output_json:
        import json
        print(json.dumps({"response": response, "model": settings.get("model")}))
    else:
        print(response)


@app.command()
def init(
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Nom du projet"),
):
    """Initialise ORION.md dans le workspace courant."""
    ws = (workspace or Path.cwd()).resolve()
    settings = Settings(workspace=ws)
    set_theme(settings.get("theme", "dark"))
    memory_manager = MemoryManager(workspace=ws)
    result = memory_manager.init_project_memory(name or ws.name)
    renderer.print_success(f"Initialized: {result}")


@app.command()
def run(
    command_file: Path = typer.Argument(..., help="Fichier de commandes à exécuter"),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
):
    """Exécute un fichier de prompts séquentiellement (batch mode)."""
    ws = (workspace or Path.cwd()).resolve()
    settings, memory_manager, session_manager, agent, _, _ = _bootstrap(workspace=ws, model=model)

    if not command_file.exists():
        renderer.print_error(f"File not found: {command_file}")
        raise typer.Exit(1)

    prompts = command_file.read_text(encoding="utf-8").strip().splitlines()
    for i, prompt in enumerate(prompts, 1):
        prompt = prompt.strip()
        if not prompt or prompt.startswith("#"):
            continue
        renderer.print_muted(f"\n[{i}/{len(prompts)}] {prompt}")
        response = agent.chat(prompt)
        renderer.print_assistant(response)


def entry_point():
    """Point d'entrée pour setup.py."""
    app()


if __name__ == "__main__":
    entry_point()
