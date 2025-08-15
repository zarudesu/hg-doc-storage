#!/bin/bash

# 🚀 Production deployment script для 1C Contract Service

set -e

echo "🏥 Deploying 1C Contract Service to Production"
echo "=============================================="

# Проверка что мы в правильной директории
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Run from project root directory."
    exit 1
fi

# Проверка переменных окружения
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "📋 Please copy .env.example to .env and configure:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your production values"
    exit 1
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    exit 1
fi

# Загружаем переменные окружения
source .env

# Проверка обязательных переменных
if [ "$API_KEY" = "CHANGE_THIS_API_KEY_FOR_1C_INTEGRATION" ]; then
    echo "❌ Error: Please change API_KEY in .env file!"
    exit 1
fi

if [ "$POSTGRES_PASSWORD" = "CHANGE_THIS_PASSWORD" ]; then
    echo "❌ Error: Please change POSTGRES_PASSWORD in .env file!"
    exit 1
fi

echo "✅ Environment variables validated"

# Создание backup директории
mkdir -p backups

# Backup существующих данных (если есть)
if docker volume ls | grep -q "hg-doc-storage_postgres_data"; then
    echo "📦 Creating database backup..."
    docker-compose exec -T db pg_dump -U postgres contract_db > "backups/db_backup_$(date +%Y%m%d_%H%M%S).sql" || true
fi

# Остановка старых контейнеров
echo "🛑 Stopping existing containers..."
docker-compose down

# Сборка новых образов
echo "🔨 Building application image..."
docker-compose build --no-cache app

# Запуск базы данных и MinIO
echo "🗄️ Starting database and storage..."
docker-compose up -d db minio

# Ожидание готовности БД
echo "⏳ Waiting for database to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker-compose exec -T db pg_isready -U postgres -d contract_db; then
        echo "✅ Database is ready"
        break
    fi
    sleep 2
    ((timeout--))
done

if [ $timeout -eq 0 ]; then
    echo "❌ Database failed to start within 2 minutes"
    exit 1
fi

# Выполнение миграций
echo "🗄️ Running database migrations..."
docker-compose run --rm app alembic upgrade head

# Запуск приложения
echo "🚀 Starting application..."
docker-compose up -d app

# Ожидание готовности приложения
echo "⏳ Waiting for application to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo "✅ Application is ready"
        break
    fi
    sleep 2
    ((timeout--))
done

if [ $timeout -eq 0 ]; then
    echo "❌ Application failed to start within 2 minutes"
    echo "📋 Check logs: docker-compose logs app"
    exit 1
fi

# Опционально запуск Nginx (если нужен reverse proxy)
read -p "🌐 Start Nginx reverse proxy? (y/N): " start_nginx
if [[ $start_nginx =~ ^[Yy]$ ]]; then
    if [ ! -f "nginx/ssl/cert.pem" ]; then
        echo "⚠️ Warning: SSL certificates not found in nginx/ssl/"
        echo "📋 Please add your SSL certificates to nginx/ssl/ directory"
        echo "   - cert.pem (certificate)"
        echo "   - key.pem (private key)"
    fi
    docker-compose --profile production up -d nginx
    echo "✅ Nginx started"
fi

# Проверка статуса всех сервисов
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Service URLs:"
echo "   Health Check: http://localhost:8000/health"
echo "   API Base URL: $BASE_URL"
echo "   MinIO Console: http://localhost:9001"
echo ""
echo "🔐 Security Information:"
echo "   API Key: $API_KEY"
echo "   Environment: $ENVIRONMENT"
echo ""
echo "📋 Next Steps:"
echo "1. Test the API with your 1C integration"
echo "2. Configure your domain DNS to point to this server"
echo "3. Set up SSL certificates in nginx/ssl/ if using Nginx"
echo "4. Configure backup strategy for volumes"
echo "5. Set up monitoring and alerting"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker-compose logs -f app"
echo "   Stop service: docker-compose down"
echo "   Backup database: docker-compose exec db pg_dump -U postgres contract_db > backup.sql"
echo ""
echo "⚠️ Important: Keep your .env file secure and backed up!"
