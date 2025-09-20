SHELL := /bin/bash

# Tooling variables
PY := python3
UNIT := ./scripts/test-unit
API := ./scripts/test-api
PLAYWRIGHT := ./scripts/test-e2e
MYPY := ./scripts/run_mypy.sh

# User-tunable knobs
ARGS ?=
PYTEST_FLAGS ?=
PATHS_TO_MUTATE ?= src
JOBS ?= 4

# Pick docker compose flavor automatically
DOCKER_COMPOSE := $(shell command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

# Default pipeline
.PHONY: all
all:
	$(MAKE) start-app
	$(MAKE) restart-app
	$(MAKE) test
	$(MAKE) test-typecheck
	$(MAKE) test-api
	$(MAKE) test-e2e
	$(MAKE) test-e2e-chromium
	$(MAKE) test-mutation
	$(MAKE) stop-app

.PHONY: help start-app restart-app test test-typecheck test-api test-e2e test-e2e-chromium test-mutation  stop-app

help:
	@echo "Available targets:"
	@echo "  make start-app            # build and start Docker services"
	@echo "  make restart-app          # rebuild and start Docker services"
	@echo "  make test                 # run unit tests"
	@echo "  make test-typecheck       # run mypy type checking"
	@echo "  make test-api             # run API tests (Newman)"
	@echo "  make test-e2e             # run all E2E tests"
	@echo "  make test-e2e-chromium    # run E2E on Chromium only (use ARGS='-H -w 1')"
	@echo "  make test-mutation        # run mutation tests (mutmut)"
	@echo "  make stop-app             # stop Docker services"

# Run unit tests
test:
	$(UNIT)

# Run API tests (Postman/Newman)
test-api:
	$(API)

# Run E2E tests (Playwright)
test-e2e:
	$(PLAYWRIGHT)

# Run E2E tests on Chromium only (pass extra flags via ARGS, e.g., ARGS="-H -w 1")
test-e2e-chromium:
	$(PLAYWRIGHT) -b chromium $(ARGS)

# Run mypy type checking
test-typecheck:
	$(MYPY)

# Run mutation tests with mutmut (Python)
test-mutation:
	# Generate coverage baseline for --use-coverage
	$(PY) -m pytest -q --maxfail=1 --disable-warnings --cov=src $(PYTEST_FLAGS) || true
	$(PY) -m mutmut run --use-coverage --paths-to-mutate $(PATHS_TO_MUTATE) --tests-dir tests --runner "$(PY) -m pytest -q --maxfail=1 --disable-warnings --ignore=e2e-tests $(PYTEST_FLAGS)" || true
	$(PY) -m mutmut results

# Restart Docker services non-interactively
restart-app:
	printf "y\ny\n" | ./start-docker.sh

# Start Docker services non-interactively (alias)
start-app:
	printf "y\ny\n" | ./start-docker.sh

# Stop Docker services
stop-app:
	- $(DOCKER_COMPOSE) down || true
	- @echo "Stopped docker services (if running)"