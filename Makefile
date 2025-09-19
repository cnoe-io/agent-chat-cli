# Common Makefile for CNOE Agent Projects
# --------------------------------------------------
# This Makefile provides common targets for building, testing, and running CNOE agents.
# Usage:
#   make <target>
# --------------------------------------------------

.PHONY: \
	build setup-venv activate-venv install run \
	help clean clean-pyc clean-venv clean-build-artifacts \
	install-uv \
	run-a2a-client run-mcp-client test \
	check-env lint ruff-fix \
	add-copyright-license-headers

.DEFAULT_GOAL := run-a2a-client
AGENT_PKG_NAME := agent_chat_cli
## ========== Setup & Clean ==========

setup-venv:        ## Create the Python virtual environment
	@echo "Setting up virtual environment..."
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv && echo "Virtual environment created."; \
	else \
		echo "Virtual environment already exists."; \
	fi
	@echo "To activate manually, run: source .venv/bin/activate"
	@. .venv/bin/activate

clean-pyc:         ## Remove Python bytecode and __pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + || echo "No __pycache__ directories found."

clean-venv:        ## Remove the virtual environment
	@rm -rf .venv && echo "Virtual environment removed." || echo "No virtual environment found."

clean-build-artifacts: ## Remove dist/, build/, egg-info/
	@rm -rf dist $(AGENT_PKG_NAME).egg-info || echo "No build artifacts found."

clean:             ## Clean all build artifacts and cache
	@$(MAKE) clean-pyc
	@$(MAKE) clean-venv
	@$(MAKE) clean-build-artifacts
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + || echo "No .pytest_cache directories found."

## ========== Environment Helpers ==========

venv-activate = . .venv/bin/activate
## ========== Install ==========

install: setup-venv ## Install Python dependencies using Poetry
	@echo "Installing dependencies..."
	@$(venv-activate) && poetry install --no-interaction
	@echo "Dependencies installed successfully."

install-uv:        ## Install uv package manager
	@$(venv-activate) pip install uv


## ========== Build & Lint ==========

build: setup-venv  ## Build the package using Poetry
	@$(venv-activate) && poetry build

lint: setup-venv   ## Lint code with ruff
	@$(venv-activate) && poetry install && ruff check $(AGENT_PKG_NAME) tests

ruff-fix: setup-venv ## Auto-fix lint issues with ruff
	@$(venv-activate) && ruff check $(AGENT_PKG_NAME) tests --fix

## ========== Clients ==========

run-a2a-client: setup-venv build install ## Run A2A client script
	@$(venv-activate) && AGENT_CHAT_PROTOCOL=a2a python agent_chat_cli

run-mcp-client: setup-venv build install ## Run MCP client script
	@$(venv-activate) uv run python -m agent_chat_cli mcp

run-slim-client: setup-venv build install ## Run SLIM client script
	@$(venv-activate) AGENT_CHAT_PROTOCOL=slim uv run python -m agent_chat_cli

## ========== Docker Build ==========
build-docker: ## Build Docker image for the agent
	@echo "Building Docker image..."
	@docker build -t cnoe/$(AGENT_PKG_NAME):latest .

## ========== Tests ==========

test: setup-venv build ## Run tests using pytest and coverage
	@$(venv-activate) && poetry install
	@$(venv-activate) && poetry add pytest-asyncio pytest-cov --dev
	@$(venv-activate) && pytest -v --tb=short --disable-warnings --maxfail=1 --ignore=evals --cov=$(AGENT_PKG_NAME) --cov-report=term --cov-report=xml

## ========== Release & Versioning ==========
release: setup-venv  ## Bump version and create a release
	@. .venv/bin/activate; poetry install
	@. .venv/bin/activate; poetry add commitizen --dev
	@. .venv/bin/activate; git tag -d stable || echo "No stable tag found."
	@. .venv/bin/activate; cz changelog
	@git add CHANGELOG.md
	@git commit -m "docs: update changelog"
	@. .venv/bin/activate; cz bump --increment PATCH
	@. .venv/bin/activate; git tag -f stable
	@echo "Version bumped and stable tag updated successfully."


## ========== Licensing & Help ==========

add-copyright-license-headers: ## Add license headers
	docker run --rm -v $(shell pwd)/$(AGENT_PKG_NAME):/workspace ghcr.io/google/addlicense:latest -c "CNOE" -l apache -s=only -v /workspace

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort
