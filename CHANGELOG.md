# Changelog

All notable changes to Orion CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-04-17

### Added
- Interactive REPL with prompt_toolkit (vim mode, history, auto-completion)
- Multi-provider support: Ollama, LM Studio, OpenAI, Anthropic
- 14 built-in tools: file ops, shell commands, web search, memory management
- 22 slash commands: /help, /provider, /model, /settings, /memory, /chat, etc.
- LangGraph ReAct agent with full tool-calling support
- Streaming token-by-token with `<think/>` detection for reasoning models
- Session management: save, resume, list, delete conversations
- Checkpoint system: auto-snapshots before modifications with /restore
- Hierarchical ORION.md memory system (global + project-scoped)
- MCP (Model Context Protocol) client support
- Custom slash commands via TOML files
- Rich terminal UI with dark/light/ansi themes
- `@path` file injection and `!command` shell execution
- 84 pytest tests with 100% pass rate
- DuckDuckGo web search (no API key required)
- JSON repair for malformed model outputs
- Text tool call fallback for models without native tool calling
- Nudge mechanism for models that stop after tool calls

### Known Limitations
- No image/multimodal support yet
- No built-in code execution sandbox
- Session history is plain text (no encryption)
