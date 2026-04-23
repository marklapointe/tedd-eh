.PHONY: help venv install install-dev test test-cov lint format run run-server run-mock-client run-demo clean

PYTHON := python3
VENV_DIR := .venv
VENV_BIN := $(CURDIR)/$(VENV_DIR)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python

help: ## Show this help message
	@echo "Tedd-EH - Build Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

venv: ## Create Python virtual environment
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

install: venv ## Install server dependencies
	cd teddy-server && $(PIP) install -e ".[dev]"

install-dev: install ## Install all dev dependencies
	@echo "Dev dependencies installed"

test: ## Run all tests
	cd teddy-server && $(PYTHON_VENV) -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	cd teddy-server && $(PYTHON_VENV) -m pytest tests/ -v --cov=teddy_server --cov-report=term-missing

lint: ## Run linter (ruff)
	cd teddy-server && $(PYTHON_VENV) -m ruff check src/ tests/

format: ## Format code with ruff
	cd teddy-server && $(PYTHON_VENV) -m ruff format src/ tests/

run: install ## Build environment and start the Tedd-EH server
	@echo "Starting Tedd-EH Server on http://0.0.0.0:8000"
	@echo "Dashboard: http://0.0.0.0:8000/static/index.html"
	@echo "API docs:  http://0.0.0.0:8000/docs"
	@echo "Press Ctrl+C to stop"
	@echo ""
	cd teddy-server && $(PYTHON_VENV) -m uvicorn teddy_server.main:app --reload --host 0.0.0.0 --port 8000

run-server: ## Start the Tedd-EH server (assumes install already done)
	cd teddy-server && $(PYTHON_VENV) -m uvicorn teddy_server.main:app --reload --host 0.0.0.0 --port 8000

run-mock-client: ## Start a mock doll client for testing
	cd teddy-server && $(PYTHON_VENV) -c "from teddy_server.mock_client import run_mock_client; import asyncio; asyncio.run(run_mock_client())"

run-demo: ## Start server and mock client in separate terminals
	@echo "Starting Tedd-EH Server..."
	@cd teddy-server && $(PYTHON_VENV) -m uvicorn teddy_server.main:app --host 0.0.0.0 --port 8000 &
	@sleep 2
	@echo "Starting Mock Doll Client..."
	@cd teddy-server && $(PYTHON_VENV) -c "from teddy_server.mock_client import run_mock_client; import asyncio; asyncio.run(run_mock_client())"

clean: ## Remove build artifacts and venv
	rm -rf $(VENV_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
