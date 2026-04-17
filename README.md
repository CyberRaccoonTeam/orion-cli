# 🔮 Orion

**A command-line interface for AI coding assistants — Your local alternative to Gemini CLI and Claude Code**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)

Orion CLI is a powerful terminal-based interface that connects to AI models from multiple providers. Like GitHub Copilot or Claude Code, but with its own personality and running in your terminal. Use local models via Ollama/LM Studio (100% offline, no API keys) or connect to OpenAI/Anthropic APIs.

---

## ✨ Features

- 🖥️ **Terminal-Based Interface** - Full-featured CLI with interactive REPL
- 🤖 **Multi-Provider Support** - Connect to Ollama, LM Studio, OpenAI, or Anthropic
- 🔒 **Privacy First** - Run 100% locally with Ollama/LM Studio (zero data leaks)
- 🎭 **Own Personality** - Like GitHub Copilot or Claude Code, but with Orion's persona
- 🛠️ **14 Built-in Tools** - File operations, shell commands, web search, memory management
- 💬 **Interactive REPL** - Vim mode, command history, auto-completion
- 📝 **Persistent Memory** - Hierarchical ORION.md system (global + project-scoped)
- 💾 **Session Management** - Save, resume, list, and delete conversations
- 🔄 **Checkpoint System** - Auto-snapshots before modifications with `/restore`
- 🧠 **Reasoning Models** - Live `<think>` display for reasoning models (DeepSeek-R1, QwQ)
- 🌐 **Web Integration** - DuckDuckGo search (no API key) + web fetch
- 📦 **MCP Support** - Model Context Protocol client for extensibility
- 🎛️ **Custom Commands** - Create custom slash commands via TOML files

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Ollama** (for local models) - [Install Ollama](https://ollama.ai)

### Installation

```bash
# 1. Install Ollama and pull a model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder:7b

# 2. Clone and install Orion
git clone https://github.com/yourusername/project_orion.git
cd project_orion/orion_cli

# 3. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# 4. Launch Orion
python main.py
```

### First Commands

```bash
orion ❯ Hello! What can you do?

orion ❯ @src/main.py Explain this file

orion ❯ /help  # Show all available commands

orion ❯ /provider  # Switch between Ollama, LM Studio, OpenAI, Anthropic

orion ❯ /model qwen2.5-7b-instruct  # Change model for current provider
```

---

## 📦 Project Structure

**orion_cli** is the main and only component — a powerful terminal interface with:
- Interactive REPL with vim mode and history
- AI agent integration via LangChain/LangGraph
- 22 built-in slash commands
- 14 integrated tools

See complete documentation: [orion_cli/docs/README.md](orion_cli/docs/README.md)

---

## 🎯 Usage Examples

### File Operations

```bash
# Read a file
orion ❯ Read main.py and explain the structure

# Edit a file
orion ❯ Add error handling to the parse_config function in config.py

# Create new files
orion ❯ Create a test file for the DatabaseManager class
```

### Code Analysis

```bash
# Inject files with @ syntax
orion ❯ @src/**.py Review the codebase for security issues

# Analyze specific functions
orion ❯ @utils.py Refactor the validate_input function
```

### Shell Commands

```bash
# Execute shell commands with !
orion ❯ !git status

# Toggle shell mode
orion ❯ !
shell ❯ ls -la
shell ❯ git log --oneline
shell ❯ !  # Exit shell mode
```

### Memory & Sessions

```bash
# Save to persistent memory
orion ❯ /memory add "This project uses PostgreSQL database"

# Save conversation
orion ❯ /chat save refactoring-session

# Resume conversation
orion ❯ /chat resume refactoring-session
```

---

## 🔧 Configuration

### Quick Provider Setup

```bash
# Switch to Ollama (local)
orion ❯ /provider ollama

# Switch to LM Studio (local)
orion ❯ /provider lmstudio

# Switch to OpenAI (cloud)
orion ❯ /provider openai

# Switch to Anthropic Claude (cloud)
orion ❯ /provider anthropic

# Change model for current provider
orion ❯ /model qwen2.5-7b-instruct
orion ❯ /model 2  # Select by number
```

### Configuration Files

Configuration is merged from multiple sources (local takes precedence):

- **Global**: `~/.config/orion/settings.json`
- **Project**: `.orion/settings.json`
- **Environment**: `ORION_*` environment variables

See [orion_cli/docs/PROVIDERS.md](orion_cli/docs/PROVIDERS.md) for detailed provider configuration.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Usage Guide](orion_cli/docs/USAGE.md) | Complete usage documentation |
| [Provider Setup](orion_cli/docs/PROVIDERS.md) | Configure Ollama, LM Studio, OpenAI, Anthropic |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |

---

## 🎨 Screenshots

### CLI Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  🔮 Orion CLI                                                    │
│  Model: qwen2.5-coder:7b  |  Workspace: ~/my-project            │
└─────────────────────────────────────────────────────────────────┘

orion (qwen2.5-coder:7b) ❯ @src/main.py Explain the main function

🤖 Analyzing main.py...

┌─ 🔧 read_file ──────────────────────────────────────────────────┐
│ Arguments: {"path": "src/main.py", "start_line": 1}             │
│ Status: ✓ Success                                               │
└─────────────────────────────────────────────────────────────────┘

The main function initializes the application and sets up the CLI environment...
```

---

## 🏗️ Architecture

```
orion/
├── orion_cli/              # Main CLI application
│   ├── src/orion/
│   │   ├── agent.py        # LangGraph ReAct agent
│   │   ├── repl.py         # Interactive REPL (prompt_toolkit)
│   │   ├── commands/       # 22 built-in slash commands
│   │   ├── tools/          # 14 LangChain tools
│   │   ├── config/         # Settings management
│   │   ├── memory/         # ORION.md manager
│   │   ├── session/        # Conversation persistence
│   │   └── ui/             # Rich rendering + themes
│   └── tests/              # 84 pytest tests
│
├── langchain_core/         # LangChain stubs (local development)
├── langchain_ollama/       # Ollama integration
└── langgraph_local_stub/   # LangGraph stubs
```

---

## 🛠️ Available Tools

Orion includes 14 built-in tools accessible to the AI agent:

| Tool | Description |
|------|-------------|
| `read_file` | Read file with line numbers |
| `write_file` | Create or overwrite file |
| `replace` | Precise string replacement in files |
| `list_directory` | List directory contents |
| `glob` | Find files by pattern (e.g., `**/*.py`) |
| `search_file_content` | Grep through files |
| `delete_file` | Delete files/directories |
| `create_directory` | Create directories (with parents) |
| `read_many_files` | Batch read multiple files |
| `run_shell_command` | Execute bash commands |
| `web_fetch` | Fetch and extract web content |
| `web_search` | DuckDuckGo search (no API key) |
| `save_memory` | Save notes to ORION.md |
| `write_todos` | Manage todo list |

---

## 💡 Slash Commands (22)

| Command | Description |
|---------|-------------|
| `/help`, `/?` | Show available commands |
| `/provider` | Configure LLM provider (ollama, lmstudio, openai, anthropic) |
| `/model`, `/models` | Change model for current provider |
| `/settings` | View/edit settings |
| `/memory` | Manage persistent memory |
| `/chat` | Save/resume/list sessions |
| `/stats` | Show session statistics |
| `/theme` | Change visual theme (dark/light/ansi) |
| `/tools` | List available tools |
| `/clear` | Clear screen and history |
| `/quit`, `/exit` | Exit Orion |
| `/streaming` | Toggle token-by-token streaming |
| `/vim` | Toggle vim input mode |
| `/restore` | Restore from checkpoint |
| ... | [See full list](orion_cli/docs/USAGE.md#slash-commands) |

---

## 🔒 Privacy

When using **Ollama** or **LM Studio**:
- ✅ 100% local - runs entirely on your machine
- ✅ Zero data leaks - no external API calls
- ✅ Offline capable - no internet required
- ✅ No API keys needed

When using **OpenAI** or **Anthropic**:
- ⚠️ Data is sent to their servers
- 💰 Usage-based pricing applies
- 🔑 API key required
- 🌐 Internet connection required

---

## 🧪 Testing

```bash
cd orion_cli
pytest                          # Run all tests
pytest --cov=src/orion         # With coverage
pytest -v tests/test_config.py # Specific test file
```

**Current status**: 84 tests, 100% passing ✅

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/yourusername/project_orion.git
cd project_orion/orion_cli

# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by [Google Gemini CLI](https://geminicli.com/) and [Anthropic Claude Code](https://claude.ai/)
- Similar to [GitHub Copilot](https://github.com/features/copilot) but for the terminal with its own personality
- Built with [LangChain](https://python.langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/), and [Ollama](https://ollama.ai)
- Terminal UI powered by [Rich](https://rich.readthedocs.io/) and [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/project_orion/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/project_orion/discussions)
- 📧 **Email**: your-email@example.com

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by the Orion community

</div>
