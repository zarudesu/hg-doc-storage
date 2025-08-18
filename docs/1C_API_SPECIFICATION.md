# 📋 API Спецификация v2.0 - с короткими ссылками

## 🔗 Базовые параметры подключения

**Base URL:** `https://doc.yourcompany.ru`  
**Авторизация:** Bearer Token в заголовке `Authorization`  
**Content-Type:** `multipart/form-data` для загрузки файлов  
**Timeout:** Рекомендуемый 30 секунд  

---

## 🆕 Главное нововведение: Короткие ссылки

### Принцип работы
1. **1С загружает оригинал** → получает `short_url`
2. **Клиент переходит по ссылке** → автоматически скачивает оригинал
3. **Файл подписывается и загружается в 1С** → `short_url` остается той же
4. **Клиент переходит по той же ссылке** → автоматически скачивает подписанную версию

### Формат короткой ссылки
```
https://doc.yourcompany.ru/abc12345
```
- 36 символов (с доменом)
- Идеально для SMS
- Автоматический выбор актуальной версии

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

### 1. 🔒 POST /api/v1/upload *(Обновлен)*
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

**Ответ 200 OK *(обновлен)*:**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "short_id": "abc12345",
  "file_url": "https://doc.yourcompany.ru/api/v1/download/550e8400-e29b-41d4-a716-446655440000/original",
  "short_url": "https://doc.yourcompany.ru/abc12345",
  "message": "File uploaded successfully"
}
```

**Новые поля:**
- `short_id` - 8-символьный идентификатор
- `short_url` - короткая ссылка для SMS

---

### 2. 🔒 POST /api/v1/sign/{contract_id} *(Обновлен)*
**Назначение:** Загрузка подписанного файла

**Параметры URL:**
- `contract_id` (UUID, required) - ID договора

**Параметры формы:**
- `signer_id` (string, required) - Хешированный ID подписавшего
- `file` (file, required) - Подписанный PDF файл

**Ответ 200 OK *(обновлен)*:**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000", 
  "short_id": "abc12345",
  "signed_file_url": "https://doc.yourcompany.ru/api/v1/download/550e8400-e29b-41d4-a716-446655440000/signed",
  "short_url": "https://doc.yourcompany.ru/abc12345",
  "message": "File signed successfully"
}
```

**Важно:** `short_url` остается неизменной!

---

### 3. 🆕 GET /{file_identifier} *(Новый!)*
**Назначение:** Универсальная короткая ссылка

**Параметры URL:**
- `file_identifier` - Короткий ID (8 символов) или полный UUID (36 символов)

**Примеры:**
```
GET /abc12345
GET /550e8400-e29b-41d4-a716-446655440000
```

**Логика выбора файла:**
1. Если есть подписанная версия → возвращает её
2. Если нет подписанной → возвращает оригинал  
3. Если файла нет → 404 ошибка

**Ответ 200 OK:**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename=contract_abc12345_signed.pdf
X-File-Type: signed
X-Contract-Status: signed
X-Short-ID: abc12345
```

**Заголовки ответа:**
- `X-File-Type` - тип файла (`original` или `signed`)
- `X-Contract-Status` - статус договора (`uploaded` или `signed`)
- `X-Short-ID` - короткий идентификатор

---

### 4. 🔒 GET /api/v1/status/{contract_id} *(Обновлен)*
**Назначение:** Проверка статуса договора

**Ответ 200 OK *(обновлен)*:**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "short_id": "abc12345", 
  "client_id": "CLIENT_456789",
  "contract_type": "surgery",
  "status": "signed",
  "original_file_url": "https://doc.yourcompany.ru/api/v1/download/550e8400-e29b-41d4-a716-446655440000/original",
  "signed_file_url": "https://doc.yourcompany.ru/api/v1/download/550e8400-e29b-41d4-a716-446655440000/signed",
  "short_url": "https://doc.yourcompany.ru/abc12345",
  "created_at": "2024-01-15T10:30:00Z",
  "signed_at": "2024-01-15T14:22:00Z", 
  "signer_id": "SIGNER_789123"
}
```

---

### 5. 📥 GET /api/v1/download/{contract_id}/{file_type}
**Назначение:** Скачивание конкретного типа файла *(без изменений)*

**Параметры URL:**
- `contract_id` (UUID) - ID договора
- `file_type` - тип файла (`original` или `signed`)

---

### 6. 🟢 GET /health
**Назначение:** Проверка здоровья сервиса *(без изменений)*

---

## 🔄 Workflow интеграции с 1С

### Новый рекомендуемый подход

```
1. 1С → POST /api/v1/upload 
   Ответ: { "short_url": "https://doc.yourcompany.ru/abc12345" }

2. Отправка SMS клиенту с короткой ссылкой
   "Договор: https://doc.yourcompany.ru/abc12345"

3. Клиент → GET /abc12345 
   (получает оригинал для подписания)

4. После подписания файла клиентом:
   1С → POST /api/v1/sign/{contract_id}
   Ответ: { "short_url": "https://doc.yourcompany.ru/abc12345" }

5. Уведомление клиента о готовности:
   "Подписанный договор: https://doc.yourcompany.ru/abc12345"

6. Клиент → GET /abc12345 
   (автоматически получает подписанную версию!)
```

### Старый подход (всё ещё работает)
```
1. POST /api/v1/upload → file_url 
2. Передача file_url клиенту
3. POST /api/v1/sign/{id} → signed_file_url
4. Передача signed_file_url клиенту  
```

---

## 📊 Коды ошибок

| Код | Описание | Примеры |
|-----|----------|---------|
| 200 | Успешно | Все операции прошли |
| 400 | Неверные данные | Не PDF файл, некорректные параметры |
| 401 | Неавторизован | Неверный API ключ |
| 403 | Запрещено | IP не в whitelist |
| 404 | Не найден | Договор не существует |
| 413 | Файл слишком большой | >50MB |
| 429 | Слишком много запросов | Rate limit exceeded |
| 500 | Ошибка сервера | Внутренняя ошибка |

---

## 💡 Рекомендации для 1С

### 1. Обработка ошибок
```1c
Попытка
    Результат = HTTPЗапрос.Выполнить();
    Если Результат.КодСостояния = 200 Тогда
        КороткаяСсылка = ПолучитьЗначениеJSON(Результат.Тело, "short_url");
    Иначе
        // Логирование ошибки
        ЗаписьЖурналаРегистрации("ContractService", УровеньЖурнала.Ошибка, 
            "Ошибка загрузки: " + Результат.КодСостояния);
    КонецЕсли;
Исключение
    // Обработка сетевых ошибок
КонецПопытки;
```

### 2. Отправка SMS с короткой ссылкой
```1c
Функция ОтправитьДоговорСMS(ТелефонКлиента, КороткаяСсылка)
    ТекстСообщения = "Договор готов к подписанию: " + КороткаяСсылка;
    Возврат СервисSMS.ОтправитьСообщение(ТелефонКлиента, ТекстСообщения);
КонецФункции
```

### 3. Использование одной ссылки
```1c
// При загрузке оригинала
КороткаяСсылка = РезультатЗагрузки.short_url;

// Сохраняем ссылку в 1С для повторного использования  
ДоговорОбъект.КороткаяСсылка = КороткаяСсылка;
ДоговорОбъект.Записать();

// При подписании - используем ту же ссылку!
УведомлениеОПодписании = "Договор подписан: " + ДоговорОбъект.КороткаяСсылка;
```

---

## 🔧 Миграция с версии 1.0

### Что изменилось
- ✅ Добавлены поля `short_id` и `short_url` в ответы
- ✅ Новый endpoint `GET /{file_identifier}` 
- ✅ Обновлена таблица БД (поле `short_id`)
- ✅ Nginx конфигурация для обработки коротких ссылок

### Что осталось без изменений
- ✅ Все существующие API endpoints
- ✅ Формат авторизации  
- ✅ Структура запросов
- ✅ Коды ошибок

### Процедура обновления
1. Остановить сервис
2. Применить миграцию БД: `alembic upgrade head`
3. Обновить код приложения
4. Обновить nginx конфигурацию
5. Запустить сервис

### Проверка работоспособности
```bash
# Проверка health check
curl https://doc.yourcompany.ru/health

# Тест загрузки (должен вернуть short_url)
curl -X POST https://doc.yourcompany.ru/api/v1/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "client_id=test" -F "contract_type=test" -F "file=@test.pdf"
```

---

## 📞 Поддержка

**Документация:** [GitHub Repository](https://github.com/zarudesu/hg-doc-storage)  
**Примеры:** [CURL Examples](CURL_EXAMPLES.md)  
**Короткие ссылки:** [Short Links Guide](SHORT_LINKS_GUIDE.md)

При возникновении проблем проверьте логи сервиса и документацию по устранению неполадок.
