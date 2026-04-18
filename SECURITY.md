# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Orion CLI, please report it responsibly:

- **GitHub:** Open a private [Security Advisory](https://github.com/CyberRaccoonTeam/orion-cli/security/advisories/new)
- **Do NOT** open a public issue for security vulnerabilities

## Response Time
- We'll acknowledge your report within 48 hours
- We'll provide a fix timeline within 7 days
- Critical vulnerabilities will be patched ASAP

## Known Security Considerations

### Shell Command Execution
Orion can execute shell commands via the `run_shell_command` tool. This is by design for development workflows. If you're using Orion in a shared or production environment:
- Use `auto_accept_edits: false` in settings
- Review tool confirmations before accepting
- Consider disabling shell tools via MCP configuration

### API Keys
- API keys for OpenAI/Anthropic are stored locally in `~/.config/orion/settings.json`
- Never commit settings files with real API keys
- Use environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) for CI/CD

### Local Models
- When using Ollama/LM Studio, all data stays on your machine
- No telemetry, no analytics, no phone-home
- Verify model downloads from official sources
