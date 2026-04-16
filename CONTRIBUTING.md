# Contributing to MCPBox

Thank you for your interest in contributing to MCPBox!

## Development Setup

```bash
git clone https://github.com/LouisYeap/McpBox.git
cd McpBox

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint and type-check
ruff check .
mypy src/
```

## Project Structure

```
src/mcpbox/          # Main package source
tests/               # Test suite
examples/            # Usage examples
```

## Code Standards

- Follow **PEP 8** (enforced by `ruff check`)
- Add **type hints** to all public functions
- Write **docstrings** for all public APIs
- Add **tests** for new features (pytest + pytest-asyncio)
- Keep **commits clean** — one logical change per commit

## Commit Message Format

```
<type>(<scope>): <short description>

[optional body]

Types: feat | fix | docs | refactor | test | chore
```

Example:
```
feat(openapi): support OpenAPI 3.1 JSON specs

- Update parser to handle schema objects without operationId
- Add test coverage for 3.1 discriminator fields
```

## Pull Request Checklist

- [ ] Code passes `ruff check` and `mypy`
- [ ] Tests pass (`pytest -v`)
- [ ] New features include docstrings and tests
- [ ] README updated if public API changed
- [ ] PR description explains *what* and *why*, not just *what*

## Reporting Issues

Bug reports and feature requests are welcome. Please include:
- Python version
- MCPBox version
- Minimal reproducible example
- Expected vs actual behavior

## Questions?

Open an issue or reach out via GitHub Discussions.
