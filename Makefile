# 🏥 1C Contract Service - Production Makefile

.PHONY: help build test deploy clean logs backup restore security-check

# Default target
help: ## 📋 Show this help message
	@echo "🏥 1C Contract Service - Production Commands"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 🔧 Development commands
dev-setup: ## 🔧 Setup development environment
	@echo "🔧 Setting up development environment..."
	cp .env.example .env
	@echo "📝 Please edit .env file with your settings"
	@echo "✅ Development setup complete"

dev-start: ## 🚀 Start development environment
	@echo "🚀 Starting development environment..."
	docker-compose up -d db minio
	@echo "⏳ Waiting for services..."
	sleep 10
	docker-compose run --rm app alembic upgrade head
	docker-compose up app

test: ## 🧪 Run tests
	@echo "🧪 Running tests..."
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down

test-local: ## 🧪 Run tests locally (requires Python)
	@echo "🧪 Running tests locally..."
	pytest tests/ -v --cov=app --cov-report=html
	@echo "📊 Coverage report: htmlcov/index.html"

# 🚀 Production commands
build: ## 🔨 Build production Docker image
	@echo "🔨 Building production image..."
	docker-compose build --no-cache app

deploy: ## 🚀 Deploy to production
	@echo "🚀 Deploying to production..."
	@if [ ! -f .env ]; then echo "❌ .env file not found!"; exit 1; fi
	./deploy.sh

quick-deploy: ## ⚡ Quick deploy (no rebuild)
	@echo "⚡ Quick deployment..."
	docker-compose up -d

start: ## ▶️ Start all services
	@echo "▶️ Starting all services..."
	docker-compose up -d

stop: ## ⏹️ Stop all services
	@echo "⏹️ Stopping all services..."
	docker-compose down

restart: ## 🔄 Restart all services
	@echo "🔄 Restarting all services..."
	docker-compose restart

# 📊 Monitoring commands
logs: ## 📋 Show application logs
	docker-compose logs -f app

logs-all: ## 📋 Show all services logs
	docker-compose logs -f

status: ## 📊 Show services status
	@echo "📊 Services Status:"
	docker-compose ps
	@echo ""
	@echo "🔍 Health Checks:"
	@curl -s http://localhost:8000/health | jq '.' || echo "❌ App not responding"

health: ## 🏥 Health check
	@echo "🏥 Health Check..."
	@curl -f http://localhost:8000/health && echo "✅ Service is healthy" || echo "❌ Service is unhealthy"

# 💾 Backup commands
backup: ## 💾 Create full backup
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@echo "📊 Backing up database..."
	docker-compose exec -T db pg_dump -U postgres contract_db > "backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql"
	@echo "📁 Backing up files..."
	docker run --rm -v hg-doc-storage_minio_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/files_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz /data
	@echo "✅ Backup completed"

backup-db: ## 💾 Backup database only
	@echo "💾 Backing up database..."
	@mkdir -p backups
	docker-compose exec -T db pg_dump -U postgres contract_db > "backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql"
	@echo "✅ Database backup completed"

restore-db: ## 🔄 Restore database (requires BACKUP_FILE=path)
	@if [ -z "$(BACKUP_FILE)" ]; then echo "❌ Usage: make restore-db BACKUP_FILE=backups/db_backup_YYYYMMDD.sql"; exit 1; fi
	@echo "🔄 Restoring database from $(BACKUP_FILE)..."
	docker-compose exec -T db psql -U postgres contract_db < $(BACKUP_FILE)
	@echo "✅ Database restored"

# 🧹 Maintenance commands
clean: ## 🧹 Clean up Docker resources
	@echo "🧹 Cleaning up..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed"

clean-logs: ## 🧹 Clean application logs
	@echo "🧹 Cleaning logs..."
	docker-compose exec app find /app/logs -name "*.log" -type f -delete || true
	@echo "✅ Logs cleaned"

update: ## 🔄 Update and restart services
	@echo "🔄 Updating services..."
	git pull
	docker-compose pull
	docker-compose up -d --remove-orphans
	@echo "✅ Update completed"

# 🔒 Security commands
security-check: ## 🔒 Run security checks
	@echo "🔒 Running security checks..."
	@echo "📋 Checking Docker image..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD):/tmp/app aquasec/trivy image hg-doc-storage_app:latest
	@echo "📋 Checking filesystem..."
	docker run --rm -v $(PWD):/tmp/app aquasec/trivy fs /tmp/app

check-env: ## 🔍 Check environment configuration
	@echo "🔍 Checking environment configuration..."
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		if grep -q "CHANGE_THIS" .env; then \
			echo "⚠️ Warning: Default values found in .env file"; \
			grep "CHANGE_THIS" .env; \
		else \
			echo "✅ .env file configured"; \
		fi; \
	else \
		echo "❌ .env file not found"; \
	fi

# 📈 Performance commands
benchmark: ## 📈 Run performance benchmark
	@echo "📈 Running performance benchmark..."
	@if command -v hey >/dev/null 2>&1; then \
		hey -n 100 -c 10 http://localhost:8000/health; \
	else \
		echo "❌ 'hey' tool not found. Install with: go install github.com/rakyll/hey@latest"; \
	fi

# 🛠️ Development utilities
shell: ## 🐚 Open shell in app container
	docker-compose exec app /bin/sh

db-shell: ## 🗄️ Open database shell
	docker-compose exec db psql -U postgres contract_db

generate-api-key: ## 🔑 Generate secure API key
	@echo "🔑 Generated API key:"
	@openssl rand -base64 32

# 📋 Information commands
info: ## ℹ️ Show system information
	@echo "ℹ️ System Information:"
	@echo "===================="
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo "Current directory: $(PWD)"
	@echo "Git branch: $(shell git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo "Git commit: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
	@echo ""
	@echo "📊 Container Stats:"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" || true

ports: ## 🌐 Show service ports
	@echo "🌐 Service Ports:"
	@echo "==============="
	@echo "App:          http://localhost:8000"
	@echo "Database:     postgresql://localhost:5432"
	@echo "MinIO:        http://localhost:9000"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Nginx:        http://localhost:80 (if enabled)"
