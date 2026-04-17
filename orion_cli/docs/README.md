# Orion CLI

**Command-Line Interface for AI Models — Your Terminal Coding Assistant**

Orion CLI is a terminal interface that connects to AI models, replicating Google Gemini CLI and Claude Code functionality. Like GitHub Copilot but in your terminal with its own personality. Use local models via Ollama/LM Studio (100% offline, no API keys) or connect to OpenAI/Anthropic APIs.

---

## 📦 About

**Orion CLI** is a complete terminal-based interface for AI coding assistants.

- Interactive REPL with vim mode and command history
- ReAct agent powered by LangChain/LangGraph
- 22 built-in slash commands
- 14 integrated tools for file operations, shell, web search, and more

See complete usage guide: [USAGE.md](USAGE.md)

> Inspired by https://geminicli.com/

---

## Quick Start

```bash
# Prerequisites: Ollama installed and running
ollama pull qwen2.5-coder:7b

# Installation
cd orion_cli/
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Launch
python main.py
```

---

## Architecture

```
orion_cli/
├── src/orion/
│   ├── main.py              # Entry point — Typer CLI (interactive, chat, init, run)
│   ├── repl.py              # REPL — prompt_toolkit (vim, history, autocompletion)
│   ├── agent.py             # LangGraph ReAct agent + ChatOllama
│   ├── config/
│   │   ├── settings.py      # Merged config (global/local/env)
│   │   ├── defaults.py      # Default values + 3 themes
│   │   └── providers.py     # Multi-provider support (Ollama, LM Studio, OpenAI, Anthropic)
│   ├── commands/
│   │   ├── registry.py      # Registry + slash command dispatch
│   │   ├── builtins.py      # 22 built-in slash commands
│   │   └── custom.py        # Custom commands via .toml files
│   ├── tools/
│   │   ├── filesystem.py    # 9 tools: read/write/replace/list/glob/search/delete/mkdir/read_many
│   │   ├── shell.py         # run_shell_command (bash, timeout, security)
│   │   ├── web.py           # web_fetch + web_search (DuckDuckGo, no API key)
│   │   └── memory_tools.py  # save_memory + write_todos
│   ├── memory/
│   │   └── manager.py       # Hierarchical ORION.md (global + project)
│   ├── session/
│   │   ├── manager.py       # Save/resume/list/delete conversations (JSON)
│   │   └── checkpoint.py    # Snapshots before modification → /restore
│   ├── mcp/
│   │   └── client.py        # MCP client: stdio + HTTP, auto-discovery of tools
│   └── ui/
│       ├── renderer.py      # Rich: banner, markdown, tool calls, stats, confirmations
│       └── theme.py         # Dynamic themes (dark/light/ansi)
├── tests/                   # 84 pytest tests — 100% passing
├── docs/
│   ├── README.md            # This file
│   ├── USAGE.md             # Complete usage guide
│   ├── PROVIDERS.md         # Provider configuration (Ollama, LM Studio, OpenAI, Anthropic)
│   └── CONTRIBUTING.md      # Contribution guidelines
├── .orionignore             # Patterns excluded from @ injection
├── requirements.txt
└── setup.py
```

---

## Features

| Feature | Status | Details |
|---|---|---|
| Interactive REPL | ✅ | prompt_toolkit, history, vim mode, autocompletion |
| ReAct Agent (tool-calling) | ✅ | LangChain + multi-provider, 14 built-in tools |
| LLM Providers | ✅ | Ollama (local) + LM Studio (local) + OpenAI + Anthropic |
| Token-by-token streaming | ✅ | Rich Live, `/streaming` to toggle |
| Reasoning models | ✅ | Live `<think>` display (deepseek-r1, qwq, qwen3) |
| Slash commands | ✅ | 22 built-in commands |
| Custom commands (.toml) | ✅ | `~/.config/orion/commands/` and `.orion/commands/` |
| Persistent memory | ✅ | Hierarchical ORION.md (global + project) |
| Sessions (save/resume) | ✅ | JSON in `~/.config/orion/sessions/` |
| Checkpointing + /restore | ✅ | Snapshots before write/replace, granular restoration |
| File injection (@) | ✅ | Files and entire directories |
| Shell commands (!) | ✅ | Direct execution + toggle shell mode |
| Web search | ✅ | DuckDuckGo, no API key |
| Web fetch | ✅ | HTTP with HTML→text conversion |
| MCP client | ✅ | stdio + HTTP, auto-discovery of tools |
| Visual themes | ✅ | dark / light / ansi |
| Headless mode | ✅ | `orion chat "..."` + `orion run file.txt` |
| Tool confirmations | ✅ | Before write/delete/dangerous shell commands |
| Multi-workspace | ✅ | `/directory add <path>` |
| Tests | ✅ | 84 pytest tests (config, memory, session, tools, commands) |

---

## Slash Commands (22)

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/?` | Help and command list |
| `/quit` | `/exit`, `/q` | Exit Orion |
| `/clear` | — | Clear screen + history |
| `/settings` | — | View/edit settings |
| `/provider` | — | Configure LLM provider (ollama, lmstudio, openai, anthropic) + endpoint + model |
| `/model` | `/models` | Change model for current provider |
| `/memory` | — | Manage memory (ORION.md) |
| `/chat` | — | Save/resume/list/delete sessions |
| `/stats` | — | Session statistics |
| `/theme` | — | Change visual theme |
| `/directory` | `/dir` | Manage workspace directories |
| `/tools` | — | List available tools |
| `/about` | — | Version and model info |
| `/init` | — | Initialize ORION.md |
| `/compress` | — | Compress conversation context |
| `/copy` | — | Copy last response |
| `/mcp` | — | MCP servers (status, connect, disconnect) |
| `/vim` | — | Toggle vim mode |
| `/streaming` | — | Toggle token-by-token streaming |
| `/privacy` | — | Privacy notice |
| `/restore` | — | Restore from checkpoint |
| `/extensions` | — | Active extensions |
| `/editor` | — | Select editor |

---

## Input Shortcuts

| Symbol | Example | Description |
|--------|---------|-------------|
| `@` | `@src/main.py` | Inject file/directory into prompt |
| `!` | `!ls -la` | Execute shell command directly |
| `!` alone | `!` | Toggle continuous shell mode |

---

## Built-in Tools (LangChain tools)

| Tool | Description |
|------|-------------|
| `read_file` | Read file with line numbers |
| `write_file` | Create or overwrite file |
| `replace` | Precise editing: replace old_string → new_string |
| `list_directory` | List directory |
| `glob` | Search files by pattern (e.g., `**/*.py`) |
| `search_file_content` | Grep through files |
| `delete_file` | Delete file/directory |
| `create_directory` | Create directory (with parents) |
| `read_many_files` | Read multiple files at once |
| `run_shell_command` | Execute bash command |
| `web_fetch` | Fetch and extract web content |
| `web_search` | DuckDuckGo search (no API key) |
| `save_memory` | Save note to ORION.md |
| `write_todos` | Manage task list |

---

## Configuration

```json
{
  "llm_provider": "ollama",
  "model": "qwen2.5-coder:7b",
  "model_temperature": 0.7,
  "model_context_length": 8192,
  "theme": "dark",
  "vim_mode": false,
  "streaming_mode": false,
  "auto_accept_edits": false,
  "show_tool_confirmations": true,
  "checkpointing": false,
  "web_search_enabled": true,
  "shell": "bash",
  "shell_timeout": 30,
  "show_thinking": true,
  "thinking_words_per_second": 30
}
```

Configuration files (local takes precedence over global):
- `~/.config/orion/settings.json` — global configuration
- `.orion/settings.json` — project configuration

---

## Custom Commands

`.toml` files in `~/.config/orion/commands/` or `.orion/commands/`:

```toml
# ~/.config/orion/commands/git/commit.toml → /git:commit
description = "Generate a Git commit message"
prompt = "Generate a conventional commit for: {{input}}"
```

---

## Provider Setup

Quick provider configuration:

```bash
# Switch to Ollama (local, free, private)
orion ❯ /provider ollama

# Switch to LM Studio (local, free, private)
orion ❯ /provider lmstudio

# Switch to OpenAI (cloud, paid, powerful)
orion ❯ /provider openai

# Switch to Anthropic Claude (cloud, paid, powerful)
orion ❯ /provider anthropic

# Change model for current provider
orion ❯ /model qwen2.5-7b-instruct

# Test connection
orion ❯ /provider test
```

See [PROVIDERS.md](PROVIDERS.md) for detailed configuration.

---

## Documentation

- **[USAGE.md](USAGE.md)** — Complete usage guide
- **[PROVIDERS.md](PROVIDERS.md)** — Configure Ollama, LM Studio, OpenAI, Anthropic
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Contribution guidelines

---

## Testing

```bash
cd orion_cli
pytest                          # Run all tests
pytest --cov=src/orion         # With coverage
pytest -v tests/test_config.py # Specific test file
```

**Current status**: 84 tests, 100% passing ✅

---

## Privacy

**With Ollama or LM Studio (local):**
- ✅ 100% local — runs entirely on your machine
- ✅ Zero data leaks — no external API calls
- ✅ Offline capable — no internet required
- ✅ No API keys needed

**With OpenAI or Anthropic (cloud):**
- ⚠️ Data is sent to their servers
- 💰 Usage-based pricing applies
- 🔑 API key required
- 🌐 Internet connection required

---

## License

MIT License — see [LICENSE](../../LICENSE) for details.

---

## Acknowledgments

- Inspired by [Google Gemini CLI](https://geminicli.com/)
- Built with [LangChain](https://python.langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/), and [Ollama](https://ollama.ai)
- UI powered by [Rich](https://rich.readthedocs.io/) and [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)
