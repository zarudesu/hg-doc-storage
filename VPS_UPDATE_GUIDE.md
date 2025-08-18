# 🚀 Инструкция по обновлению на VPS

## Обновление с версии 1.0 до 2.0 (короткие ссылки)

### ⚠️ ВАЖНО: Создание бэкапа

**Перед обновлением обязательно создайте бэкап!**

```bash
# Подключитесь к VPS
ssh zardes@dochealthgardenru

# Перейдите в папку проекта
cd /opt/hg-doc-storage

# 1. Создайте бэкап базы данных
docker-compose exec db pg_dump -U postgres contract_db > backup_before_v2_$(date +%Y%m%d_%H%M%S).sql

# 2. Создайте бэкап MinIO данных
docker run --rm \
  -v hg-doc-storage_minio_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/minio_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# 3. Создайте бэкап .env файла
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

echo "✅ Бэкапы созданы"
ls -la backup_* .env.backup.*
```

### 🔄 Процедура обновления

```bash
# 1. Остановите текущие сервисы
docker-compose down

# 2. Получите обновления из Git
git pull origin main

# 3. ВАЖНО: Обновите .env файл для вашего домена
# Замените yourcompany.ru на ваш реальный домен (например, doc.healthgarden.ru)
nano .env

# Найдите строку:
# BASE_URL=https://doc.yourcompany.ru
# Измените на ваш домен:
# BASE_URL=https://doc.healthgarden.ru

# 4. Обновите nginx конфигурацию для вашего домена
nano nginx/nginx.conf

# Найдите строки:
# server_name doc.yourcompany.ru;
# Замените на ваш домен:
# server_name doc.healthgarden.ru;

# 5. Запустите обновление
./deploy.sh

# 6. Проверьте что миграция прошла успешно
docker-compose exec db psql -U postgres -d contract_db -c "\\d contracts" | grep short_id

# Вы должны увидеть строку с short_id
# Если не видите - миграция не выполнилась, обратитесь за помощью
```

### ✅ Проверка работоспособности

```bash
# 1. Проверьте статус всех сервисов
docker-compose ps

# Все сервисы должны быть в состоянии "Up"

# 2. Проверьте health check
curl http://localhost:8000/health

# Должен вернуть статус "healthy"

# 3. Проверьте что API отвечает (замените на ваш API ключ)
curl -H "Authorization: Bearer ВАШ_API_КЛЮЧ" \
     http://localhost:8000/api/v1/status/test-uuid

# Должен вернуть 404 (это нормально, UUID не существует)
# Если 401 - проблема с API ключом
# Если 500 - проблема с сервисом
```

### 🧪 Полное тестирование (опционально)

```bash
# Если хотите протестировать новую функциональность:

# 1. Обновите тестовый скрипт с вашим доменом и API ключом
nano test_short_links.sh

# Найдите строки:
# API_BASE="${API_BASE:-https://doc.yourcompany.ru}"
# API_KEY="${API_KEY:-your-api-key-here}"

# Замените на ваши данные:
# API_BASE="${API_BASE:-https://doc.healthgarden.ru}"
# API_KEY="${API_KEY:-ваш-реальный-api-ключ}"

# 2. Запустите тест
./test_short_links.sh
```

### 📱 Настройка SSL для нового домена (если нужно)

```bash
# Если используете новый домен, обновите SSL сертификаты:

# 1. Получите новые сертификаты
sudo certbot certonly --standalone -d doc.healthgarden.ru

# 2. Скопируйте в проект
sudo cp /etc/letsencrypt/live/doc.healthgarden.ru/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/doc.healthgarden.ru/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem

# 3. Перезапустите nginx
docker-compose restart nginx
```

### ⚠️ В случае проблем - откат к версии 1.0

```bash
# Если что-то пошло не так, откатитесь к предыдущей версии:

# 1. Остановите сервисы
docker-compose down

# 2. Откатите Git к предыдущей версии
git log --oneline -5  # Посмотрите последние коммиты
git checkout HEAD~1   # Откатитесь на 1 коммит назад

# 3. Восстановите .env
cp .env.backup.ДАТА_БЭКАПА .env

# 4. Восстановите базу данных
docker-compose up -d db
docker-compose exec -T db psql -U postgres -d contract_db < backup_before_v2_ДАТА.sql

# 5. Запустите старую версию
./deploy.sh
```

### 🎉 После успешного обновления

#### Что изменилось для 1С:

1. **API ответы теперь содержат короткие ссылки:**
```json
{
  "contract_id": "uuid-here",
  "short_id": "abc12345",
  "short_url": "https://doc.healthgarden.ru/abc12345"
}
```

2. **Новый workflow с одной ссылкой:**
```
1С загружает файл → получает short_url
Отправляете short_url клиенту в SMS
Клиент скачивает оригинал по ссылке
После подписания загружаете подписанный файл
Клиент переходит по той же ссылке → получает подписанную версию!
```

3. **Все старые API продолжают работать**
- Существующие интеграции не сломаются
- Можете постепенно переходить на новые возможности

### 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи:**
```bash
docker-compose logs -f app
```

2. **Перезапустите сервисы:**
```bash
docker-compose restart app
```

3. **Обратитесь за помощью:**
- Telegram: укажите что именно не работает
- Email: приложите логи и описание проблемы

### 🔍 Проверочный список

- [ ] Бэкапы созданы
- [ ] Git обновлен
- [ ] .env файл обновлен с правильным доменом
- [ ] nginx.conf обновлен с правильным доменом  
- [ ] Миграция БД выполнилась (есть поле short_id)
- [ ] Все сервисы запущены
- [ ] Health check отвечает
- [ ] SSL сертификаты обновлены (если нужно)
- [ ] Тестирование прошло успешно

**После выполнения всех пунктов система готова к использованию с короткими ссылками! 🚀**
