.PHONY: help build up down restart logs test clean clean-all

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	docker-compose build

build-fresh: ## Clean everything and build from scratch
	@echo "Cleaning everything..."
	@make clean-all
	@echo "Building fresh Docker image..."
	docker-compose build --no-cache
	@echo "Fresh build complete"

up: ## Start the application
	docker-compose up

up-d: ## Start the application in detached mode
	docker-compose up -d

down: ## Stop the application
	docker-compose down

restart: ## Restart the application
	docker-compose restart

logs: ## Show application logs
	docker-compose logs -f

test: ## Run pytest tests
	python3 -m pytest

test-sqlite: ## Test SQLite implementation (Bonus 1)
	python3 -m pytest tests/test_sqlite_bonus.py -v

clean: ## Remove Docker containers and images
	docker-compose down -v --rmi all

clean-all: ## Complete cleanup (containers, volumes, images, networks, DB)
	@echo "Performing complete cleanup..."
	docker-compose down -v --rmi all --remove-orphans
	rm -f src/data/products.db src/data/products.db-journal
	rm -rf __pycache__ src/__pycache__ src/*/__pycache__ src/*/*/__pycache__ tests/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	@echo "Cleanup complete"

shell: ## Open shell in running container
	docker-compose exec agent-api /bin/bash

install: ## Install dependencies locally (for development)
	pip install -r requirements.txt
