"""Implémentation de toutes les slash commands intégrées."""

import sys
from pathlib import Path

from orion.config.providers import LLMProvider, test_connection
from orion.ui import renderer
from .registry import Command, CommandRegistry


# ─── /help ──────────────────────────────────────────────────────────────────

def cmd_help(args: str, ctx: dict) -> str:
    registry: CommandRegistry = ctx["registry"]
    lines = [
        "**Orion CLI — Commands**\n",
        "| Command | Aliases | Description |",
        "|---------|---------|-------------|",
    ]
    for cmd in registry.all_commands():
        aliases = ", ".join(f"`/{a}`" for a in cmd.aliases) if cmd.aliases else "-"
        lines.append(f"| `/{cmd.name}` | {aliases} | {cmd.description} |")
    lines += [
        "",
        "**Input shortcuts:**",
        "- `@<path>` — Inject file/directory content into prompt",
        "- `!<cmd>`  — Execute shell command directly",
        "- `!`       — Toggle shell mode",
        "",
        "**Keyboard shortcuts:**",
        "- `Ctrl+C`  — Cancel / exit",
        "- `Ctrl+L`  — Clear screen",
        "- `Ctrl+R`  — Search history",
    ]
    return "\n".join(lines)


# ─── /quit ──────────────────────────────────────────────────────────────────

def cmd_quit(args: str, ctx: dict) -> str:
    renderer.print_muted("Goodbye!")
    sys.exit(0)


# ─── /clear ─────────────────────────────────────────────────────────────────

def cmd_clear(args: str, ctx: dict) -> str:
    import os
    os.system("clear" if os.name != "nt" else "cls")
    ctx["session_manager"].clear()
    return ""


# ─── /settings ──────────────────────────────────────────────────────────────

def cmd_settings(args: str, ctx: dict) -> str:
    settings = ctx["settings"]
    parts = args.strip().split(maxsplit=2)

    if not parts or parts[0] == "":
        # Affiche tous les settings
        lines = ["**Current Settings:**\n"]
        for k, v in sorted(settings.all().items()):
            # Mask API keys in display
            if "api_key" in k.lower() and v:
                display_val = "***" + str(v)[-4:] if len(str(v)) > 4 else "***"
            else:
                display_val = v
            lines.append(f"- `{k}` = `{display_val}`")
        return "\n".join(lines)

    if parts[0] == "set" and len(parts) >= 3:
        key, value = parts[1], parts[2]
        
        # Redirect provider management to dedicated command
        if key == "llm_provider":
            return f"⚠️  Use `/provider {value}` instead to change the LLM provider.\nThe `/provider` command provides interactive configuration and connection testing."
        
        # Redirect model management to dedicated command
        if key == "model":
            return f"⚠️  Use `/provider` to change the model.\nThe `/provider` command will prompt you for the model name when configuring a provider."
        
        # Auto-correct LM Studio URL to include /v1
        if key == "lmstudio_base_url" and not value.endswith("/v1"):
            value = value.rstrip("/") + "/v1"
            renderer.get_console().print(f"[dim]→ Auto-corrected to: {value}[/]")
        
        # Conversion de type basique
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        settings.set(key, value)
        
        # Force agent LLM reset for critical config changes
        llm_config_keys = [
            "lmstudio_base_url", "lmstudio_api_key",
            "ollama_base_url",
            "openai_api_key", "anthropic_api_key",
            "model_temperature", "model_context_length"
        ]
        if key in llm_config_keys and "agent" in ctx:
            ctx["agent"]._llm = None
            return f"Setting updated: `{key}` = `{value}`\n[dim]→ Agent LLM will be reinitialized on next message[/]"
        
        return f"Setting updated: `{key}` = `{value}`"

    if parts[0] == "get" and len(parts) >= 2:
        key = parts[1]
        value = settings.get(key, 'not set')
        # Mask API keys in display
        if "api_key" in key.lower() and value != 'not set':
            display_val = "***" + str(value)[-4:] if len(str(value)) > 4 else "***"
        else:
            display_val = value
        return f"`{key}` = `{display_val}`"
    
    # Redirect test-provider to dedicated command
    if parts[0] == "test-provider":
        return "⚠️  Use `/provider test` instead to test the current provider connection."

    return (
        "Usage:\n"
        "  `/settings` - Show all settings\n"
        "  `/settings get <key>` - Get a setting value\n"
        "  `/settings set <key> <value>` - Set a setting\n"
        "\nNote: Use `/provider` to manage LLM providers and models."
    )


# ─── /memory ────────────────────────────────────────────────────────────────

def cmd_memory(args: str, ctx: dict) -> str:
    memory = ctx["memory_manager"]
    parts = args.strip().split(maxsplit=1)

    if not parts or parts[0] == "show":
        return memory.show()

    if parts[0] == "add" and len(parts) >= 2:
        memory.add_memory(parts[1])
        return f"Memory added: {parts[1][:80]}"

    if parts[0] == "refresh":
        context = memory.load_context()
        ctx["agent"].reset()
        return f"Memory refreshed. Context length: {len(context)} chars."

    return "Usage: `/memory` | `/memory show` | `/memory add <text>` | `/memory refresh`"


# ─── /chat ──────────────────────────────────────────────────────────────────

def cmd_chat(args: str, ctx: dict) -> str:
    session = ctx["session_manager"]
    parts = args.strip().split(maxsplit=1)

    if not parts or parts[0] == "":
        return "Usage: `/chat save <tag>` | `/chat resume <tag>` | `/chat list` | `/chat delete <tag>`"

    subcmd = parts[0]
    tag = parts[1].strip() if len(parts) > 1 else ""

    if subcmd == "save":
        return session.save(tag)
    if subcmd == "resume":
        result = session.resume(tag)
        ctx["agent"].reset()
        return result
    if subcmd == "list":
        return session.list_sessions()
    if subcmd == "delete":
        return session.delete(tag)

    return "Usage: `/chat save <tag>` | `/chat resume <tag>` | `/chat list` | `/chat delete <tag>`"


# ─── /stats ─────────────────────────────────────────────────────────────────

def cmd_stats(args: str, ctx: dict) -> str:
    session = ctx["session_manager"]
    stats = session.get_stats()
    model_info = ctx["agent"].get_model_info()
    stats["Model"] = model_info.get("model", "unknown")
    renderer.print_stats_table(stats)
    return ""


# ─── /theme ─────────────────────────────────────────────────────────────────

def cmd_theme(args: str, ctx: dict) -> str:
    from orion.ui.theme import set_theme, available_themes, get_theme_name
    themes = available_themes()
    theme_name = args.strip().lower()

    if not theme_name:
        current = get_theme_name()
        return f"Current theme: `{current}`\nAvailable: {', '.join(f'`{t}`' for t in themes)}"

    if set_theme(theme_name):
        ctx["settings"].set("theme", theme_name)
        return f"Theme set to: `{theme_name}`"
    return f"Unknown theme: `{theme_name}`. Available: {', '.join(themes)}"


# ─── /directory ─────────────────────────────────────────────────────────────

def cmd_directory(args: str, ctx: dict) -> str:
    parts = args.strip().split(maxsplit=1)
    extra_dirs: list[Path] = ctx.setdefault("extra_dirs", [])

    if not parts or parts[0] == "list":
        if not extra_dirs:
            return f"Workspace: `{ctx['workspace']}`\nNo extra directories added."
        lines = [f"Workspace: `{ctx['workspace']}`", "Extra directories:"]
        for d in extra_dirs:
            lines.append(f"  - {d}")
        return "\n".join(lines)

    if parts[0] == "add" and len(parts) > 1:
        new_dir = Path(parts[1]).expanduser().resolve()
        if not new_dir.exists():
            return f"Error: Directory not found: {new_dir}"
        if not new_dir.is_dir():
            return f"Error: Not a directory: {new_dir}"
        extra_dirs.append(new_dir)
        return f"Directory added: `{new_dir}`"

    return "Usage: `/directory` | `/directory add <path>` | `/directory list`"


# ─── /tools ─────────────────────────────────────────────────────────────────

def cmd_tools(args: str, ctx: dict) -> str:
    tools = ctx["agent"].list_tools()
    lines = [f"**Available tools ({len(tools)}):**\n"]
    for name, desc in tools:
        lines.append(f"- `{name}`: {desc}")
    return "\n".join(lines)


# ─── /about ─────────────────────────────────────────────────────────────────

def cmd_about(args: str, ctx: dict) -> str:
    model_info = ctx["agent"].get_model_info()
    return (
        "**Orion CLI v0.1.0**\n"
        "Clone local de Gemini CLI — propulsé par Ollama\n\n"
        f"Model: `{model_info.get('model', 'unknown')}`\n"
        f"Workspace: `{ctx['workspace']}`\n"
        "GitHub: https://github.com/orion-cli/orion"
    )


# ─── /init ──────────────────────────────────────────────────────────────────

def cmd_init(args: str, ctx: dict) -> str:
    memory = ctx["memory_manager"]
    project_name = args.strip() or ctx["workspace"].name
    result = memory.init_project_memory(project_name)
    return f"Initialized ORION.md: `{result}`"


# ─── /compress ──────────────────────────────────────────────────────────────

def cmd_compress(args: str, ctx: dict) -> str:
    session = ctx["session_manager"]
    agent = ctx["agent"]
    history = session.get_history()
    if not history:
        return "No conversation to compress."
    # Demande un résumé au modèle
    summary_prompt = "Summarize this conversation history in a concise paragraph, preserving key context and decisions:\n\n"
    for msg in history:
        summary_prompt += f"{msg['role'].upper()}: {msg['content'][:200]}\n"
    summary = agent.chat(summary_prompt)
    session.compress(summary)
    return f"Context compressed. Summary stored."


# ─── /copy ──────────────────────────────────────────────────────────────────

def cmd_copy(args: str, ctx: dict) -> str:
    last_response = ctx.get("last_response", "")
    if not last_response:
        return "Nothing to copy."
    try:
        import pyperclip
        pyperclip.copy(last_response)
        return f"Copied to clipboard ({len(last_response)} chars)."
    except ImportError:
        return "Error: pyperclip not installed. Run: pip install pyperclip"
    except Exception as e:
        return f"Copy failed: {e}"


# ─── /mcp ───────────────────────────────────────────────────────────────────

def cmd_mcp(args: str, ctx: dict) -> str:
    mcp_client = ctx.get("mcp_client")
    if mcp_client:
        parts = args.strip().split()
        if parts and parts[0] == "connect" and len(parts) > 1:
            ok, msg = mcp_client.connect(parts[1])
            return msg
        if parts and parts[0] == "disconnect" and len(parts) > 1:
            mcp_client.disconnect(parts[1])
            return f"Disconnected: {parts[1]}"
        return mcp_client.status_report()

    mcp_servers = ctx["settings"].get("mcp_servers", {})
    if not mcp_servers:
        return (
            "No MCP servers configured.\n"
            "Add in `~/.config/orion/settings.json`:\n"
            "```json\n"
            '{"mcp_servers": {"my-server": {"transport": "stdio", "command": ["node", "server.js"]}}}\n'
            "```"
        )
    lines = [f"**MCP Servers ({len(mcp_servers)}) — not connected:**\n"]
    for name, cfg in mcp_servers.items():
        transport_info = cfg.get("url", " ".join(cfg.get("command", ["?"])))
        lines.append(f"- `{name}`: {transport_info}")
    return "\n".join(lines)


# ─── /streaming ──────────────────────────────────────────────────────────────

def cmd_streaming(args: str, ctx: dict) -> str:
    repl_state = ctx.get("repl_state", {})
    current = repl_state.get("streaming_mode", ctx["settings"].get("streaming_mode", False))
    new_value = not current
    repl_state["streaming_mode"] = new_value
    ctx["settings"].set("streaming_mode", new_value)
    status = "enabled" if new_value else "disabled"
    note = " (tool-calling disabled in streaming mode)" if new_value else ""
    return f"Streaming mode {status}.{note}"


# ─── /vim ───────────────────────────────────────────────────────────────────

def cmd_vim(args: str, ctx: dict) -> str:
    current = ctx["settings"].get("vim_mode", False)
    new_value = not current
    ctx["settings"].set("vim_mode", new_value)
    ctx["repl_state"]["vim_mode"] = new_value
    status = "enabled" if new_value else "disabled"
    return f"Vim mode {status}."


# ─── /privacy ───────────────────────────────────────────────────────────────

def cmd_privacy(args: str, ctx: dict) -> str:
    return (
        "**Privacy Notice**\n\n"
        "Orion CLI runs **100% locally**.\n"
        "- All AI inference runs via Ollama on your machine\n"
        "- No data is sent to external servers\n"
        "- Web search uses DuckDuckGo (no account required)\n"
        "- Sessions are stored locally in `~/.config/orion/sessions/`\n"
        "- Memory files are stored in `ORION.md` and `~/.config/orion/ORION.md`"
    )


# ─── /restore ───────────────────────────────────────────────────────────────

def cmd_restore(args: str, ctx: dict) -> str:
    cp_manager = ctx.get("checkpoint_manager")
    if not cp_manager:
        return "Checkpointing not enabled. Enable with `/settings set checkpointing true` and restart."

    parts = args.strip().split()

    if not parts or parts[0] == "list":
        return cp_manager.list_checkpoints()

    if parts[0] == "undo":
        ok, msg = cp_manager.restore(checkpoint_id=None)
        return msg

    if parts[0].isdigit():
        ok, msg = cp_manager.restore(checkpoint_id=int(parts[0]))
        return msg

    return "Usage: `/restore` | `/restore list` | `/restore undo` | `/restore <id>`"


# ─── /extensions ────────────────────────────────────────────────────────────

def cmd_extensions(args: str, ctx: dict) -> str:
    # TODO: système d'extensions via MCP ou plugins
    return "No extensions loaded.\n(Extension system coming soon — MCP server support is available via `/mcp`)"


# ─── Helper functions for model detection ───────────────────────────────────

def _detect_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Detect available Ollama models on the local system."""
    try:
        import ollama
        models_info = ollama.list()
        # Compatibility: ListResponse object or dict depending on SDK version
        if hasattr(models_info, "models"):
            raw = models_info.models
        else:
            raw = models_info.get("models", [])
        
        model_names: list[str] = []
        for m in raw:
            if hasattr(m, "model"):
                model_names.append(m.model)
            elif isinstance(m, dict):
                model_names.append(m.get("model") or m.get("name", ""))
        
        return sorted([m for m in model_names if m])
    except Exception:
        return []


def _detect_lmstudio_models(base_url: str) -> list[str]:
    """Detect available models in LM Studio via API."""
    try:
        import httpx
        response = httpx.get(f"{base_url}/models", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            return sorted([m.get("id", "") for m in models if m.get("id")])
        return []
    except Exception:
        return []


# ─── /provider ───────────────────────────────────────────────────────────────

def cmd_provider(args: str, ctx: dict) -> str:
    """List or switch LLM providers (ollama, lmstudio, openai, anthropic)."""
    settings = ctx["settings"]
    current_provider = settings.get("llm_provider", "ollama")
    parts = args.strip().split()
    
    # No args: show current provider and available options
    if not parts or parts[0] == "":
        available = [LLMProvider.OLLAMA, LLMProvider.LMSTUDIO, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
        lines = [f"**Current provider:** `{current_provider}`\n"]
        lines.append("**Available providers:**")
        lines.append(f"- `{LLMProvider.OLLAMA}` - Local models via Ollama (100% private)")
        lines.append(f"- `{LLMProvider.LMSTUDIO}` - Local models via LM Studio (100% private)")
        lines.append(f"- `{LLMProvider.OPENAI}` - OpenAI API (GPT-4, GPT-4o, etc.)")
        lines.append(f"- `{LLMProvider.ANTHROPIC}` - Anthropic API (Claude 3.5, etc.)")
        lines.append(f"\n**Usage:**")
        lines.append(f"- `/provider` - Show this help")
        lines.append(f"- `/provider <name>` - Switch to a provider")
        lines.append(f"- `/provider test` - Test current provider connection")
        return "\n".join(lines)
    
    # Test connection
    if parts[0] == "test":
        success, message = test_connection(settings)
        if success:
            return f"✓ {current_provider.upper()}: {message}"
        else:
            return f"✗ {current_provider.upper()}: {message}"
    
    # Switch provider
    target_provider = parts[0].lower()
    valid_providers = [LLMProvider.OLLAMA, LLMProvider.LMSTUDIO, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
    
    if target_provider not in valid_providers:
        return f"Invalid provider: `{target_provider}`\nValid options: {', '.join(f'`{p}`' for p in valid_providers)}"
    
    if target_provider == current_provider:
        return f"Already using `{current_provider}` provider."
    
    # Interactive configuration based on provider
    if target_provider == LLMProvider.OLLAMA:
        renderer.get_console().print(f"\n[cyan]Switching to Ollama...[/]")
        
        # Prompt for base URL
        current_url = settings.get("ollama_base_url", "http://localhost:11434")
        renderer.get_console().print(f"[yellow]Ollama base URL [{current_url}]:[/] ", end="")
        try:
            new_url = input().strip()
            if new_url:
                settings.set("ollama_base_url", new_url)
                current_url = new_url
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Detect available models
        detected_models = _detect_ollama_models(current_url)
        if detected_models:
            renderer.get_console().print(f"\n[cyan]Detected models on your hardware:[/]")
            for i, model in enumerate(detected_models[:10], 1):  # Show max 10 models
                renderer.get_console().print(f"  [dim]{i}.[/] {model}")
            renderer.get_console().print()
        
        # Prompt for model name (allow selection by number)
        current_model = settings.get("model", "llama3.2")
        prompt_hint = "number or name" if detected_models else "name"
        renderer.get_console().print(f"[yellow]Model ({prompt_hint}) [{current_model}]:[/] ", end="")
        try:
            user_input = input().strip()
            if user_input:
                # Check if user entered a number to select from detected models
                if detected_models and user_input.isdigit():
                    model_index = int(user_input) - 1
                    if 0 <= model_index < len(detected_models[:10]):
                        settings.set("model", detected_models[model_index])
                    else:
                        renderer.get_console().print(f"[red]Invalid selection. Using: {current_model}[/]")
                else:
                    # User entered a model name directly
                    settings.set("model", user_input)
        except (EOFError, KeyboardInterrupt):
            pass
        
        settings.set("llm_provider", target_provider)
    
    elif target_provider == LLMProvider.LMSTUDIO:
        renderer.get_console().print(f"\n[cyan]Switching to LM Studio...[/]")
        
        # Prompt for base URL
        current_url = settings.get("lmstudio_base_url", "http://localhost:1234/v1")
        renderer.get_console().print(f"[yellow]LM Studio base URL [{current_url}]:[/] ", end="")
        try:
            new_url = input().strip()
            if new_url:
                # Auto-correct URL: ensure it ends with /v1 for OpenAI API compatibility
                if not new_url.endswith("/v1"):
                    new_url = new_url.rstrip("/") + "/v1"
                    renderer.get_console().print(f"[dim]  → Corrected to: {new_url}[/]")
                settings.set("lmstudio_base_url", new_url)
                current_url = new_url
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Prompt for API key
        current_key = settings.get("lmstudio_api_key", "lm-studio")
        renderer.get_console().print(f"[yellow]API key [{current_key}]:[/] ", end="")
        try:
            new_key = input().strip()
            if new_key:
                settings.set("lmstudio_api_key", new_key)
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Detect available models
        detected_models = _detect_lmstudio_models(current_url)
        if detected_models:
            renderer.get_console().print(f"\n[cyan]Detected models on your hardware:[/]")
            for i, model in enumerate(detected_models[:10], 1):  # Show max 10 models
                renderer.get_console().print(f"  [dim]{i}.[/] {model}")
            renderer.get_console().print()
        
        # Prompt for model name (allow selection by number)
        current_model = settings.get("model", "local-model")
        prompt_hint = "number or name" if detected_models else "name"
        renderer.get_console().print(f"[yellow]Model ({prompt_hint}) [{current_model}]:[/] ", end="")
        try:
            user_input = input().strip()
            if user_input:
                # Check if user entered a number to select from detected models
                if detected_models and user_input.isdigit():
                    model_index = int(user_input) - 1
                    if 0 <= model_index < len(detected_models[:10]):
                        settings.set("model", detected_models[model_index])
                    else:
                        renderer.get_console().print(f"[red]Invalid selection. Using: {current_model}[/]")
                else:
                    # User entered a model name directly
                    settings.set("model", user_input)
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Test connection
        settings.set("llm_provider", target_provider)
        renderer.get_console().print("\n[cyan]Testing connection to LM Studio...[/]")
        success, message = test_connection(settings)
        
        if success:
            renderer.get_console().print(f"[green]✓ {message}[/]\n")
        else:
            renderer.get_console().print(f"[red]✗ {message}[/]")
            renderer.get_console().print("[yellow]Provider set, but may not work until LM Studio is running.[/]\n")
    
    elif target_provider == LLMProvider.OPENAI:
        renderer.get_console().print(f"\n[cyan]Switching to OpenAI...[/]")
        
        # Prompt for API key
        current_key = settings.get("openai_api_key", "")
        masked_key = "***" + current_key[-4:] if current_key and len(current_key) > 4 else "not set"
        renderer.get_console().print(f"[yellow]OpenAI API key [{masked_key}]:[/] ", end="")
        try:
            new_key = input().strip()
            if new_key:
                settings.set("openai_api_key", new_key)
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Suggest default model
        current_model = settings.get("model", "gpt-4o")
        renderer.get_console().print(f"[yellow]Model name [{current_model}]:[/] ", end="")
        try:
            new_model = input().strip()
            if new_model:
                settings.set("model", new_model)
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Test connection if API key is set
        settings.set("llm_provider", target_provider)
        if settings.get("openai_api_key"):
            renderer.get_console().print("\n[cyan]Testing connection to OpenAI API...[/]")
            success, message = test_connection(settings)
            
            if success:
                renderer.get_console().print(f"[green]✓ {message}[/]\n")
            else:
                renderer.get_console().print(f"[red]✗ {message}[/]\n")
        else:
            renderer.get_console().print("\n[yellow]⚠ API key required. Set it with: /settings set openai_api_key YOUR_KEY[/]\n")
    
    elif target_provider == LLMProvider.ANTHROPIC:
        renderer.get_console().print(f"\n[cyan]Switching to Anthropic (Claude)...[/]")
        
        # Prompt for API key
        current_key = settings.get("anthropic_api_key", "")
        masked_key = "***" + current_key[-4:] if current_key and len(current_key) > 4 else "not set"
        renderer.get_console().print(f"[yellow]Anthropic API key [{masked_key}]:[/] ", end="")
        try:
            new_key = input().strip()
            if new_key:
                settings.set("anthropic_api_key", new_key)
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Suggest default model
        current_model = settings.get("model", "claude-3-5-sonnet-20241022")
        renderer.get_console().print(f"[yellow]Model name [{current_model}]:[/] ", end="")
        try:
            new_model = input().strip()
            if new_model:
                settings.set("model", new_model)
        except (EOFError, KeyboardInterrupt):
            pass
        
        # Test connection if API key is set
        settings.set("llm_provider", target_provider)
        if settings.get("anthropic_api_key"):
            renderer.get_console().print("\n[cyan]Testing connection to Anthropic API...[/]")
            success, message = test_connection(settings)
            
            if success:
                renderer.get_console().print(f"[green]✓ {message}[/]\n")
            else:
                renderer.get_console().print(f"[red]✗ {message}[/]\n")
        else:
            renderer.get_console().print("\n[yellow]⚠ API key required. Set it with: /settings set anthropic_api_key YOUR_KEY[/]\n")
    
    # Force agent to reset LLM on next use
    if "agent" in ctx:
        ctx["agent"]._llm = None
    
    return f"Switched to `{target_provider}` provider. Send a message to start using it."


# ─── /model ────────────────────────────────────────────────────────────────

def cmd_model(args: str, ctx: dict) -> str:
    """Change or show the current model for the active provider."""
    settings = ctx["settings"]
    current_provider = settings.get("llm_provider", "ollama")
    current_model = settings.get("model", "unknown")
    
    # No args: show current model and available models
    if not args.strip():
        lines = [f"**Current provider:** `{current_provider}`"]
        lines.append(f"**Current model:** `{current_model}`\n")
        
        # Detect and display available models based on provider
        if current_provider == LLMProvider.OLLAMA:
            base_url = settings.get("ollama_base_url", "http://localhost:11434")
            detected_models = _detect_ollama_models(base_url)
            if detected_models:
                lines.append("**Available models on your hardware:**")
                for i, model in enumerate(detected_models[:15], 1):
                    marker = "← current" if model == current_model else ""
                    lines.append(f"  {i}. `{model}` {marker}")
                lines.append(f"\n**Usage:**")
                lines.append(f"- `/model <name>` - Switch to a model by name")
                lines.append(f"- `/model <number>` - Switch to a model by number")
            else:
                lines.append("**No models detected.** Is Ollama running?")
                lines.append(f"\n**Usage:** `/model <model-name>`")
        
        elif current_provider == LLMProvider.LMSTUDIO:
            base_url = settings.get("lmstudio_base_url", "http://localhost:1234/v1")
            detected_models = _detect_lmstudio_models(base_url)
            if detected_models:
                lines.append("**Available models on your hardware:**")
                for i, model in enumerate(detected_models[:15], 1):
                    marker = "← current" if model == current_model else ""
                    lines.append(f"  {i}. `{model}` {marker}")
                lines.append(f"\n**Usage:**")
                lines.append(f"- `/model <name>` - Switch to a model by name")
                lines.append(f"- `/model <number>` - Switch to a model by number")
            else:
                lines.append("**No models detected.** Is LM Studio running?")
                lines.append(f"\n**Usage:** `/model <model-name>`")
        
        elif current_provider == LLMProvider.OPENAI:
            lines.append("**Common OpenAI models:**")
            common_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            for i, model in enumerate(common_models, 1):
                marker = "← current" if model == current_model else ""
                lines.append(f"  {i}. `{model}` {marker}")
            lines.append(f"\n**Usage:** `/model <model-name>`")
        
        elif current_provider == LLMProvider.ANTHROPIC:
            lines.append("**Common Anthropic models:**")
            common_models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            for i, model in enumerate(common_models, 1):
                marker = "← current" if model == current_model else ""
                lines.append(f"  {i}. `{model}` {marker}")
            lines.append(f"\n**Usage:** `/model <model-name>`")
        
        return "\n".join(lines)
    
    # User provided a model name or number
    target_model = args.strip()
    
    # Detect available models and check if user entered a number
    detected_models = []
    if current_provider == LLMProvider.OLLAMA:
        base_url = settings.get("ollama_base_url", "http://localhost:11434")
        detected_models = _detect_ollama_models(base_url)
    elif current_provider == LLMProvider.LMSTUDIO:
        base_url = settings.get("lmstudio_base_url", "http://localhost:1234/v1")
        detected_models = _detect_lmstudio_models(base_url)
    
    # Check if user entered a number to select from detected models
    if detected_models and target_model.isdigit():
        model_index = int(target_model) - 1
        if 0 <= model_index < len(detected_models[:15]):
            target_model = detected_models[model_index]
        else:
            return f"❌ Invalid selection. Please choose a number between 1 and {min(len(detected_models), 15)}."
    
    # Check if already using this model
    if target_model == current_model:
        return f"Already using model: `{target_model}`"
    
    # Update the model setting
    settings.set("model", target_model)
    
    # Force agent to reset LLM on next use
    if "agent" in ctx:
        ctx["agent"]._llm = None
    
    return f"✓ Switched to model: `{target_model}`\nProvider: `{current_provider}`\n\n[dim]Send a message to start using the new model.[/]"


# ─── /editor ────────────────────────────────────────────────────────────────

def cmd_editor(args: str, ctx: dict) -> str:
    import os
    editors = ["nano", "vim", "nvim", "micro", "code"]
    if args.strip():
        editor = args.strip()
        ctx["settings"].set("editor", editor)
        os.environ["EDITOR"] = editor
        return f"Editor set to: `{editor}`"
    current = ctx["settings"].get("editor", os.environ.get("EDITOR", "nano"))
    return f"Current editor: `{current}`\nAvailable: {', '.join(editors)}"


# ─── Builder ────────────────────────────────────────────────────────────────

def build_registry() -> CommandRegistry:
    """Construit et retourne le registry complet des commands."""
    registry = CommandRegistry()

    commands = [
        Command("help", ["?"], "Show help and available commands", "/help", cmd_help),
        Command("quit", ["exit", "q"], "Exit Orion CLI", "/quit", cmd_quit),
        Command("clear", [], "Clear screen and conversation history", "/clear", cmd_clear),
        Command("settings", [], "View/edit settings", "/settings [get|set] [key] [value]", cmd_settings),
        Command("provider", [], "Configure LLM provider (ollama, lmstudio, openai, anthropic)", "/provider [ollama|lmstudio|openai|anthropic|test]", cmd_provider),
        Command("model", ["models"], "Change model for current provider", "/model [name|number]", cmd_model),
        Command("memory", [], "Manage persistent memory (ORION.md)", "/memory [show|add|refresh]", cmd_memory),
        Command("chat", [], "Save/resume/list conversation sessions", "/chat [save|resume|list|delete] [tag]", cmd_chat),
        Command("stats", [], "Show session statistics", "/stats", cmd_stats),
        Command("theme", [], "Change visual theme", "/theme [dark|light|ansi]", cmd_theme),
        Command("directory", ["dir"], "Manage workspace directories", "/directory [add|list] [path]", cmd_directory),
        Command("tools", [], "List available tools", "/tools", cmd_tools),
        Command("about", [], "Show version and model info", "/about", cmd_about),
        Command("init", [], "Initialize ORION.md for this project", "/init [project-name]", cmd_init),
        Command("compress", [], "Compress conversation context with a summary", "/compress", cmd_compress),
        Command("copy", [], "Copy last response to clipboard", "/copy", cmd_copy),
        Command("mcp", [], "List/manage MCP servers and tools", "/mcp [connect|disconnect] [name]", cmd_mcp),
        Command("vim", [], "Toggle vim input mode", "/vim", cmd_vim),
        Command("streaming", [], "Toggle streaming mode (token-by-token)", "/streaming", cmd_streaming),
        Command("privacy", [], "Show privacy information", "/privacy", cmd_privacy),
        Command("restore", [], "Restore files from checkpoint", "/restore [list|undo|<id>]", cmd_restore),
        Command("extensions", [], "List active extensions", "/extensions", cmd_extensions),
        Command("editor", [], "Select default editor", "/editor [name]", cmd_editor),
    ]

    for cmd in commands:
        registry.register(cmd)

    return registry
