# Build/Lint/Test Commands
make build            # Build distribution packages
make install-dev      # Install in dev mode with extras
make test             # Run all tests with pytest
pytest tests/<file>.py::<TestClass>::<test_name>  # Single test
make test-cov         # Run tests with coverage
make lint             # Ruff linter
make format           # Ruff formatter
make type-check       # Mypy type checker

# Code Style Guidelines
- **Formatting**: Ruff (88 chars, double quotes, spaces)
- **Imports**: isort/black; stdlib → third-party → qkdpy
- **Types**: Strict mypy (all funcs typed, no untyped defs)
- **Naming**: snake_case (funcs), PascalCase (classes)
- **Tests**: pytest; test_*.py files; test_* functions
- **Errors**: Specific exceptions; no bare `except:`

# Pre-commit Hooks
- Auto-formats, lints, and type-checks on commit
- Configured in .pre-commit-config.yaml

# Notes
- Always run `make lint && make format && make type-check` before PR
- Core modules require 100% test coverage
