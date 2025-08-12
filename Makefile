.PHONY: help install install-dev test test-cov lint format type-check docs clean build upload upload-test

help:
	@echo Available commands:
	@echo   install      Install the package
	@echo   install-dev  Install the package in development mode
	@echo   test         Run tests
	@echo   test-cov     Run tests with coverage
	@echo   lint         Run linting with ruff
	@echo   format       Format code with ruff
	@echo   type-check   Run type checking
	@echo   docs         Build documentation
	@echo   clean        Clean build artifacts
	@echo   build        Build distribution packages
	@echo   upload       Upload to PyPI
	@echo   upload-test  Upload to TestPyPI

install:
	uv pip install .

install-dev:
	uv sync --all-extras --dev

test:
	uv pip install -e ".[dev]"
	uv run pytest -v

test-cov:
	uv pip install -e ".[dev]"
	uv run pytest --cov=src/qkdpy --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

lint-fix:
	uv run ruff check . --fix

type-check:
	uv run mypy src/qkdpy

docs:
	cd docs && make html

clean:
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist *.egg-info rmdir /s /q *.egg-info
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist htmlcov rmdir /s /q htmlcov
	if exist .coverage del /q .coverage
	if exist coverage.xml del /q coverage.xml
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"

build: clean
	uv run python -m build

upload: build
	uv run twine upload dist/*

upload-test: build
	uv run twine upload --repository testpypi dist/*
