.PHONY: help install frontend-install frontend-test frontend-build test lint format format-check docs docs-serve validate clean all dev

help:	## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:	## Install dependencies
	uv sync

frontend-install:	## Install frontend dependencies
	npm --prefix ui install --cache /Users/connorkitchings/.cache/npm

frontend-test:	## Run frontend tests
	npm --prefix ui test

frontend-build:	## Build frontend assets
	npm --prefix ui run build

test:	## Run tests with coverage
	uv run pytest --cov=project_manager --cov-report=html --cov-report=term-missing

lint:	## Run linter
	uv run ruff check .

format:	## Format code
	uv run ruff format .

format-check:	## Check code formatting
	uv run ruff format . --check

docs:	## Build documentation
	uv run mkdocs build

docs-serve:	## Serve documentation locally
	uv run mkdocs serve

validate:	## Validate code and docs
	npm --prefix ui test
	npm --prefix ui run build
	uv run ruff check .
	uv run pytest -q
	uv run --extra dev mkdocs build

clean:	## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov site

all:	## Run all quality checks (format, lint, test)
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test

dev:	## Start development environment
	@echo "Starting development environment..."
	@echo "Run 'uv run flask --app project_manager.api.main run' for the backend"
	@echo "Run 'npm --prefix ui run dev' for frontend development"
	@echo "Run 'make validate' to verify the full stack"
