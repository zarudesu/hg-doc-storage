# ⚡ Быстрый старт - Короткие ссылки v2.0

## 🚀 Развертывание обновления

### 1. Остановить текущие сервисы
```bash
cd /opt/hg-doc-storage
docker-compose down
```

### 2. Получить обновления
```bash
git pull origin main
```

### 3. Обновить конфигурацию
```bash
# Проверить .env файл
cat .env | grep BASE_URL

# Если не doc.yourcompany.ru, то обновить:
sed -i 's/your-domain.com/doc.yourcompany.ru/g' .env
sed -i 's/https:\/\/.*$/https:\/\/doc.yourcompany.ru/g' .env
```

### 4. Запустить развертывание
```bash
./deploy.sh
```

### 5. Проверить работу
```bash
# Базовая проверка
curl https://doc.yourcompany.ru/health

# Полное тестирование
./test_short_links.sh
```

---

## 📎 Использование коротких ссылок

### Пример интеграции с 1С

#### 1. Загрузка оригинала
```http
POST https://doc.yourcompany.ru/api/v1/upload
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data

client_id=CLIENT_123
contract_type=surgery
file=@contract.pdf
```

**Ответ:**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "short_id": "abc12345", 
  "short_url": "https://doc.yourcompany.ru/abc12345"
}
```

#### 2. Отправка SMS клиенту
```
Договор готов к подписанию: https://doc.yourcompany.ru/abc12345
```

#### 3. Клиент скачивает оригинал
```
GET https://doc.yourcompany.ru/abc12345
→ Возвращает оригинальный файл
```

#### 4. Загрузка подписанного файла
```http
POST https://doc.yourcompany.ru/api/v1/sign/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer YOUR_API_KEY

signer_id=SIGNER_456
file=@signed_contract.pdf
```

**Ответ (та же ссылка!):**
```json
{
  "short_url": "https://doc.yourcompany.ru/abc12345"
}
```

#### 5. Клиент скачивает подписанный файл
```
GET https://doc.yourcompany.ru/abc12345
→ Теперь возвращает подписанный файл!
```

---

## 🔧 Быстрая диагностика

### Проверить статус сервисов
```bash
docker-compose ps
```

### Проверить логи
```bash
# Приложение
docker-compose logs -f app | tail -20

# База данных  
docker-compose logs db | grep -i error

# Nginx
docker-compose logs nginx | grep -i error
```

### Проверить миграцию БД
```bash
docker-compose exec db psql -U postgres -d contract_db -c "\d contracts" | grep short_id
```

### Тестирование API
```bash
# Health check
curl https://doc.yourcompany.ru/health

# Тест авторизации (должно вернуть 401)
curl https://doc.yourcompany.ru/api/v1/status/test

# Тест с авторизацией
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://doc.yourcompany.ru/api/v1/status/550e8400-e29b-41d4-a716-446655440000
```

---

## 📱 SMS шаблоны

### Для оригинала
```
Договор готов к подписанию: https://doc.yourcompany.ru/abc12345
```

### После подписания  
```
Договор подписан: https://doc.yourcompany.ru/abc12345
```

### Универсальный
```
Ваш договор: https://doc.yourcompany.ru/abc12345
Ссылка автоматически показывает актуальную версию.
```

---

## ⚠️ Важные моменты

### Обратная совместимость
✅ Все старые API работают  
✅ Существующие интеграции не сломаются  
✅ Полные UUID поддерживаются  

### Безопасность
✅ Короткие ID уникальны (2.8 триллиона комбинаций)  
✅ Rate limiting на скачивание  
✅ Логирование всех операций  

### Производительность
✅ Кэширование подписанных файлов  
✅ Оптимизированные запросы к БД  
✅ CDN-ready заголовки  

---

## 📞 Поддержка

**Если что-то не работает:**

1. **Проверить логи:** `docker-compose logs -f app`
2. **Перезапустить:** `docker-compose restart app`  
3. **Откатить:** `git checkout HEAD~1 && ./deploy.sh`
4. **Обратиться:** zardes@dochealthgardenru

**Полезные ссылки:**
- [Подробное руководство](docs/SHORT_LINKS_GUIDE.md)
- [API спецификация](docs/1C_API_SPECIFICATION.md)  
- [Примеры CURL](docs/CURL_EXAMPLES.md)
- [Changelog](CHANGELOG.md)

---

**🎉 Готово! Система с короткими ссылками запущена и готова к использованию.**
