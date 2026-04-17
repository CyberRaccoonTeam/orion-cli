"""Custom slash commands via fichiers .toml — équivalent Gemini CLI custom commands.

Structure d'un fichier de commande (.toml) :
    ~/.config/orion/commands/git/commit.toml  → /git:commit
    .orion/commands/review.toml               → /review

Format du .toml :
    description = "Description courte de la commande"
    prompt = "Ton prompt template. Utilise {{input}} pour l'argument utilisateur."
    # Optionnel :
    args_description = "Description de l'argument attendu"
"""

import sys
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib


def _toml_path_to_command_name(base_dir: Path, toml_file: Path) -> str:
    """Convertit un chemin de fichier en nom de commande."""
    rel = toml_file.relative_to(base_dir)
    parts = list(rel.parts)
    # Enlève l'extension .toml du dernier
    parts[-1] = parts[-1].removesuffix(".toml")
    # Sous-dossiers séparés par ':'
    return ":".join(parts)


def load_custom_commands(
    global_dir: Path,
    local_dir: Optional[Path] = None,
) -> list[dict]:
    """
    Charge toutes les custom commands depuis les dossiers configurés.

    Retourne une liste de dicts:
    {
        "name": "git:commit",
        "description": "...",
        "prompt": "...",
        "args_description": "...",
        "source": "global" | "local",
        "file": Path,
    }
    """
    commands = []

    def scan_dir(base: Path, source: str) -> None:
        if not base.exists():
            return
        for toml_file in sorted(base.rglob("*.toml")):
            try:
                with open(toml_file, "rb") as f:
                    data = tomllib.load(f)
                name = _toml_path_to_command_name(base, toml_file)
                commands.append({
                    "name": name,
                    "description": data.get("description", f"Custom command: {name}"),
                    "prompt": data.get("prompt", ""),
                    "args_description": data.get("args_description", "Optional argument"),
                    "source": source,
                    "file": toml_file,
                })
            except Exception:
                continue

    scan_dir(global_dir, "global")
    if local_dir:
        scan_dir(local_dir, "local")

    return commands


def register_custom_commands(registry, global_dir: Path, local_dir: Optional[Path] = None) -> int:
    """
    Charge et enregistre toutes les custom commands dans le registry.
    Retourne le nombre de commandes enregistrées.
    """
    from .registry import Command

    custom_cmds = load_custom_commands(global_dir, local_dir)

    for cmd_def in custom_cmds:
        # Capture par valeur
        prompt_template = cmd_def["prompt"]
        cmd_name = cmd_def["name"]

        def make_handler(template: str, name: str):
            def handler(args: str, ctx: dict) -> str:
                # Remplace {{input}} par les args de l'utilisateur
                prompt = template.replace("{{input}}", args).replace("{{ input }}", args)
                if not prompt.strip():
                    return f"Error: Command /{name} has no prompt template configured."
                # Envoie au modèle
                agent = ctx.get("agent")
                if agent:
                    return agent.chat(prompt)
                return f"Error: No agent available for command /{name}"
            return handler

        cmd = Command(
            name=cmd_name,
            aliases=[],
            description=cmd_def["description"],
            usage=f"/{cmd_name} [{cmd_def['args_description']}]",
            handler=make_handler(prompt_template, cmd_name),
        )
        registry.register(cmd)

    return len(custom_cmds)


def create_example_command(target_dir: Path, name: str = "example") -> Path:
    """Crée un exemple de fichier de commande .toml."""
    parts = name.split(":")
    toml_path = target_dir
    for part in parts[:-1]:
        toml_path = toml_path / part
    toml_path = toml_path / f"{parts[-1]}.toml"
    toml_path.parent.mkdir(parents=True, exist_ok=True)

    content = '''description = "Exemple de commande personnalisée"
args_description = "Texte optionnel à inclure"

prompt = """
Tu es un assistant expert. Réponds de manière concise et précise.

{{input}}
"""
'''
    toml_path.write_text(content)
    return toml_path
