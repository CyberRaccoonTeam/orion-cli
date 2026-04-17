"""Registry des slash commands Orion CLI."""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Command:
    name: str
    aliases: list[str]
    description: str
    usage: str
    handler: Callable


class CommandRegistry:
    """Registre central des slash commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        self._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self._commands[alias] = cmd

    def get(self, name: str) -> Optional[Command]:
        return self._commands.get(name.lstrip("/"))

    def dispatch(self, raw_input: str, context: dict) -> Optional[str]:
        """
        Dispatch une slash command.
        raw_input: ex "/chat save mytag" ou "/help"
        context: dict avec agent, settings, session_manager, memory_manager, etc.
        Retourne None si la commande n'existe pas.
        """
        parts = raw_input.strip().split(maxsplit=1)
        cmd_name = parts[0].lstrip("/").lower()
        args = parts[1] if len(parts) > 1 else ""
        cmd = self._commands.get(cmd_name)
        if cmd is None:
            return None
        return cmd.handler(args, context)

    def all_commands(self) -> list[Command]:
        seen = set()
        result = []
        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                result.append(cmd)
        return sorted(result, key=lambda c: c.name)
