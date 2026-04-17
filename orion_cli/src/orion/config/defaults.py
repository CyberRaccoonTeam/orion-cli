"""Valeurs par défaut de la configuration Orion CLI."""

DEFAULT_SETTINGS = {
    # LLM Provider
    "llm_provider": "ollama",  # "ollama", "lmstudio", "openai", or "anthropic"
    
    # Modèle Ollama
    "model": "qwen2.5-coder:14b",
    "model_temperature": 0.7,
    "model_context_length": 8192,
    
    # LM Studio
    "lmstudio_base_url": "http://localhost:1234/v1",
    "lmstudio_api_key": "lm-studio",
    
    # OpenAI
    "openai_api_key": "",  # Get from https://platform.openai.com/api-keys
    
    # Anthropic
    "anthropic_api_key": "",  # Get from https://console.anthropic.com/

    # Workspace
    "workspace": ".",
    "sandbox_enabled": False,

    # UI
    "theme": "dark",
    "vim_mode": False,
    "auto_accept_edits": False,
    "show_tool_confirmations": True,
    "typing_animation": True,   # Animation mot-par-mot sur la réponse finale
    "typing_delay": 0.010,      # Délai entre chaque mot (secondes)

    # Raisonnement (modèles <think>)
    "show_thinking": True,              # Afficher la réflexion des modèles de raisonnement
    "thinking_words_per_second": 30,    # Vitesse d'animation de la réflexion (replay)

    # Checkpointing
    "checkpointing": False,

    # Mémoire
    "memory_file": "ORION.md",
    "memory_discovery_enabled": True,

    # Sessions
    "sessions_dir": "~/.config/orion/sessions",

    # MCP
    "mcp_servers": {},

    # Custom commands
    "custom_commands_dir": "~/.config/orion/commands",

    # Web
    "web_search_enabled": True,
    "web_fetch_enabled": True,

    # Shell
    "shell": "bash",
    "shell_timeout": 30,

    # Ignore patterns
    "ignore_file": ".orionignore",

    # Bugs/feedback
    "bug_command": None,
}

THEMES = {
    "dark": {
        "primary": "cyan",
        "secondary": "blue",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "prompt_color": "cyan",
        "tool_color": "yellow",
        "assistant_color": "white",
        "user_color": "bright_blue",
    },
    "light": {
        "primary": "blue",
        "secondary": "magenta",
        "success": "green",
        "warning": "dark_orange",
        "error": "red",
        "muted": "grey50",
        "prompt_color": "blue",
        "tool_color": "dark_orange",
        "assistant_color": "black",
        "user_color": "blue",
    },
    "ansi": {
        "primary": "cyan",
        "secondary": "blue",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "prompt_color": "cyan",
        "tool_color": "yellow",
        "assistant_color": "white",
        "user_color": "bright_blue",
    },
}
