.PHONY: help install install-dev test test-unit test-integration test-all lint format type-check security clean docker-build docker-test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test: test-unit ## Run unit tests (default)

test-unit: ## Run unit tests only
	pytest tests/unit/ -v --cov=src --cov-report=term-missing -m "unit"

test-integration: ## Run integration tests only
	pytest tests/integration/ -v -m "integration and not slow"

test-slow: ## Run slow integration tests
	pytest tests/integration/ -v -m "slow"

test-all: ## Run all tests
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	pytest-watch tests/unit/ -- -v -m "unit"

lint: ## Run linting checks
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format: ## Format code
	black src/ tests/
	isort src/ tests/

type-check: ## Run type checking
	mypy src/ --ignore-missing-imports

security: ## Run security checks
	bandit -r src/ -f json
	safety check

quality: lint type-check security ## Run all quality checks

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

docker-build: ## Build Docker image
	docker build -t dam-firebase-mcp-server:latest .

docker-test: ## Test Docker image
	docker run --rm -v $(PWD)/credentials.json.example:/app/credentials.json dam-firebase-mcp-server:latest \
		python main.py --google-credentials /app/credentials.json --help

docker-run: ## Run Docker container
	docker run --rm -p 8000:8000 -v $(PWD)/credentials.json:/app/credentials.json dam-firebase-mcp-server:latest

docker-compose-up: ## Start with docker-compose
	docker-compose up --build

docker-compose-down: ## Stop docker-compose
	docker-compose down

coverage-html: ## Generate HTML coverage report
	pytest tests/ --cov=src --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

coverage-xml: ## Generate XML coverage report
	pytest tests/ --cov=src --cov-report=xml

dev-setup: install-dev ## Complete development setup
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make help' to see all available commands"