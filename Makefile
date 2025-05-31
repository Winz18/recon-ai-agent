# Makefile for Recon AI-Agent Docker operations

# Variables
IMAGE_NAME = recon-ai-agent
CONTAINER_NAME = recon-ai-agent-container
DOCKER_COMPOSE_FILE = docker-compose.yml

# Default domain for testing
DOMAIN ?= google.com
WORKFLOW ?= standard
OUTPUT ?= markdown
VERBOSITY ?= 1

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help build run clean stop logs shell test scan-quick scan-deep scan-stealth setup check-env

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)Recon AI-Agent Docker Management$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Environment Variables:$(NC)"
	@echo "  $(YELLOW)DOMAIN$(NC)     - Target domain (default: $(DOMAIN))"
	@echo "  $(YELLOW)WORKFLOW$(NC)   - Workflow type (default: $(WORKFLOW))"
	@echo "  $(YELLOW)OUTPUT$(NC)     - Output format (default: $(OUTPUT))"
	@echo "  $(YELLOW)VERBOSITY$(NC)  - Verbosity level (default: $(VERBOSITY))"
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make scan-quick DOMAIN=example.com"
	@echo "  make scan-deep DOMAIN=example.com OUTPUT=html"
	@echo "  make scan-stealth DOMAIN=example.com VERBOSITY=2"

setup: ## Create necessary directories and check prerequisites
	@echo "$(BLUE)Setting up Recon AI-Agent environment...$(NC)"
	@mkdir -p reports cache credentials
	@echo "$(GREEN)Created directories: reports, cache, credentials$(NC)"
	@make check-env

check-env: ## Check environment configuration
	@echo "$(BLUE)Checking environment configuration...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Warning: .env file not found$(NC)"; \
		echo "$(YELLOW)Create .env file with:$(NC)"; \
		echo "GOOGLE_PROJECT_ID=your-project-id"; \
		echo "GOOGLE_REGION=us-central1"; \
		echo "TARGET_DOMAIN=google.com"; \
	else \
		echo "$(GREEN)Found .env file$(NC)"; \
	fi
	@if [ ! -f credentials/service-account.json ]; then \
		echo "$(YELLOW)Warning: No service account key found in credentials/service-account.json$(NC)"; \
		echo "$(YELLOW)Either add the key or use Application Default Credentials$(NC)"; \
	else \
		echo "$(GREEN)Found service account key$(NC)"; \
	fi

build: ## Build the Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t $(IMAGE_NAME) .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

build-no-cache: ## Build the Docker image without cache
	@echo "$(BLUE)Building Docker image without cache...$(NC)"
	@docker build --no-cache -t $(IMAGE_NAME) .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

run: setup ## Run the application with custom parameters
	@echo "$(BLUE)Running Recon AI-Agent...$(NC)"
	@echo "$(YELLOW)Domain: $(DOMAIN)$(NC)"
	@echo "$(YELLOW)Workflow: $(WORKFLOW)$(NC)"
	@echo "$(YELLOW)Output: $(OUTPUT)$(NC)"
	@echo "$(YELLOW)Verbosity: $(VERBOSITY)$(NC)"
	@docker run --rm \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $$(pwd)/reports:/app/reports \
		-v $$(pwd)/cache:/app/cache \
		-v $$(pwd)/credentials:/app/credentials:ro \
		$(IMAGE_NAME) \
		python main.py -d $(DOMAIN) -w $(WORKFLOW) -o $(OUTPUT) -v $(VERBOSITY)

scan-quick: ## Run quick reconnaissance scan
	@make run WORKFLOW=quick

scan-deep: ## Run deep reconnaissance scan
	@make run WORKFLOW=deep

scan-comprehensive: ## Run comprehensive reconnaissance scan
	@make run WORKFLOW=comprehensive

scan-stealth: ## Run stealth reconnaissance scan
	@make run WORKFLOW=stealth

scan-targeted-ssl: ## Run targeted SSL/TLS scan
	@echo "$(BLUE)Running targeted SSL/TLS scan...$(NC)"
	@docker run --rm \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $$(pwd)/reports:/app/reports \
		-v $$(pwd)/cache:/app/cache \
		-v $$(pwd)/credentials:/app/credentials:ro \
		$(IMAGE_NAME) \
		python main.py -d $(DOMAIN) -w targeted --target-type ssl -o $(OUTPUT) -v $(VERBOSITY)

scan-targeted-web: ## Run targeted web application scan
	@echo "$(BLUE)Running targeted web application scan...$(NC)"
	@docker run --rm \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-v $$(pwd)/reports:/app/reports \
		-v $$(pwd)/cache:/app/cache \
		-v $$(pwd)/credentials:/app/credentials:ro \
		$(IMAGE_NAME) \
		python main.py -d $(DOMAIN) -w targeted --target-type web -o $(OUTPUT) -v $(VERBOSITY)

shell: ## Get shell access to the container
	@echo "$(BLUE)Starting interactive shell...$(NC)"
	@docker run --rm -it \
		--name $(CONTAINER_NAME)-shell \
		--env-file .env \
		-v $$(pwd)/reports:/app/reports \
		-v $$(pwd)/cache:/app/cache \
		-v $$(pwd)/credentials:/app/credentials:ro \
		$(IMAGE_NAME) \
		/bin/bash

test: ## Run application tests
	@echo "$(BLUE)Running tests...$(NC)"
	@docker run --rm \
		--name $(CONTAINER_NAME)-test \
		--env-file .env \
		$(IMAGE_NAME) \
		python -m pytest tests/ -v

help-app: ## Show application help
	@docker run --rm $(IMAGE_NAME) python main.py --help

help-workflows: ## Show workflow help
	@docker run --rm $(IMAGE_NAME) python main.py --help-workflows

compose-up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services with docker-compose...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"

compose-down: ## Stop services with docker-compose
	@echo "$(BLUE)Stopping services with docker-compose...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Services stopped!$(NC)"

compose-run: ## Run scan with docker-compose
	@echo "$(BLUE)Running scan with docker-compose...$(NC)"
	@docker-compose run --rm recon-ai-agent \
		python main.py -d $(DOMAIN) -w $(WORKFLOW) -o $(OUTPUT) -v $(VERBOSITY)

logs: ## View container logs
	@docker logs $(CONTAINER_NAME)

stop: ## Stop running container
	@echo "$(BLUE)Stopping container...$(NC)"
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@echo "$(GREEN)Container stopped!$(NC)"

clean: ## Remove container and image
	@echo "$(BLUE)Cleaning up...$(NC)"
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-all: ## Remove all containers, images, and volumes
	@echo "$(BLUE)Cleaning up everything...$(NC)"
	@docker-compose down -v 2>/dev/null || true
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@docker system prune -f
	@echo "$(GREEN)Complete cleanup finished!$(NC)"

show-reports: ## List generated reports
	@echo "$(BLUE)Generated reports:$(NC)"
	@ls -la reports/ 2>/dev/null || echo "$(YELLOW)No reports found$(NC)"

show-cache: ## Show cache information
	@echo "$(BLUE)Cache information:$(NC)"
	@du -sh cache/ 2>/dev/null || echo "$(YELLOW)No cache found$(NC)"
	@ls -la cache/ 2>/dev/null || true

size: ## Show image size
	@echo "$(BLUE)Docker image size:$(NC)"
	@docker images $(IMAGE_NAME) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

info: ## Show system information
	@echo "$(BLUE)System Information:$(NC)"
	@echo "$(YELLOW)Docker version:$(NC)"
	@docker --version
	@echo "$(YELLOW)Docker Compose version:$(NC)"
	@docker-compose --version
	@echo "$(YELLOW)Available disk space:$(NC)"
	@df -h . | tail -1
	@echo "$(YELLOW)Memory usage:$(NC)"
	@free -h 2>/dev/null || echo "Memory info not available"

update: ## Update the application and rebuild
	@echo "$(BLUE)Updating application...$(NC)"
	@git pull 2>/dev/null || echo "$(YELLOW)Not a git repository or no remote configured$(NC)"
	@make build
	@echo "$(GREEN)Update completed!$(NC)"

# Development targets
dev-build: ## Build development image with latest dependencies
	@echo "$(BLUE)Building development image...$(NC)"
	@docker build -t $(IMAGE_NAME):dev --target builder .

dev-shell: ## Start development shell
	@echo "$(BLUE)Starting development shell...$(NC)"
	@docker run --rm -it \
		--name $(CONTAINER_NAME)-dev \
		--env-file .env \
		-v $$(pwd):/app \
		-v $$(pwd)/reports:/app/reports \
		-v $$(pwd)/cache:/app/cache \
		-v $$(pwd)/credentials:/app/credentials:ro \
		$(IMAGE_NAME):dev \
		/bin/bash 