# OpenWebUI Suite Makefile

.DEFAULT_GOAL := help

PY ?= python
COMPOSE ?= docker compose
PROFILE ?= core

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sed 's/:.*## /\t- /'

build: ## Build all images
	$(COMPOSE) build

up: ## Start selected profile (PROFILE=core|all)
ifeq ($(PROFILE),all)
	$(COMPOSE) --profile core --profile memory --profile affect --profile policy --profile tools --profile finance --profile speech --profile vision --profile telemetry --profile extras up -d
else
	$(COMPOSE) --profile $(PROFILE) up -d
endif

stop: ## Stop current profile containers
	$(COMPOSE) down

down: stop ## Alias for stop

ps: ## List containers
	$(COMPOSE) ps

logs: ## Tail logs (SERVICE=name optional)
	$(COMPOSE) logs -f $(SERVICE)

clean: ## Remove containers & dangling images
	$(COMPOSE) down -v || true
	docker image prune -f

format: ## Run rough formatting (py only fastapi services)
	@echo "(Placeholder) Add black/isort here if desired"

lint: ## Placeholder lint target
	@echo "(Placeholder) Add ruff/mypy here if desired"

test: ## Run fast API smoke tests (gateway + intent)
	$(PY) -m pytest 00-pipelines-gateway -k health || true
	$(PY) -m pytest 01-intent-router -k health || true

compose-validate: ## Validate compose file
	$(COMPOSE) config > /dev/null

.PHONY: help build up stop down ps logs clean format lint test compose-validate
