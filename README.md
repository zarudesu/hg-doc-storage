# 🔒 1C Contract Service - Production Ready

Защищенный сервис для приема файлов от 1С с API ключами и безопасным хранением данных.

## 🎯 Основные возможности

- **🔐 API Key защита** - все операции защищены Bearer токенами
- **🛡️ Защита персональных данных** - хеширование client_id и signer_id
- **📊 Rate limiting** - защита от DDoS атак  
- **🔍 Аудит логи** - полное логирование всех операций
- **🐳 Production Docker** - готовая сборка для продакшена
- **🌐 Nginx proxy** - SSL терминация и балансировка нагрузки

## 🚀 Production Deployment

### 1. Клонирование и настройка
```bash
git clone https://github.com/zarudesu/hg-doc-storage.git
cd hg-doc-storage

# Настройка переменных окружения
cp .env.example .env
nano .env  # Измените все секретные ключи!
```

### 2. Обязательная настройка безопасности
```bash
# В .env файле обязательно измените:
API_KEY=your-super-secret-api-key-32-chars-min
POSTGRES_PASSWORD=your-strong-database-password
MINIO_SECRET_KEY=your-strong-minio-password
BASE_URL=https://your-domain.com
```

### 3. Запуск в продакшене
```bash
./deploy.sh
```

### 4. Настройка SSL (опционально)
```bash
# Для HTTPS с SSL сертификатами
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Копируем сертификаты
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem

# Запускаем с Nginx и SSL
docker-compose --profile production up -d
```

### 5. Проверка
```bash
curl -H "Authorization: Bearer your-api-key" \
     https://your-domain.com/health
```

## 🔐 API Security

### Защищенные endpoints (требуют API ключ):
```bash
# Загрузка файлов от 1С
POST /api/v1/upload
POST /api/v1/sign/{id}
GET  /api/v1/status/{id}

# Заголовок авторизации обязателен:
Authorization: Bearer your-api-key
```

### Публичные endpoints (по UUID):
```bash
# Скачивание файлов клиентами
GET /api/v1/download/{uuid}/original
GET /api/v1/download/{uuid}/signed
```

## 📋 Защищенный API Usage

### 1. Загрузка оригинала (1С)
```bash
curl -X POST "https://your-domain.com/api/v1/upload" \
  -H "Authorization: Bearer your-api-key" \
  -F "client_id=CLIENT_001_HASH" \
  -F "contract_type=surgery" \
  -F "file=@contract.pdf"

Response:
{
  "contract_id": "uuid-here",
  "file_url": "https://your-domain.com/api/v1/download/uuid/original"
}
```

### 2. Загрузка подписанного (1С)
```bash
curl -X POST "https://your-domain.com/api/v1/sign/{uuid}" \
  -H "Authorization: Bearer your-api-key" \
  -F "signer_id=DOCTOR_001_HASH" \
  -F "file=@signed.pdf"

Response:
{
  "contract_id": "uuid-here", 
  "signed_file_url": "https://your-domain.com/api/v1/download/uuid/signed"
}
```

### 3. Скачивание (публично по UUID)
```bash
# Клиент скачивает без API ключа
curl "https://your-domain.com/api/v1/download/{uuid}/signed" \
  -o contract.pdf
```

## 🛡️ Безопасность данных

### Защита персональных данных:
- **Хеширование**: client_id и signer_id хешируются перед сохранением
- **UUID ссылки**: файлы доступны только по неугадываемым идентификаторам  
- **No-cache headers**: файлы не кешируются браузерами
- **Secure headers**: защита от XSS, clickjacking, etc.

### Пример хеширования в 1С:
```python
# В API отправляются хешированные данные
client_id = f"CLIENT_{hash('Иванов И.И.') % 1000000:06d}"
signer_id = f"SIGNER_{hash('Доктор Петров') % 1000000:06d}"
```

## 🏗️ Production Architecture

```
Internet → Nginx (SSL, Rate Limiting) → FastAPI App → PostgreSQL
                                                    → MinIO Storage
```

### Компоненты:
- **FastAPI**: Async веб-сервер с автодокументацией
- **PostgreSQL 15**: Надежная БД для метаданных
- **MinIO**: S3-совместимое объектное хранилище
- **Nginx**: Reverse proxy с SSL и rate limiting
- **Docker**: Полная контейнеризация

## 📊 Мониторинг и логи

### Логирование:
```bash
# Просмотр логов приложения
docker-compose logs -f app

# Логи базы данных
docker-compose logs -f db

# Логи Nginx
docker-compose logs -f nginx
```

### Метрики для мониторинга:
- Request rate и response times
- Database connection pool
- File upload/download volumes
- Error rates по статус кодам
- Security events (неверные API ключи)

## 🔧 Операционные команды

### Backup:
```bash
# Backup базы данных
docker-compose exec db pg_dump -U postgres contract_db > backup.sql

# Backup файлов MinIO
docker run --rm -v hg-doc-storage_minio_data:/data \
  alpine tar czf /backup/minio-$(date +%Y%m%d).tar.gz /data
```

### Восстановление:
```bash
# Restore базы данных
docker-compose exec -T db psql -U postgres contract_db < backup.sql

# Масштабирование приложения
docker-compose up -d --scale app=3
```

### Обновление:
```bash
# Обновление с сохранением данных
git pull
docker-compose build --no-cache app
docker-compose up -d app
```

## 🚨 Security Checklist

### Перед продакшеном:
- [ ] Изменен API_KEY на криптостойкий (32+ символов)
- [ ] Изменены все пароли БД и MinIO
- [ ] Настроен BASE_URL на реальный домен
- [ ] Добавлены SSL сертификаты в nginx/ssl/
- [ ] Настроен ALLOWED_IPS whitelist (если нужно)
- [ ] Отключены debug endpoints (/docs, /redoc)
- [ ] Настроено логирование и мониторинг
- [ ] Настроены backup процедуры

### Рекомендации:
- Используйте WAF (Web Application Firewall)
- Настройте автоматические backup
- Мониторинг с алертами (Prometheus/Grafana)
- Ротация логов
- Регулярные security updates

## 🔗 Интеграция с 1С

### Python пример:
```python
import requests

class ContractAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {api_key}'}
    
    def upload_contract(self, client_data, pdf_path):
        # Хешируем персональные данные
        client_id = f"CLIENT_{hash(client_data) % 1000000:06d}"
        
        with open(pdf_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/upload",
                headers=self.headers,
                data={'client_id': client_id, 'contract_type': 'surgery'},
                files={'file': f}
            )
        return response.json()
```

## 🆘 Troubleshooting

### Частые проблемы:

**401 Unauthorized:**
- Проверьте API ключ в заголовке Authorization
- Убедитесь что ключ не содержит лишних пробелов

**403 Forbidden:**
- Проверьте IP whitelist в ALLOWED_IPS
- Убедитесь что запрос идет с разрешенного IP

**File upload errors:**
- Проверьте размер файла (MAX_FILE_SIZE)
- Убедитесь что файл имеет расширение .pdf

**Database connection errors:**
- Проверьте статус контейнера: `docker-compose ps`
- Проверьте логи: `docker-compose logs db`

## 📞 Поддержка

Для вопросов по развертыванию и настройке создавайте issues в репозитории проекта.

---

**Версия**: 1.0.0 Production  
**Лицензия**: MIT  
**Репозиторий**: https://github.com/zarudesu/hg-doc-storage
