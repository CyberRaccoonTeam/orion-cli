"""Rendu visuel Rich pour Orion CLI."""

import time

from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .theme import get_console, get_theme_colors


def print_assistant(content: str) -> None:
    """Affiche la réponse de l'assistant avec rendu Markdown."""
    console = get_console()
    colors = get_theme_colors()
    console.print()
    # Afficher le préfixe ORION: en couleur
    console.print(Text("ORION: ", style=f"bold {colors['primary']}"), end="")
    console.print(Markdown(content))
    console.print()


def print_thinking_animated(thinking: str, words_per_second: float = 30) -> None:
    """
    Affiche progressivement la réflexion d'un modèle de raisonnement (deepseek-r1, qwq...).
    Simule une génération en direct mot par mot.
    """
    console = get_console()
    colors = get_theme_colors()
    words = thinking.split()
    if not words:
        return

    delay = 1.0 / max(float(words_per_second), 1)
    think_title = f"[{colors['muted']}]💭 Réflexion[/]"
    buffer = ""

    console.print()
    with Live(
        Panel(Text(""), title=think_title, border_style=colors["muted"]),
        console=console,
        refresh_per_second=20,
        transient=True,
    ) as live:
        for word in words:
            buffer += ("" if not buffer else " ") + word
            live.update(
                Panel(
                    Text(buffer, style=colors["muted"]),
                    title=think_title,
                    border_style=colors["muted"],
                )
            )
            time.sleep(delay)

    # Panneau final permanent (remplace le transient)
    console.print(
        Panel(
            Text(buffer, style=colors["muted"]),
            title=think_title,
            border_style=colors["muted"],
        )
    )
    console.print()


def print_thinking_notice() -> None:
    """Informe que le modèle courant ne produit pas de réflexion visible."""
    colors = get_theme_colors()
    get_console().print(
        f"[{colors['muted']}]ℹ  Ce modèle ne produit pas de réflexion visible. "
        "Pour activer la réflexion, utilisez un modèle de raisonnement "
        "(ex : deepseek-r1, qwq, qwen3).[/]"
    )


def print_assistant_typing(content: str, delay: float = 0.010) -> None:
    """
    Affiche la réponse mot par mot avec un effet de frappe.

    Args:
        content: Texte à afficher (support Markdown).
        delay: Délai en secondes entre chaque mot (défaut 10 ms).
    """
    console = get_console()
    colors = get_theme_colors()
    console.print()
    
    # Afficher le préfixe ORION: en couleur
    console.print(Text("ORION: ", style=f"bold {colors['primary']}"), end="")
    
    words = content.split()
    if not words:
        console.print()
        return

    buffer = ""
    with Live(Markdown(""), console=console, refresh_per_second=30, transient=False) as live:
        for i, word in enumerate(words):
            buffer += ("" if i == 0 else " ") + word
            live.update(Markdown(buffer))
            time.sleep(delay)

    console.print()


def print_user_echo(content: str) -> None:
    """Echo visuel du message utilisateur."""
    colors = get_theme_colors()
    console = get_console()
    console.print(f"[{colors['user_color']}]> {content}[/]")


def print_tool_call(tool_name: str, tool_input: dict) -> None:
    """Affiche un appel d'outil."""
    colors = get_theme_colors()
    console = get_console()
    input_str = str(tool_input)
    if len(input_str) > 120:
        input_str = input_str[:120] + "..."
    console.print(
        f"[{colors['tool_color']}]  Tool:[/] [{colors['primary']}]{tool_name}[/] "
        f"[{colors['muted']}]{input_str}[/]"
    )


def print_tool_result(result: str, success: bool = True) -> None:
    """Affiche le résultat d'un outil."""
    colors = get_theme_colors()
    console = get_console()
    color = colors["success"] if success else colors["error"]
    icon = "" if success else ""
    if len(result) > 200:
        result = result[:200] + "..."
    console.print(f"[{color}]  {icon} {result}[/]")


def print_error(message: str) -> None:
    colors = get_theme_colors()
    console = get_console()
    console.print(f"[{colors['error']}]Error: {message}[/]")


def print_warning(message: str) -> None:
    colors = get_theme_colors()
    console = get_console()
    console.print(f"[{colors['warning']}]Warning: {message}[/]")


def print_success(message: str) -> None:
    colors = get_theme_colors()
    console = get_console()
    console.print(f"[{colors['success']}]{message}[/]")


def print_info(message: str) -> None:
    colors = get_theme_colors()
    console = get_console()
    console.print(f"[{colors['primary']}]{message}[/]")


def print_muted(message: str) -> None:
    colors = get_theme_colors()
    console = get_console()
    console.print(f"[{colors['muted']}]{message}[/]")


def print_separator() -> None:
    console = get_console()
    console.print(Rule(style="bright_black"))


def print_banner() -> None:
    """Affiche le banner de démarrage Orion CLI."""
    console = get_console()
    colors = get_theme_colors()
    banner = f"""[{colors['primary']}]
  ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
 ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║
 ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║
 ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║
 ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║
  ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/]
[{colors['muted']}]  CLI Agent — Local AI powered by Ollama[/]
"""
    console.print(banner)


def confirm_tool_action(tool_name: str, description: str, details: str) -> bool:
    """Demande confirmation avant d'exécuter un outil dangereux."""
    colors = get_theme_colors()
    console = get_console()
    console.print(
        Panel(
            f"[{colors['warning']}]{description}[/]\n[{colors['muted']}]{details}[/]",
            title=f"[{colors['tool_color']}]Tool: {tool_name}[/]",
            border_style=colors["warning"],
        )
    )
    console.print(f"[{colors['primary']}]Proceed? [y/N][/] ", end="")
    try:
        answer = input().strip().lower()
        return answer in ("y", "yes", "o", "oui")
    except (EOFError, KeyboardInterrupt):
        return False


def print_stats_table(stats: dict) -> None:
    """Affiche les statistiques de session."""
    table = Table(title="Session Stats", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    for key, value in stats.items():
        table.add_row(str(key), str(value))
    get_console().print(table)
