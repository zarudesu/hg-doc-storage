#!/bin/bash

# Остановка проекта Contract Storage Service

echo "🛑 Stopping Contract Storage Service..."

# Останавливаем контейнеры
docker-compose down

echo "✅ Contract Storage Service stopped!"
echo ""
echo "To completely remove all data run: docker-compose down -v"
