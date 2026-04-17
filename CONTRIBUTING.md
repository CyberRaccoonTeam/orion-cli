# Contributing to Orion

Thank you for considering contributing to Orion! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/project_orion.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Development Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/project_orion.git
cd project_orion/orion_cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Run before committing:

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Testing

Write tests for all new features:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/orion

# Run specific test file
pytest tests/test_chat.py
```

## Submitting Changes

1. Ensure all tests pass
2. Update documentation if needed
3. Follow commit message conventions:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `test:` for test updates

Example: `feat: add support for multimodal inputs`

## Questions?

Open an issue on [GitHub Issues](https://github.com/yourusername/project_orion/issues) or start a discussion in [GitHub Discussions](https://github.com/yourusername/project_orion/discussions)!
