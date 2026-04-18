# Contributing to Orion CLI

First off — thanks for being here. Whether you're fixing a typo or adding a major feature, every contribution matters.

## Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/orion-cli.git
cd orion-cli

# 2. Set up environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"

# 3. Run tests
cd orion_cli
pytest

# 4. Run Orion
python main.py
```

## Development Setup

### Prerequisites
- Python 3.10+
- Ollama (for local model testing)
- Git

### Project Structure
```
orion-cli/
├── orion_cli/           # Main application
│   ├── src/orion/       # Source code
│   │   ├── agent.py     # LangGraph ReAct agent
│   │   ├── repl.py      # Interactive REPL
│   │   ├── commands/    # Slash commands
│   │   ├── tools/       # LangChain tools
│   │   ├── config/      # Settings & providers
│   │   ├── memory/      # ORION.md system
│   │   ├── session/     # Conversation persistence
│   │   ├── mcp/         # Model Context Protocol
│   │   └── ui/          # Rich rendering & themes
│   └── tests/           # Test suite
├── langchain_core/      # LangChain stubs (local dev)
├── langchain_ollama/    # Ollama integration
└── langgraph_local_stub/ # LangGraph stubs
```

## Making Changes

### Code Style
- **Formatting:** Black (line-length: 100)
- **Linting:** Ruff
- **Type hints:** Encouraged but not required
- **Language:** Code and comments in English. Variable names must be in English.

### Commit Messages
Keep them clear and descriptive:
```
feat: add OpenAI streaming support
fix: handle missing Ollama connection gracefully
docs: update provider setup guide
```

### Testing
- Run tests before submitting: `pytest`
- Add tests for new features
- All tests must pass (currently 84/84 ✅)
- Use `pytest --cov=src/orion` for coverage

### Before Submitting a PR
1. ✅ All tests pass
2. ✅ Code is formatted (`black src/ tests/`)
3. ✅ No lint errors (`ruff check src/ tests/`)
4. ✅ New features have tests
5. ✅ README updated if needed

## Reporting Issues

### Bug Reports
Please include:
- Python version (`python3 --version`)
- OS
- Steps to reproduce
- Expected vs actual behavior
- Error output (if any)

### Feature Requests
- Describe the problem you're trying to solve
- Explain why existing features don't cover it
- Suggest a solution (optional but helpful)

## Adding New Tools

Tools are LangChain tools in `orion_cli/src/orion/tools/`:

```python
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> str:
    """Brief description of what the tool does."""
    # Implementation
    return result
```

Register it in `orion_cli/src/orion/tools/__init__.py`.

## Adding New Providers

Providers are in `orion_cli/src/orion/config/providers.py`:

1. Add provider config class
2. Add to the provider factory function
3. Add tests in `orion_cli/tests/test_providers.py`
4. Update `orion_cli/docs/PROVIDERS.md`

## Questions?

- **Issues:** [GitHub Issues](https://github.com/CyberRaccoonTeam/orion-cli/issues)
- **Discussions:** [GitHub Discussions](https://github.com/CyberRaccoonTeam/orion-cli/discussions)

---

Licensed under MIT. By contributing, you agree your code is also MIT licensed.
