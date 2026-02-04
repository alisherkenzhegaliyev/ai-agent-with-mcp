.PHONY: help build up down restart logs test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	docker-compose build

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

test-cov: ## Run tests with coverage
	python3 -m pytest --cov=src --cov-report=html

clean: ## Remove Docker containers and images
	docker-compose down -v --rmi all

shell: ## Open shell in running container
	docker-compose exec agent-api /bin/bash

install: ## Install dependencies locally (for development)
	pip install -r requirements.txt
