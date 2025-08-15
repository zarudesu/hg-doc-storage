# 📋 API Спецификация для интеграции с 1С

## 🔗 Базовые параметры подключения

**Base URL:** `https://contracts.your-domain.com`  
**Авторизация:** Bearer Token в заголовке `Authorization`  
**Content-Type:** `multipart/form-data` для загрузки файлов  
**Timeout:** Рекомендуемый 30 секунд  

---

## 🔐 Авторизация

Все защищенные endpoints требуют заголовок:
```http
Authorization: Bearer YOUR_API_KEY_HERE
```

❌ **401 Unauthorized** - неверный API ключ  
❌ **403 Forbidden** - IP не в whitelist (если включен)  
❌ **429 Too Many Requests** - превышен лимит (100 req/min)

---

## 📡 API Endpoints

### 1. 🔒 POST /api/v1/upload
**Назначение:** Загрузка оригинального договора от 1С

**Заголовки:**
```http
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data
```

**Параметры формы:**
- `client_id` (string, required) - Хешированный ID клиента
- `contract_type` (string, required) - Тип договора
- `file` (file, required) - PDF файл

**Пример запроса:**
```http
POST /api/v1/upload
Authorization: Bearer abc123...
Content-Type: multipart/form-data

--boundary123
Content-Disposition: form-data; name="client_id"

CLIENT_456789
--boundary123
Content-Disposition: form-data; name="contract_type"

surgery
--boundary123
Content-Disposition: form-data; name="file"; filename="contract.pdf"
Content-Type: application/pdf

[PDF binary data]
--boundary123--
```

**Успешный ответ (200):**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_url": "https://contracts.your-domain.com/api/v1/download/550e8400-e29b-41d4-a716-446655440000/original",
  "message": "File uploaded successfully"
}
```

**Ошибки:**
- `400` - Неправильный тип файла или размер > 50MB
- `401` - Неверный API ключ
- `500` - Внутренняя ошибка сервера

---

### 2. 🔒 POST /api/v1/sign/{contract_id}
**Назначение:** Загрузка подписанного договора

**URL параметры:**
- `contract_id` (UUID) - ID договора из предыдущего запроса

**Заголовки:**
```http
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data
```

**Параметры формы:**
- `signer_id` (string, required) - Хешированный ID подписавшего
- `file` (file, required) - Подписанный PDF файл

**Пример запроса:**
```http
POST /api/v1/sign/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer abc123...
Content-Type: multipart/form-data

--boundary123
Content-Disposition: form-data; name="signer_id"

SIGNER_789123
--boundary123
Content-Disposition: form-data; name="file"; filename="signed.pdf"
Content-Type: application/pdf

[Signed PDF binary data]
--boundary123--
```

**Успешный ответ (200):**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "signed_file_url": "https://contracts.your-domain.com/api/v1/download/550e8400-e29b-41d4-a716-446655440000/signed",
  "message": "File signed successfully"
}
```

**Ошибки:**
- `400` - Договор уже подписан или неправильный файл
- `404` - Договор не найден
- `401` - Неверный API ключ

---

### 3. 🔒 GET /api/v1/status/{contract_id}
**Назначение:** Получение статуса договора

**Заголовки:**
```http
Authorization: Bearer YOUR_API_KEY
```

**Успешный ответ (200):**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "CLIENT_456789",
  "contract_type": "surgery",
  "status": "signed",
  "original_file_url": "https://contracts.your-domain.com/api/v1/download/550e8400-e29b-41d4-a716-446655440000/original",
  "signed_file_url": "https://contracts.your-domain.com/api/v1/download/550e8400-e29b-41d4-a716-446655440000/signed",
  "created_at": "2025-08-15T10:30:00Z",
  "signed_at": "2025-08-15T11:45:00Z",
  "signer_id": "SIGNER_789123"
}
```

**Возможные статусы:**
- `uploaded` - Загружен оригинал, ждет подписания
- `signed` - Договор подписан

---

### 4. 📥 GET /api/v1/download/{contract_id}/{file_type}
**Назначение:** Публичное скачивание файлов (БЕЗ API ключа)

**URL параметры:**
- `contract_id` (UUID) - ID договора
- `file_type` (string) - `original` или `signed`

**Ответ:** Бинарные данные PDF файла
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename=contract_UUID_original.pdf
Cache-Control: no-cache, no-store, must-revalidate

[PDF binary data]
```

**Ошибки:**
- `404` - Договор или файл не найден
- `404` - Подписанный файл недоступен (если статус `uploaded`)

---

## 🛡️ Требования к данным

### Хеширование персональных данных
❗ **ОБЯЗАТЕЛЬНО** хешируйте ПДн перед отправкой:

```
client_id = "CLIENT_" + HASH(ФИО + ДатаРождения + НомерДокумента) % 1000000
signer_id = "SIGNER_" + HASH(ФИОВрача + Должность + ЛицензияВрача) % 1000000
```

### Ограничения файлов
- **Тип:** Только PDF
- **Размер:** Максимум 50MB
- **Кодировка:** UTF-8

---

## 📊 Коды ошибок HTTP

| Код | Описание | Действие |
|-----|----------|----------|
| 200 | Успех | Продолжить |
| 400 | Неправильный запрос | Проверить данные |
| 401 | Неверный API ключ | Проверить ключ |
| 403 | IP заблокирован | Связаться с админом |
| 404 | Не найдено | Проверить UUID |
| 413 | Файл слишком большой | Уменьшить размер |
| 429 | Лимит запросов | Подождать 1 минуту |
| 500 | Ошибка сервера | Повторить позже |

---

## 🔄 Типичный workflow

1. **1С создает договор** → вызывает `POST /api/v1/upload`
2. **Получает UUID и ссылку** → сохраняет в базе 1С
3. **Отправляет ссылку клиенту** → email/SMS с `file_url`
4. **Врач подписывает** → 1С вызывает `POST /api/v1/sign/{uuid}`
5. **Отправляет подписанную версию** → email/SMS с `signed_file_url`

---

## 🧪 Тестирование

### Health Check (без API ключа):
```http
GET /health
→ {"status": "healthy", "service": "1C Contract Service"}
```

### Проверка API ключа:
```http
GET /api/v1/status/00000000-0000-0000-0000-000000000000
Authorization: Bearer YOUR_KEY
→ 404 (ключ правильный) или 401 (неверный ключ)
```

---

## ⚠️ Важные моменты

1. **UUID сохранять в 1С** - для дальнейших операций
2. **Публичные ссылки безопасны** - UUID невозможно угадать
3. **Rate limiting** - не более 100 запросов в минуту с одного IP
4. **Логирование** - все операции логируются на сервере
5. **Timeout** - устанавливайте 30+ секунд для загрузки файлов

---

## 📞 Техническая поддержка

- 🔧 **Health Check:** `GET /health`
- 📧 **Email:** tech@hg-doc-storage.com  
- 🎫 **Issues:** GitHub Issues в репозитории проекта

---

*API Version: 1.0.0*  
*Документация актуальна на: 15.08.2025*