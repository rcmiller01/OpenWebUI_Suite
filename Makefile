# OpenWebUI Suite Makefile

.DEFAULT_GOAL := help

PY ?= python
COMPOSE ?= docker compose
PROFILE ?= core

R ?= ruff
MYPY ?= mypy

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sed 's/:.*## /\t- /'

build: ## Build all images
	$(COMPOSE) build

base-build: ## Build shared base image
	docker build -f docker/Dockerfile -t owui/base:py311 .

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

lint: ## Run static analysis (ruff + mypy all services)
	@echo "Running ruff (if available)"; command -v $(R) >/dev/null 2>&1 && $(R) . || echo "ruff not installed"
	@echo "Running mypy (if available)"; command -v $(MYPY) >/dev/null 2>&1 && TARGETS="$$(ls -d [0-9][0-9]-*/src 2>/dev/null || true)"; if [ -n "$$TARGETS" ]; then $(MYPY) $$TARGETS; else echo "No src targets"; fi || echo "mypy not installed"

gpu-build: ## Build CUDA variants for heavy services (adds -cuda tag)
	@for svc in 11-stt-tts-gateway 16-fastvlm-sidecar; do \
	  base_tag=$${svc#??-}; \
	  echo "Building CUDA $$svc"; \
	  docker build --build-arg BASE_IMAGE=nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 -t owui/$$base_tag:cuda $$svc; \
	done

prefetch-build: ## Build images with model prefetch layer (ARG PREFETCH_MODELS=true)
	@for svc in 11-stt-tts-gateway 16-fastvlm-sidecar; do \
	  tag=$${svc#??-}; \
	  echo "Building prefetch $$svc"; \
	  docker build --build-arg PREFETCH_MODELS=true -t owui/$$tag:prefetch $$svc; \
	done

image-sizes: ## Show local image sizes for owui/*
	docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep '^owui/' || true

test: ## Run fast API smoke tests (gateway + intent)
	$(PY) -m pytest 00-pipelines-gateway -k health || true
	$(PY) -m pytest 01-intent-router -k health || true

dev\:core: ## Launch only core profile (gateway, intent, merger, redis)
	$(COMPOSE) --profile core up -d

dev\:all: ## Launch full stack (aggregated profiles)
	$(MAKE) up PROFILE=all

compose-validate: ## Validate compose file
	$(COMPOSE) config > /dev/null

.PHONY: help build up stop down ps logs clean format lint test compose-validate gpu-build prefetch-build image-sizes
