#!/bin/bash

# Запуск проекта Contract Storage Service

echo "🚀 Starting Contract Storage Service..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    exit 1
fi

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    echo "📄 Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "⚠️  .env file not found, using defaults"
fi

# Запускаем контейнеры
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Ждем запуска базы данных
echo "⏳ Waiting for database to start..."
sleep 10

# Запускаем миграции
echo "🗄️  Running database migrations..."
docker-compose exec app alembic upgrade head

echo "✅ Contract Storage Service is running!"
echo "🌐 Web interface: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🗄️  MinIO console: http://localhost:9001 (admin/password)"
echo "🐘 PostgreSQL: localhost:5432 (postgres/postgres)"

echo ""
echo "To stop the service run: ./scripts/stop.sh"
