# Orion CLI — Complete Usage Guide

> Local AI coding assistant powered by Ollama, LM Studio, OpenAI, or Anthropic

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [First Launch](#3-first-launch)
4. [Basic Usage](#4-basic-usage)
5. [Slash Commands](#5-slash-commands)
6. [Input Shortcuts](#6-input-shortcuts)
7. [Memory Management (ORION.md)](#7-memory-management-orionmd)
8. [Session Management](#8-session-management)
9. [Checkpointing and Restore](#9-checkpointing-and-restore)
10. [Streaming Mode](#10-streaming-mode)
11. [Advanced Configuration](#11-advanced-configuration)
12. [Custom Commands (.toml)](#12-custom-commands-toml)
13. [MCP Servers](#13-mcp-servers)
14. [Non-Interactive Mode (Headless)](#14-non-interactive-mode-headless)
15. [Visual Themes](#15-visual-themes)
16. [Changing Models](#16-changing-models)
17. [Testing](#17-testing)
18. [Troubleshooting](#18-troubleshooting)

---

## 1. Prerequisites

| Dependency | Min Version | Installation |
|---|---|---|
| Python | 3.10+ | `sudo apt install python3` |
| pip | — | `sudo apt install python3-pip` |
| Ollama | latest | See below |

### Installing Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Verify Ollama is running
ollama serve &
ollama list
```

### Download a Model

```bash
# Recommended model (lightweight and powerful for code)
ollama pull qwen2.5-coder:7b

# Alternative models
ollama pull mistral:7b           # Good general purpose
ollama pull deepseek-coder:6.7b  # Code specialist
ollama pull deepseek-r1:7b       # Reasoning model
```

### Alternative: LM Studio

Orion also supports **LM Studio** as an LLM provider via its OpenAI-compatible API.

```bash
# 1. Download and install LM Studio from https://lmstudio.ai
# 2. Load a model in LM Studio (e.g., Mistral 7B, Qwen, etc.)
# 3. Start the local server in LM Studio ("Server" tab)
#    Default: http://localhost:1234
# 4. In Orion CLI, change the provider:
```

From the REPL:
```
> /provider lmstudio
```

Orion will prompt you to configure the server URL and API key (optional).

### Alternative: OpenAI

Use your own OpenAI API key to access GPT-4, GPT-4o, etc.

```bash
# From the REPL:
> /provider openai
```

Orion will ask for:
- Your OpenAI API key (get one at https://platform.openai.com/api-keys)
- The model to use (default: `gpt-4o`)

Recommended models:
- `gpt-4o` - Most recent and powerful
- `gpt-4o-mini` - More economical
- `gpt-4-turbo` - Good balance of performance/cost
- `o1-preview` / `o1-mini` - Advanced reasoning models

Manual configuration:
```
> /settings set openai_api_key sk-proj-...
> /settings set model gpt-4o
> /provider test
```

### Alternative: Anthropic (Claude)

Use your own Anthropic API key to access Claude 3.5, etc.

```bash
# From the REPL:
> /provider anthropic
```

Orion will ask for:
- Your Anthropic API key (get one at https://console.anthropic.com/)
- The model to use (default: `claude-3-5-sonnet-20241022`)

Recommended models:
- `claude-3-5-sonnet-20241022` - Most powerful
- `claude-3-5-haiku-20241022` - Faster and more economical
- `claude-3-opus-20240229` - Maximum reasoning capability

Manual configuration:
```
> /settings set anthropic_api_key sk-ant-...
> /settings set model claude-3-5-sonnet-20241022
> /provider test
```

The connection will be tested automatically.

---

## 2. Installation

### From the orion_cli/ directory

```bash
cd /path/to/project_orion/orion_cli/

# Option A — Standard installation (recommended)
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -e .

# Option B — Without venv (if USB drive doesn't support symlinks)
pip install -r requirements.txt --user
```

### Verify Installation

```bash
# Check that orion command is available
orion --version

# Or run directly
python main.py
```

---

## 3. First Launch

```bash
python main.py
```

You'll see the welcome banner:

```
╔═══════════════════════════════════════════════════════════╗
║                      🔮 ORION CLI                         ║
║              Local AI Agent — 100% Private               ║
╚═══════════════════════════════════════════════════════════╝

Model: qwen2.5-coder:7b
Workspace: /home/user/my-project
Type /help for commands

orion (qwen2.5-coder:7b) ❯ 
```

### Initial Setup

```bash
# Test your provider connection
orion ❯ /provider test

# Change provider if needed
orion ❯ /provider ollama

# Change model
orion ❯ /model qwen2.5-7b-instruct

# Initialize project memory
orion ❯ /init my-project
```

---

## 4. Basic Usage

### Simple Questions

```bash
orion ❯ What is the difference between async and sync in Python?

orion ❯ Explain how decorators work
```

### File Operations

```bash
# Read a file
orion ❯ Read the config.py file and explain it

# Inject file content with @
orion ❯ @src/main.py Explain the main function

# Edit a file
orion ❯ Add error handling to the database connection in db.py

# Create a new file
orion ❯ Create a new file called test_utils.py with unit tests for utils.py
```

### Code Analysis

```bash
# Analyze multiple files
orion ❯ @src/**.py Review the codebase for potential bugs

# Specific analysis
orion ❯ @models/ Check if all models follow the same naming convention
```

### Shell Commands

```bash
# Execute a command
orion ❯ !git status

# Get help with commands
orion ❯ !ls -la && du -sh *

# Toggle shell mode
orion ❯ !
shell ❯ cd src/
shell ❯ grep -r "TODO" .
shell ❯ !  # Exit shell mode
```

---

## 5. Slash Commands

Full list of 22 built-in commands:

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/?` | Show help and available commands |
| `/quit` | `/exit`, `/q` | Exit Orion CLI |
| `/clear` | — | Clear screen and conversation history |
| `/settings` | — | View/edit settings |
| `/provider` | — | Configure LLM provider (ollama, lmstudio, openai, anthropic) |
| `/model` | `/models` | Change model for current provider |
| `/memory` | — | Manage persistent memory (ORION.md) |
| `/chat` | — | Save/resume/list/delete sessions |
| `/stats` | — | Show session statistics |
| `/theme` | — | Change visual theme |
| `/directory` | `/dir` | Manage workspace directories |
| `/tools` | — | List available tools |
| `/about` | — | Show version and model info |
| `/init` | — | Initialize ORION.md for this project |
| `/compress` | — | Compress conversation context with a summary |
| `/copy` | — | Copy last response to clipboard |
| `/mcp` | — | List/manage MCP servers |
| `/vim` | — | Toggle vim input mode |
| `/streaming` | — | Toggle token-by-token streaming |
| `/privacy` | — | Show privacy information |
| `/restore` | — | Restore files from checkpoint |
| `/extensions` | — | List active extensions |
| `/editor` | — | Select default editor |

### Examples

```bash
# Get help
orion ❯ /help

# Change theme
orion ❯ /theme light

# Save conversation
orion ❯ /chat save debugging-session

# List tools
orion ❯ /tools

# Show statistics
orion ❯ /stats
```

---

## 6. Input Shortcuts

| Symbol | Example | Description |
|--------|---------|-------------|
| `@` | `@src/main.py` | Inject file/directory into prompt |
| `@` | `@src/**.py` | Inject multiple files with glob pattern |
| `!` | `!ls -la` | Execute shell command directly |
| `!` | `!` (alone) | Toggle continuous shell mode |

### @ Injection Examples

```bash
# Single file
orion ❯ @config.py Explain this configuration

# Multiple files
orion ❯ @src/*.py @tests/*.py Review test coverage

# Entire directory
orion ❯ @docs/ Summarize the documentation

# Glob patterns
orion ❯ @**/*.md Check all markdown files for broken links
```

---

## 7. Memory Management (ORION.md)

Orion maintains a hierarchical memory system:

- **Global memory**: `~/.config/orion/ORION.md` (shared across all projects)
- **Project memory**: `<workspace>/ORION.md` (project-specific)

### Commands

```bash
# Initialize project memory
orion ❯ /init my-project

# View memory
orion ❯ /memory show

# Add to memory
orion ❯ /memory add "This project uses PostgreSQL for the database"

# Refresh memory (reload from disk)
orion ❯ /memory refresh
```

### Manual Editing

You can also edit ORION.md directly with your favorite editor:

```bash
orion ❯ !nano ORION.md
orion ❯ /memory refresh
```

---

## 8. Session Management

Save and resume conversations:

```bash
# Save current session
orion ❯ /chat save refactoring-v2

# List all sessions
orion ❯ /chat list

# Resume a session
orion ❯ /chat resume refactoring-v2

# Delete a session
orion ❯ /chat delete old-session
```

Sessions are stored in `~/.config/orion/sessions/` as JSON files.

---

## 9. Checkpointing and Restore

Orion automatically creates checkpoints before file modifications.

### Enable Checkpointing

```bash
orion ❯ /settings set checkpointing true
```

### Restore Commands

```bash
# List all checkpoints
orion ❯ /restore list

# Undo last change
orion ❯ /restore undo

# Restore specific checkpoint
orion ❯ /restore 3
```

### How it Works

- Before every `write_file`, `replace`, or `delete_file` operation
- Checkpoint stores: file path, content, timestamp
- Stored in `~/.config/orion/checkpoints/`

---

## 10. Streaming Mode

Toggle token-by-token streaming:

```bash
# Enable streaming
orion ❯ /streaming

# Now responses appear word-by-word
orion ❯ Explain quantum computing

# Toggle off
orion ❯ /streaming
```

**Note**: Tool calling is disabled in streaming mode.

---

## 11. Advanced Configuration

### Settings File Locations

1. **Global**: `~/.config/orion/settings.json`
2. **Local**: `<workspace>/.orion/settings.json`
3. **Environment**: `ORION_*` variables

### View All Settings

```bash
orion ❯ /settings
```

### Modify Settings

```bash
orion ❯ /settings set model qwen2.5-7b-instruct
orion ❯ /settings set model_temperature 0.8
orion ❯ /settings set theme dark
orion ❯ /settings set vim_mode true
```

### Available Settings

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

---

## 12. Custom Commands (.toml)

Create custom slash commands using TOML files.

### Location

- **Global**: `~/.config/orion/commands/`
- **Local**: `<workspace>/.orion/commands/`

### Example: Git Commit Command

Create `~/.config/orion/commands/git/commit.toml`:

```toml
# Command will be accessible as /git:commit
description = "Generate a conventional commit message"
prompt = "Generate a conventional commit message for: {{input}}"
```

Usage:

```bash
orion ❯ /git:commit Added user authentication
```

### Example: Code Review Command

Create `.orion/commands/review.toml`:

```toml
description = "Perform code review on a file"
prompt = """
Review the following code for:
- Bug potential
- Performance issues
- Code style and best practices
- Security vulnerabilities

{{input}}
"""
```

Usage:

```bash
orion ❯ @src/auth.py /review
```

---

## 13. MCP Servers

Orion supports the Model Context Protocol (MCP) for extensibility.

### Configure MCP Servers

Edit `~/.config/orion/settings.json`:

```json
{
  "mcp_servers": {
    "my-server": {
      "transport": "stdio",
      "command": ["node", "/path/to/server.js"]
    },
    "http-server": {
      "transport": "http",
      "url": "http://localhost:3000"
    }
  }
}
```

### MCP Commands

```bash
# Show MCP status
orion ❯ /mcp

# Connect to a server
orion ❯ /mcp connect my-server

# Disconnect
orion ❯ /mcp disconnect my-server
```

---

## 14. Non-Interactive Mode (Headless)

Run Orion without the REPL:

### Single Message

```bash
# Send a single message
orion chat "Explain recursion"

# With file injection
orion chat "@main.py Explain the entry point"
```

### Process a File

```bash
# Create an instruction file
echo "Review all Python files for PEP 8 compliance" > task.txt

# Run it
orion run task.txt
```

### Scripting

```bash
#!/bin/bash
# automation.sh

orion chat "@src/**.py Generate a summary of all modules" > summary.md
orion chat "Create unit tests for UserManager class" > tests/test_user.py
```

---

## 15. Visual Themes

Three built-in themes:

```bash
# Dark theme (default)
orion ❯ /theme dark

# Light theme
orion ❯ /theme light

# ANSI theme (minimal colors)
orion ❯ /theme ansi
```

Themes are saved to settings and persist across sessions.

---

## 16. Changing Models

### Quick Model Change

```bash
# Show available models
orion ❯ /model

# Change by name
orion ❯ /model qwen2.5-7b-instruct

# Change by number (from detected list)
orion ❯ /model 2
```

### Provider-Specific

Each provider manages models differently:

**Ollama**: Auto-detects local models
**LM Studio**: Detects loaded models via API
**OpenAI**: Use standard model names (gpt-4o, gpt-4-turbo, etc.)
**Anthropic**: Use Claude model names (claude-3-5-sonnet-20241022, etc.)

---

## 17. Testing

Orion includes comprehensive tests:

```bash
cd orion_cli

# Run all tests
pytest

# Run with coverage
pytest --cov=src/orion

# Run specific test file
pytest tests/test_config.py

# Verbose output
pytest -v

# Run specific test
pytest tests/test_tools_filesystem.py::test_read_file
```

**Current test coverage**: 84 tests, 100% passing ✅

---

## 18. Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# Test connection from Orion
orion ❯ /provider test
```

### LM Studio Connection Issues

```bash
# Check if LM Studio server is running
curl http://localhost:1234/v1/models

# In LM Studio: Server tab → Start Server
# In Orion:
orion ❯ /settings set lmstudio_base_url http://localhost:1234/v1
orion ❯ /provider test
```

### Model Not Found

```bash
# List available models
ollama list

# Pull the model
ollama pull qwen2.5-coder:7b

# Update Orion settings
orion ❯ /model qwen2.5-coder:7b
```

### Import Errors

```bash
# Reinstall dependencies
pip install -e . --force-reinstall

# Or
pip install -r requirements.txt --upgrade
```

### Permission Denied

```bash
# On Linux, ensure ~/.config/orion is writable
chmod -R u+w ~/.config/orion

# Or create it
mkdir -p ~/.config/orion
```

### Slow Responses

- Use a smaller model (e.g., `mistral:7b` instead of `qwen2.5-coder:14b`)
- Reduce context length: `/settings set model_context_length 4096`
- Enable streaming mode: `/streaming`

---

## Getting Help

- 📚 **Documentation**: [README.md](README.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/project_orion/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/project_orion/discussions)

---

**Happy coding with Orion! 🔮**
