.PHONY: run dev test test-unit test-integration test-coverage lint format migrate migrate-new migrate-status clean help

# ── Variables ────────────────────────────────────────────────
PYTHON := python3
UVICORN := uvicorn
PYTEST := pytest
RUFF := ruff
ALEMBIC := alembic

APP := src.main:app
HOST := 0.0.0.0
PORT := 8000

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────
run: ## Start development server with hot reload
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT) --reload

dev: run ## Alias for run

prod: ## Start production server
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT) --workers 4

# ── Testing ──────────────────────────────────────────────────
test: ## Run all tests
	$(PYTEST) tests/ -v

test-unit: ## Run unit tests only
	$(PYTEST) tests/ -v -m "not integration"

test-integration: ## Run integration tests
	$(PYTEST) tests/ -v -m "integration"

test-coverage: ## Run tests with coverage report
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	$(PYTEST) tests/ -v --tb=short -x -f

# ── Code Quality ─────────────────────────────────────────────
lint: ## Run linter
	$(RUFF) check src/ tests/

lint-fix: ## Run linter with auto-fix
	$(RUFF) check src/ tests/ --fix

format: ## Format code
	$(RUFF) format src/ tests/

format-check: ## Check formatting without changing files
	$(RUFF) format src/ tests/ --check

# ── Database Migrations ──────────────────────────────────────
migrate: ## Run all pending migrations
	$(ALEMBIC) upgrade head

migrate-new: ## Create new migration (usage: make migrate-new MSG="description")
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

migrate-status: ## Show current migration status
	$(ALEMBIC) current --verbose

migrate-history: ## Show migration history
	$(ALEMBIC) history

migrate-downgrade: ## Downgrade one migration (use with caution)
	$(ALEMBIC) downgrade -1

# ── Utilities ────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

seed: ## Seed the database
	$(PYTHON) ../../infra/scripts/seed.py

seed-reset: ## Reset and re-seed the database
	$(PYTHON) ../../infra/scripts/seed.py --reset

install: ## Install dependencies
	pip install poetry && poetry install

install-dev: ## Install dev dependencies
	pip install poetry && poetry install --with dev

requirements: ## Export requirements.txt
	poetry export -f requirements.txt --without-hashes -o requirements.txt
