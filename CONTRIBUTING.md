# Contributing to QKDpy

We welcome contributions to QKDpy! This document provides guidelines and instructions for contributors.

## Code of Conduct

Please note that this project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## How to Contribute

### Reporting Bugs

If you find a bug, please report it by opening an issue on our [GitHub Issues](https://github.com/yourusername/qkdpy/issues) page. Please include:

- A clear and descriptive title
- A detailed description of the issue
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any relevant error messages or screenshots
- Information about your environment (Python version, operating system, etc.)

### Suggesting Enhancements

We welcome suggestions for new features or improvements. Please open an issue on our [GitHub Issues](https://github.com/yourusername/qkdpy/issues) page and describe:

- A clear and descriptive title
- A detailed description of the enhancement
- The motivation behind the enhancement
- Any alternative solutions or features you've considered

### Submitting Pull Requests

We welcome pull requests! To contribute code:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Run the pre-commit hooks
7. Commit your changes with a clear commit message
8. Push your branch to your fork
9. Open a pull request against the `main` branch of the original repository

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/qkdpy.git
   cd qkdpy
   ```
2. Install the package in development mode:
   ```bash
   uv pip install -e ".[dev]"
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Coding Standards

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for all functions and methods
- Write docstrings for all public functions, classes, and methods
- Write tests for all new functionality
- Keep functions and methods small and focused
- Use meaningful variable and function names

### Testing

- All new features must include tests
- All tests must pass before a pull request will be merged
- Use pytest for testing
- Aim for high test coverage
- Run benchmarks for performance-critical changes: `pytest tests/benchmark_cv_qkd.py`

### Documentation

- Update documentation for any new features or changes
- Use clear and concise language
- Include examples where appropriate

### Code Review Process

- All pull requests go through a code review process before being merged. The process includes:
  1. Automated checks (linting, formatting, tests)
  2. Review by at least one maintainer
  3. Approval by at least one maintainer
  4. Address any feedback or requested changes
  5. Merge the pull request

### Release Process

- Releases are managed by the maintainers. The process includes:
  1. Updating the version number
  2. Updating the changelog
  3. Creating a release tag
  4. Publishing to PyPI
  5. Updating documentation

Thank you for contributing to QKDpy!
