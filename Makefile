# TTS CLI Development Makefile

.PHONY: help test test-cov test-fast lint format type-check quality clean install dev

help: ## Show this help message
	@echo "TTS CLI Development Commands:"
	@echo "============================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

test: ## Run all tests
	@echo "🧪 Running all tests..."
	python3 -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	@echo "📊 Running tests with coverage..."
	python3 -m pytest tests/ --cov=tts_cli --cov-report=term-missing --cov-report=html:htmlcov

test-fast: ## Run tests quickly (no coverage)
	@echo "⚡ Running fast tests..."
	python3 -m pytest tests/ -x -q

lint: ## Run linting with ruff
	@echo "🔍 Running linter..."
	ruff check tts_cli/ tests/

format: ## Format code with black
	@echo "🎨 Formatting code..."
	black tts_cli/ tests/ --line-length 100

type-check: ## Run type checking with mypy
	@echo "🔎 Running type checker..."
	mypy tts_cli/

quality: format lint type-check ## Run all code quality checks
	@echo "✨ All quality checks completed!"

clean: ## Clean up build artifacts and cache
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__ .pytest_cache htmlcov .coverage .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

install: ## Install package with pipx
	@echo "📦 Installing with pipx..."
	./setup.sh install

dev: ## Install in development mode
	@echo "🛠️  Installing in development mode..."
	./setup.sh dev

# Test shortcuts
unit: ## Run unit tests only
	python3 -m pytest tests/ -m "unit or not integration" -v

integration: ## Run integration tests only  
	python3 -m pytest tests/ -m "integration" -v

config-tests: ## Run configuration tests only
	python3 -m pytest tests/test_config.py -v

audio-tests: ## Run audio utility tests only
	python3 -m pytest tests/test_audio_utils.py -v