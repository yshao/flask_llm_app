# ============================================================================
# MAKEFILE FOR FLASK LLM APP DEPLOYMENT
# ============================================================================
# Orchestrates local deployment with Docker postgres and native Flask
# ============================================================================

# Use bash for shell commands
SHELL := /bin/bash

# -----------------------------------------------------------------------------
# Configuration Variables
# -----------------------------------------------------------------------------

PROJECT_DIR := $(shell pwd)
ENV_FILE := $(PROJECT_DIR)/.env
COMPOSE_FILE := $(PROJECT_DIR)/docker-compose-local.yml
COMPOSE_PROJECT := flask_llm_app

# Container names (from docker-compose-local.yml)
POSTGRES_CONTAINER := flask_llm_postgres

# Flask configuration (from .env)
FLASK_HOST := 127.0.0.1
FLASK_PORT := 8080
APP_URL := http://$(FLASK_HOST):$(FLASK_PORT)

# Database configuration (from .env)
DB_NAME := homework_db
DB_HOST := localhost
DB_USER := postgres
DB_PASSWORD := changeme
DB_PORT := 5432

# Python
PYTHON_CMD := python3

# PID file for background app
APP_PID_FILE := /tmp/flask_llm_app.pid

# Colors
COLOR_RESET := \033[0m
COLOR_GREEN := \033[32m
COLOR_RED := \033[31m
COLOR_YELLOW := \033[33m
COLOR_CYAN := \033[36m
COLOR_BLUE := \033[34m

# -----------------------------------------------------------------------------
# Phony Targets
# -----------------------------------------------------------------------------

.PHONY: help deploy start db-up db-down db-test db-ready db-init
.PHONY: app-start-bg app-stop app-status app-health app-restart
.PHONY: test test-app health stop clean logs

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------

help:
	@echo "$(COLOR_CYAN)Flask LLM App - Makefile Deployment Tool$(COLOR_RESET)"
	@echo ""
	@echo "Main targets:"
	@echo "  make deploy         Full deployment (db → init → app)"
	@echo "  make start          Alias for deploy"
	@echo "  make db-up          Start postgres docker"
	@echo "  make db-down        Stop postgres docker"
	@echo "  make db-init        Initialize database (run once)"
	@echo "  make db-test        Test database connection"
	@echo "  make app-start-bg   Start app in background"
	@echo "  make app-stop       Stop app"
	@echo "  make app-restart    Restart app"
	@echo "  make test           Run all tests"
	@echo "  make health         Full health check"
	@echo "  make logs           Show all logs"
	@echo "  make stop           Stop everything"
	@echo "  make clean          Remove containers and volumes"
	@echo ""

# -----------------------------------------------------------------------------
# Main Deployment
# -----------------------------------------------------------------------------

deploy: db-test-or-start db-init app-start-bg app-health
	@echo ""
	@echo "=============================================="
	@echo "$(COLOR_GREEN)✓ Deployment Complete$(COLOR_RESET)"
	@echo "=============================================="
	@echo "App URL: $(APP_URL)"
	@echo ""
	@echo "View logs: make logs"
	@echo "Stop: make stop"
	@echo ""

start: deploy

# -----------------------------------------------------------------------------
# Database Management
# -----------------------------------------------------------------------------

db-up:
	@echo "$(COLOR_CYAN)▶ [1/2]$(COLOR_RESET) Starting postgres container"
	@docker compose -f $(COMPOSE_FILE) up -d postgres
	@echo "$(COLOR_GREEN)✓ Container starting$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)▶ [2/2]$(COLOR_RESET) Waiting for database ready"
	@$(MAKE) --no-print-directory db-ready
	@echo "$(COLOR_GREEN)✓ Database is ready$(COLOR_RESET)"

db-down:
	@echo "$(COLOR_CYAN)▶ [1/1]$(COLOR_RESET) Stopping containers"
	@docker compose -f $(COMPOSE_FILE) down
	@echo "$(COLOR_GREEN)✓ Containers stopped$(COLOR_RESET)"

db-test:
	@echo "Testing database connection..."
	@if docker ps --filter "name=$(POSTGRES_CONTAINER)" --format "{{.Names}}" | grep -q "$(POSTGRES_CONTAINER)"; then \
		if docker exec $(POSTGRES_CONTAINER) pg_isready -U $(DB_USER) -d $(DB_NAME) > /dev/null 2>&1; then \
			echo "$(COLOR_GREEN)✓ Database is accepting connections$(COLOR_RESET)"; \
		else \
			echo "$(COLOR_RED)✗ ERROR: Database not ready$(COLOR_RESET)"; \
			exit 1; \
		fi \
	else \
		echo "$(COLOR_RED)✗ ERROR: Container not running$(COLOR_RESET)"; \
		echo "Start with: make db-up"; \
		exit 1; \
	fi

db-ready:
	@echo "Waiting for database..."
	@timeout=60; \
	until docker exec $(POSTGRES_CONTAINER) pg_isready -U $(DB_USER) -d $(DB_NAME) > /dev/null 2>&1; do \
		timeout=$$((timeout - 1)); \
		if [ $$timeout -le 0 ]; then \
			echo ""; \
			echo "$(COLOR_RED)✗ ERROR: Timeout waiting for database$(COLOR_RESET)"; \
			exit 1; \
		fi; \
		echo -n "."; \
		sleep 1; \
	done; \
	echo ""; \
	echo "$(COLOR_GREEN)✓ Database ready$(COLOR_RESET)"

db-init:
	@echo "$(COLOR_CYAN)▶ [1/1]$(COLOR_RESET) Initializing database (one-time setup)"
	@if docker ps --filter "name=$(POSTGRES_CONTAINER)" --format "{{.Names}}" | grep -q "$(POSTGRES_CONTAINER)"; then \
		if docker exec $(POSTGRES_CONTAINER) psql -U $(DB_USER) -d $(DB_NAME) -c "SELECT 1 FROM pg_extension WHERE extname='vector'" > /dev/null 2>&1; then \
			echo "$(COLOR_YELLOW)⚠ WARNING: Database already initialized (pgvector exists)$(COLOR_RESET)"; \
		else \
			docker compose -f $(COMPOSE_FILE) run --rm db-init; \
			echo "$(COLOR_GREEN)✓ Database initialized$(COLOR_RESET)"; \
		fi \
	else \
		echo "$(COLOR_RED)✗ ERROR: Database container not running$(COLOR_RESET)"; \
		echo "Start with: make db-up"; \
		exit 1; \
	fi

db-test-or-start:
	@echo "$(COLOR_CYAN)▶ [1/2]$(COLOR_RESET) Testing database connection"
	@if docker ps --filter "name=$(POSTGRES_CONTAINER)" --format "{{.Names}}" | grep -q "$(POSTGRES_CONTAINER)"; then \
		if docker exec $(POSTGRES_CONTAINER) pg_isready -U $(DB_USER) -d $(DB_NAME) > /dev/null 2>&1; then \
			echo "$(COLOR_GREEN)✓ Database already running and accessible$(COLOR_RESET)"; \
		else \
			echo "$(COLOR_YELLOW)⚠ WARNING: Container exists but not ready$(COLOR_RESET)"; \
			$(MAKE) --no-print-directory db-ready; \
		fi \
	else \
		echo "$(COLOR_YELLOW)⚠ WARNING: Database container not found$(COLOR_RESET)"; \
		echo ""; \
		echo "$(COLOR_CYAN)▶ [2/2]$(COLOR_RESET) Starting database"; \
		$(MAKE) --no-print-directory db-up; \
	fi

# -----------------------------------------------------------------------------
# Application Management
# -----------------------------------------------------------------------------

app-start-bg:
	@echo "$(COLOR_CYAN)▶ [1/2]$(COLOR_RESET) Checking if app running"
	@if [ -f "$(APP_PID_FILE)" ]; then \
		if kill -0 $$(cat $(APP_PID_FILE)) 2>/dev/null; then \
			echo "$(COLOR_YELLOW)⚠ WARNING: App already running (PID: $$(cat $(APP_PID_FILE)))$(COLOR_RESET)"; \
			$(MAKE) --no-print-directory app-status; \
			exit 0; \
		else \
			rm -f $(APP_PID_FILE); \
		fi \
	fi
	@echo "$(COLOR_CYAN)▶ [2/2]$(COLOR_RESET) Starting app in background"
	@cd $(PROJECT_DIR) && nohup $(PYTHON_CMD) app.py > /tmp/flask_app.log 2>&1 & echo $$! > $(APP_PID_FILE)
	@echo "$(COLOR_GREEN)✓ App started in background$(COLOR_RESET)"
	@sleep 3
	@$(MAKE) --no-print-directory app-health

app-stop:
	@echo "$(COLOR_CYAN)▶ [1/1]$(COLOR_RESET) Stopping app"
	@if [ -f "$(APP_PID_FILE)" ]; then \
		pid=$$(cat $(APP_PID_FILE)); \
		if kill -0 $$pid 2>/dev/null; then \
			kill $$pid; \
			rm -f $(APP_PID_FILE); \
			echo "$(COLOR_GREEN)✓ App stopped (PID: $$pid)$(COLOR_RESET)"; \
		else \
			rm -f $(APP_PID_FILE); \
		fi \
	else \
		echo "$(COLOR_YELLOW)⚠ WARNING: No PID file found (app may not be running)$(COLOR_RESET)"; \
	fi

app-restart: app-stop app-start-bg

app-status:
	@echo "App Status:"
	@if [ -f "$(APP_PID_FILE)" ]; then \
		pid=$$(cat $(APP_PID_FILE)); \
		if kill -0 $$pid 2>/dev/null; then \
			echo "$(COLOR_GREEN)✓ Running (PID: $$pid)$(COLOR_RESET)"; \
			echo "URL: $(APP_URL)"; \
		else \
			echo "$(COLOR_RED)✗ PID file exists but process dead$(COLOR_RESET)"; \
		fi \
	else \
		echo "$(COLOR_YELLOW)⚠ WARNING: Not running$(COLOR_RESET)"; \
	fi

app-health:
	@echo "Testing app at $(APP_URL)..."; \
	if command -v curl > /dev/null 2>&1; then \
		if curl -s -o /dev/null -w "%{http_code}" $(APP_URL) | grep -q "200\|302\|404"; then \
			echo "$(COLOR_GREEN)✓ App is responding$(COLOR_RESET)"; \
		else \
			echo "$(COLOR_YELLOW)⚠ WARNING: App not ready yet$(COLOR_RESET)"; \
		fi \
	else \
		echo "$(COLOR_YELLOW)⚠ WARNING: curl not available$(COLOR_RESET)"; \
	fi

# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------

test: db-test test-app
	@echo "$(COLOR_GREEN)✓ All tests passed$(COLOR_RESET)"

test-app:
	@echo "Testing app communication..."
	@if ! command -v curl > /dev/null 2>&1; then \
		echo "$(COLOR_RED)✗ ERROR: curl not installed$(COLOR_RESET)"; \
		exit 1; \
	fi
	@response_code=$$(curl -s -o /dev/null -w "%{http_code}" $(APP_URL)); \
	echo "Response: $$response_code"; \
	if echo "$$response_code" | grep -q "200\|302\|404"; then \
		echo "$(COLOR_GREEN)✓ App communication OK$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_RED)✗ ERROR: Unexpected response: $$response_code$(COLOR_RESET)"; \
		exit 1; \
	fi

health:
	@echo "=============================================="
	@echo "  SYSTEM HEALTH CHECK"
	@echo "=============================================="
	@echo ""
	@echo "1. Database:"
	@$(MAKE) --no-print-directory db-test > /dev/null 2>&1 && \
		echo "   ✓ Healthy" || echo "   ✗ Not healthy"
	@echo ""
	@echo "2. Application:"
	@$(MAKE) --no-print-directory test-app > /dev/null 2>&1 && \
		echo "   ✓ Healthy" || echo "   ✗ Not healthy"
	@echo ""

# -----------------------------------------------------------------------------
# Logs & Cleanup
# -----------------------------------------------------------------------------

logs:
	@echo "Showing combined logs (Ctrl+C to exit)..."
	@echo "==========================================="
	@echo "=== DATABASE LOGS ==="
	@docker logs -f $(POSTGRES_CONTAINER) 2>&1 &
	@LOG_PID=$$!; \
	echo ""; \
	echo "=== APP LOGS ==="; \
	tail -f /tmp/flask_app.log 2>/dev/null || echo "No app logs found"; \
	wait $$LOG_PID 2>/dev/null || true

stop: app-stop db-down
	@echo "$(COLOR_GREEN)✓ All services stopped$(COLOR_RESET)"

clean:
	@echo "$(COLOR_CYAN)▶ [1/2]$(COLOR_RESET) Stopping services"
	@$(MAKE) --no-print-directory stop > /dev/null 2>&1 || true
	@echo "$(COLOR_CYAN)▶ [2/2]$(COLOR_RESET) Removing containers and volumes"
	@docker compose -f $(COMPOSE_FILE) down -v
	@rm -f $(APP_PID_FILE)
	@echo "$(COLOR_GREEN)✓ Cleanup complete$(COLOR_RESET)"
