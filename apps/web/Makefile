.PHONY: dev build start test test-watch lint lint-fix format typecheck clean help

# ── Variables ────────────────────────────────────────────────
NPM := npm
NPM_RUN := $(NPM) run

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────
dev: ## Start development server
	$(NPM_RUN) dev

build: ## Build for production
	$(NPM_RUN) build

start: ## Start production server
	$(NPM_RUN) start

# ── Testing ──────────────────────────────────────────────────
test: ## Run all tests
	$(NPM_RUN) test

test-watch: ## Run tests in watch mode
	$(NPM_RUN) test -- --watch

test-ui: ## Run tests with UI
	$(NPM_RUN) test -- --ui

test-coverage: ## Run tests with coverage
	$(NPM_RUN) test -- --coverage

# ── Code Quality ─────────────────────────────────────────────
lint: ## Run ESLint
	$(NPM_RUN) lint

lint-fix: ## Run ESLint with auto-fix
	$(NPM_RUN) lint -- --fix

format: ## Format code with Prettier
	$(NPM_RUN) format

format-check: ## Check formatting without changing files
	$(NPM_RUN) format -- --check

typecheck: ## Run TypeScript type checker
	$(NPM) exec tsc -- --noEmit

# ── Utilities ────────────────────────────────────────────────
clean: ## Remove build artifacts
	rm -rf .next out node_modules/.cache

install: ## Install dependencies
	$(NPM) install

update: ## Update dependencies
	$(NPM) update

analyze: ## Analyze bundle size
	ANALYZE=true $(NPM_RUN) build

# ── Docker ───────────────────────────────────────────────────
docker-build: ## Build Docker image
	docker build -t deskforge-web -f ../../infra/Dockerfile.web .

docker-run: ## Run Docker image
	docker run -p 3000:3000 deskforge-web
