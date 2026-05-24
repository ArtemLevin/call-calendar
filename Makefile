# Booking Calendar Service - Development Commands
# ================================================

.PHONY: setup setup-mirror setup-wheelhouse build-wheelhouse dev test lint typecheck migrate coverage clean help test-ci-mirror test-ci-wheelhouse smoke-fullstack

# Configuration
PYTHON := python3
PIP := pip
PYTEST := pytest
MYPY := mypy
RUFF := ruff
ALEMBIC := alembic

# =============================================================================
# Setup
# =============================================================================

setup: ## Initial project setup
	@echo "Setting up project..."
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	$(PYTHON) -m pre_commit install
	@echo "Setup complete!"


setup-mirror: ## Setup via internal Python package mirror
	@echo "Setting up project via mirror..."
	./scripts/setup_with_mirror.sh
	@echo "Mirror setup complete!"

setup-wheelhouse: ## Setup from local wheelhouse (offline install)
	@echo "Setting up project from wheelhouse..."
	./scripts/setup_from_wheelhouse.sh
	@echo "Wheelhouse setup complete!"

build-wheelhouse: ## Download dependencies into local wheelhouse
	@echo "Building local wheelhouse..."
	./scripts/build_wheelhouse.sh
	@echo "Wheelhouse build complete!"

setup-db: ## Initialize database
	@echo "Initializing database..."
	$(ALEMBIC) upgrade head
	@echo "Database initialized!"

# =============================================================================
# Development
# =============================================================================

dev: ## Run development server with hot reload
	@echo "Starting development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## Run with debug logging
	@echo "Starting development server (debug mode)..."
	DEBUG=true uvicorn app.main:app --reload --log-level debug

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "Running tests..."
	$(PYTEST) tests/ -v

test-fast: ## Run tests without coverage (faster)
	@echo "Running tests (fast mode)..."
	$(PYTEST) tests/ -v --no-cov

test-watch: ## Run tests on file changes
	@echo "Running tests in watch mode..."
	ptw --now . --runner "$(PYTEST) tests/ -v"

test-single: ## Run single test (usage: make test-single TEST=path/to/test.py::test_name)
	@echo "Running single test: $(TEST)"
	$(PYTEST) $(TEST) -v -s

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linter (ruff)
	@echo "Running linter..."
	$(RUFF) check app/ tests/

lint-fix: ## Auto-fix linting issues
	@echo "Fixing linting issues..."
	$(RUFF) check app/ tests/ --fix

format: ## Format code with ruff
	@echo "Formatting code..."
	$(RUFF) format app/ tests/

typecheck: ## Run type checker (mypy)
	@echo "Running type checker..."
	$(MYPY) app/ --strict

check-all: lint typecheck test ## Run all checks

# =============================================================================
# Database
# =============================================================================

migrate: ## Run database migrations
	@echo "Running migrations..."
	$(ALEMBIC) upgrade head

migrate-test: ## Run migrations on test database
	@echo "Running migrations on test database..."
	TEST_DB=true $(ALEMBIC) upgrade head

migration-new: ## Create new migration (usage: make migration-new MSG="description")
	@echo "Creating migration: $(MSG)"
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

migration-down: ## Rollback last migration
	@echo "Rolling back last migration..."
	$(ALEMBIC) downgrade -1

# =============================================================================
# Coverage
# =============================================================================

coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	$(PYTEST) tests/ --cov=app --cov-report=term-missing

coverage-html: ## Generate HTML coverage report
	@echo "Generating HTML coverage report..."
	$(PYTEST) tests/ --cov=app --cov-report=html
	@echo "Open coverage_html/index.html in browser"

coverage-xml: ## Generate XML coverage report (for CI)
	@echo "Generating XML coverage report..."
	$(PYTEST) tests/ --cov=app --cov-report=xml

# =============================================================================
# Docker (Optional)
# =============================================================================

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show container logs
	docker-compose logs -f

docker-db: ## Access database in container
	docker-compose exec db psql -U booking_user -d booking_db

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean build artifacts
	@echo "Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "coverage_html" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	@echo "Clean complete!"

clean-db: ## Drop and recreate database (WARNING: destroys data)
	@echo "WARNING: This will destroy all data. Continue? (y/N)"
	@read confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Recreating database..."
	$(ALEMBIC) downgrade base
	$(ALEMBIC) upgrade head
	@echo "Database recreated!"

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "Booking Calendar Service - Available Commands"
	@echo "=============================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup      - Initial setup"
	@echo "  make dev        - Start development server"
	@echo "  make test       - Run all tests"
	@echo "  make check-all  - Run lint, typecheck, and tests"


test-ci-mirror: ## Setup from mirror and run tests/lint/typecheck
	@echo "Running CI checks with mirror-backed setup..."
	./scripts/setup_with_mirror.sh
	. .venv/bin/activate && $(PYTEST) tests/ -v
	. .venv/bin/activate && $(RUFF) check app/ tests/
	. .venv/bin/activate && $(MYPY) app/ --strict


test-ci-wheelhouse: ## Install from local wheelhouse and run tests/lint/typecheck
	@echo "Running CI checks with wheelhouse-backed setup..."
	./scripts/setup_from_wheelhouse.sh
	. .venv/bin/activate && $(PYTEST) tests/ -v
	. .venv/bin/activate && $(RUFF) check app/ tests/
	. .venv/bin/activate && $(MYPY) app/ --strict


smoke-fullstack: ## Run docker-compose full-stack smoke checks (health + UI + API happy/conflict/upcoming)
	@echo "Running full-stack smoke checks..."
	./scripts/smoke_fullstack.sh
