.PHONY: help install install-dev test test-cov lint format type-check docs clean build upload upload-test

help:
	@echo "Available commands:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install the package in development mode"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting with ruff"
	@echo "  format       Format code with ruff"
	@echo "  type-check   Run type checking"
	@echo "  docs         Build documentation"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build distribution packages"
	@echo "  upload       Upload to PyPI"
	@echo "  upload-test  Upload to TestPyPI"

install:
	uv pip install .

install-dev:
	uv sync --all-extras --dev

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=qkdpy --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy qkdpy

docs:
	cd docs && make html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	uv run python -m build

upload: build
	uv run twine upload dist/*

upload-test: build
	uv run twine upload --repository testpypi dist/*
