"""REPL interactif Orion CLI — propulsé par prompt_toolkit."""

import re
import sys
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from orion.agent import OrionAgent, is_reasoning_model
from orion.commands.builtins import build_registry
from orion.commands.custom import register_custom_commands
from orion.commands.registry import CommandRegistry
from orion.config.settings import Settings
from orion.memory.manager import MemoryManager
from orion.mcp.client import MCPClient
from orion.session.checkpoint import CheckpointManager
from orion.session.manager import SessionManager
from orion.ui import renderer
from orion.ui.theme import get_theme_colors


HISTORY_FILE = Path.home() / ".config" / "orion" / "history"


class OrionREPL:
    """
    REPL interactif d'Orion CLI.

    Fonctionnalités :
    - Slash commands (/help, /quit, /settings, ...)
    - @ pour injection de fichiers (@path)
    - ! pour commandes shell (!cmd)
    - ! seul pour toggle shell mode
    - Vim mode, historique persistant, autocomplétion
    - Streaming token-par-token
    - Checkpointing + /restore
    - Custom commands via .toml
    - MCP server tools
    """

    def __init__(
        self,
        settings: Settings,
        workspace: Path,
        agent: OrionAgent,
        session_manager: SessionManager,
        memory_manager: MemoryManager,
        checkpoint_manager: Optional[CheckpointManager] = None,
        mcp_client: Optional[MCPClient] = None,
    ):
        self.settings = settings
        self.workspace = workspace
        self.agent = agent
        self.session_manager = session_manager
        self.memory_manager = memory_manager
        self.checkpoint_manager = checkpoint_manager
        self.mcp_client = mcp_client
        self.registry: CommandRegistry = build_registry()
        self._shell_mode = False
        self._last_response = ""
        self._streaming_mode = settings.get("streaming_mode", False)
        self._repl_state = {"vim_mode": settings.get("vim_mode", False)}

        # Charge les custom commands
        global_cmds_dir = Path.home() / ".config" / "orion" / "commands"
        local_cmds_dir = workspace / ".orion" / "commands"
        n_custom = register_custom_commands(self.registry, global_cmds_dir, local_cmds_dir)
        if n_custom:
            renderer.print_muted(f"Loaded {n_custom} custom command(s).")

        self._thinking_notice_shown = False  # Affiché une seule fois si modèle non-reasoning
        self._context = self._build_context()

    def _build_context(self) -> dict:
        """Construit le contexte partagé entre toutes les commandes."""
        return {
            "agent": self.agent,
            "settings": self.settings,
            "session_manager": self.session_manager,
            "memory_manager": self.memory_manager,
            "workspace": self.workspace,
            "registry": self.registry,
            "repl_state": self._repl_state,
            "last_response": self._last_response,
            "checkpoint_manager": self.checkpoint_manager,
            "mcp_client": self.mcp_client,
            "extra_dirs": [],
        }

    def _build_prompt_session(self) -> PromptSession:
        """Construit la session prompt_toolkit."""
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = FileHistory(str(HISTORY_FILE))

        # Autocomplétion des slash commands
        slash_commands = [f"/{cmd.name}" for cmd in self.registry.all_commands()]
        slash_commands += ["@", "!"]
        completer = WordCompleter(slash_commands, pattern=re.compile(r"[/!@]?\w*"))

        colors = get_theme_colors()

        style = Style.from_dict({
            "prompt": f"bold {colors['prompt_color']}",
            "": colors["assistant_color"],
        })

        bindings = KeyBindings()

        @bindings.add("c-l")
        def _clear(event):
            """Ctrl+L — clear screen."""
            import os
            os.system("clear" if os.name != "nt" else "cls")
            self.session_manager.clear()
            event.app.renderer.reset()

        session = PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
            style=style,
            key_bindings=bindings,
            vi_mode=self._repl_state.get("vim_mode", False),
            mouse_support=False,
            enable_history_search=True,
        )
        return session

    def _get_prompt_text(self) -> HTML:
        """Génère le texte du prompt dynamiquement."""
        colors = get_theme_colors()
        model = self.settings.get("model", "ollama")
        workspace_name = self.workspace.name

        if self._shell_mode:
            return HTML(f'<ansigreen><b>orion !shell</b></ansigreen> <ansiyellow>❯</ansiyellow> ')

        return HTML(
            f'<b><ansiblue>orion</ansiblue></b>'
            f'<ansigray> ({model})</ansigray> '
            f'<ansicyan>❯</ansicyan> '
        )

    def _handle_at_prefix(self, text: str) -> str:
        """Traite @path — injecte le contenu du fichier dans le prompt."""
        path_str = text[1:].strip()
        if not path_str:
            return text

        p = Path(path_str).expanduser()
        if not p.is_absolute():
            p = self.workspace / p

        if not p.exists():
            renderer.print_error(f"Path not found: {path_str}")
            return ""

        if p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            renderer.print_muted(f"Injected: {path_str} ({len(content.splitlines())} lines)")
            return f"Here is the content of `{path_str}`:\n\n```\n{content}\n```"
        elif p.is_dir():
            files_content = []
            for fp in sorted(p.rglob("*"))[:30]:
                if fp.is_file() and not any(part.startswith(".") for part in fp.parts):
                    try:
                        fc = fp.read_text(encoding="utf-8", errors="replace")
                        rel = fp.relative_to(self.workspace) if fp.is_relative_to(self.workspace) else fp
                        files_content.append(f"=== {rel} ===\n{fc}")
                    except OSError:
                        continue
            renderer.print_muted(f"Injected directory: {path_str} ({len(files_content)} files)")
            return "\n\n".join(files_content)
        return text

    def _handle_shell_command(self, command: str) -> None:
        """Exécute une commande shell directement (!cmd)."""
        import subprocess
        renderer.print_muted(f"$ {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                executable=self.settings.get("shell", "bash"),
                cwd=str(self.workspace),
                text=True,
            )
        except Exception as e:
            renderer.print_error(str(e))

    def _process_input(self, user_input: str) -> bool:
        """
        Traite l'input utilisateur.
        Retourne True si la boucle doit continuer, False pour quitter.
        """
        text = user_input.strip()
        if not text:
            return True

        # ─── Slash commands ─────────────────────────────
        if text.startswith("/"):
            self._context["last_response"] = self._last_response
            result = self.registry.dispatch(text, self._context)
            if result is None:
                renderer.print_error(f"Unknown command: {text.split()[0]}. Type /help for commands.")
            elif result:
                renderer.print_assistant(result)
            return True

        # ─── Shell toggle (!!) ─────────────────────────
        if text == "!":
            self._shell_mode = not self._shell_mode
            status = "enabled" if self._shell_mode else "disabled"
            renderer.print_muted(f"Shell mode {status}.")
            return True

        # ─── Shell command (!cmd) ──────────────────────
        if text.startswith("!"):
            self._handle_shell_command(text[1:].strip())
            return True

        # ─── File injection (@path) ────────────────────
        if text.startswith("@"):
            injected = self._handle_at_prefix(text)
            if not injected:
                return True
            text = injected

        # ─── Shell mode passthrough ────────────────────
        if self._shell_mode:
            self._handle_shell_command(text)
            return True

        # ─── Agent chat ────────────────────────────────
        renderer.print_muted("")  # Ligne vide

        # /streaming active le mode sans outils (token-par-token direct)
        streaming = self._repl_state.get("streaming_mode", self._streaming_mode)
        if streaming:
            response = self._stream_response(text)
        else:
            # Mode agent complet : spinner + tool calls en temps réel + typing
            response = self._run_agent_live(text)

        self._last_response = response
        self._context["last_response"] = response
        return True

    def _run_agent_live(self, user_input: str) -> str:
        """
        Exécute l'agent avec :
        - Spinner "thinking" pendant le traitement
        - Affichage des tool calls en temps réel
        - Animation live de la réflexion (<think>) si le modèle en produit
        - Animation de frappe pour la réponse finale
        """
        console = renderer.get_console()
        colors = get_theme_colors()
        typing_animation = self.settings.get("typing_animation", True)
        typing_delay = float(self.settings.get("typing_delay", 0.010))
        show_thinking = self.settings.get("show_thinking", True)
        thinking_wps = float(self.settings.get("thinking_words_per_second", 30))
        final_response = ""
        pending_thinking = ""

        spinner_style = colors["primary"]
        status_text = f"[{colors['muted']}]Orion réfléchit...[/]"

        with console.status(status_text, spinner="dots", spinner_style=spinner_style):
            for event in self.agent.stream_events(user_input):
                etype = event["type"]

                if etype == "thinking":
                    pending_thinking = event["content"]

                elif etype == "tool_call":
                    renderer.print_tool_call(event["name"], event["args"])

                elif etype == "tool_result":
                    renderer.print_tool_result(event["result"])

                elif etype == "response":
                    final_response = event["content"]

                elif etype == "error":
                    renderer.print_error(event["content"])
                    final_response = event["content"]

        # Affichage de la réflexion (animation mot par mot après le spinner)
        if show_thinking and pending_thinking:
            renderer.print_thinking_animated(pending_thinking, words_per_second=thinking_wps)
        elif show_thinking and not pending_thinking and not self._thinking_notice_shown:
            model = self.settings.get("model", "")
            if not is_reasoning_model(model):
                renderer.print_thinking_notice()
                self._thinking_notice_shown = True

        # Réponse finale avec animation typing (ou affichage normal)
        if final_response and final_response != "(No response)":
            if typing_animation:
                renderer.print_assistant_typing(final_response, delay=typing_delay)
            else:
                renderer.print_assistant(final_response)
        elif not final_response or final_response == "(No response)":
            renderer.print_muted("(Aucune réponse)")

        return final_response

    def _stream_response(self, user_input: str) -> str:
        """
        Affiche la réponse token par token via Rich Live (mode sans outils).
        Détecte et affiche la réflexion <think> en temps réel si présente.
        """
        from rich.live import Live
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.text import Text

        console = renderer.get_console()
        colors = get_theme_colors()
        show_thinking = self.settings.get("show_thinking", True)

        think_title = f"[{colors['muted']}]💭 Réflexion[/]"
        thinking_buffer = ""
        response_buffer = ""

        # Print the ORION: prefix before streaming starts
        console.print()
        console.print(Text("ORION: ", style=f"bold {colors['primary']}"), end="")

        # Un seul contexte Live qui change de contenu selon la phase
        with Live(Text(""), console=console, refresh_per_second=20) as live:
            def on_thinking(token: str) -> None:
                nonlocal thinking_buffer
                thinking_buffer += token
                if show_thinking:
                    live.update(
                        Panel(
                            Text(thinking_buffer, style=colors["muted"]),
                            title=think_title,
                            border_style=colors["muted"],
                        )
                    )

            def on_token(token: str) -> None:
                nonlocal response_buffer
                response_buffer += token
                live.update(Markdown(response_buffer))

            response = self.agent.stream_chat(
                user_input, on_token=on_token, on_thinking=on_thinking
            )

        console.print()
        return response

    def run(self) -> None:
        """Lance la boucle REPL principale."""
        renderer.print_banner()

        # Affiche le contexte mémoire si disponible
        memory_ctx = self.memory_manager.load_context()
        if memory_ctx:
            renderer.print_muted(f"Memory loaded ({len(memory_ctx)} chars). Type /memory to view.")

        renderer.print_muted(f"Workspace: {self.workspace}")
        renderer.print_muted(f"Model: {self.settings.get('model')}  |  Type /help for commands\n")

        session = self._build_prompt_session()

        while True:
            try:
                user_input = session.prompt(
                    self._get_prompt_text,
                    vi_mode=self._repl_state.get("vim_mode", False),
                )
                if not self._process_input(user_input):
                    break

            except KeyboardInterrupt:
                renderer.print_muted("\nUse /quit or Ctrl+C twice to exit.")
                try:
                    session.prompt(self._get_prompt_text, vi_mode=False)
                except KeyboardInterrupt:
                    renderer.print_muted("Goodbye!")
                    sys.exit(0)

            except EOFError:
                renderer.print_muted("Goodbye!")
                break
