# 🧪 Примеры cURL для тестирования API

## 🔧 Настройка переменных

```bash
# Установите ваши реальные значения
export API_BASE="https://contracts.your-domain.com"
export API_KEY="your-secret-api-key-here"
export CONTRACT_ID="550e8400-e29b-41d4-a716-446655440000"
```

---

## 📡 Примеры запросов

### 1. Health Check (без авторизации)
```bash
curl -X GET "$API_BASE/health" \
  -H "Accept: application/json"
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "service": "1C Contract Service",
  "environment": "production"
}
```

---

### 2. Загрузка оригинального файла
```bash
curl -X POST "$API_BASE/api/v1/upload" \
  -H "Authorization: Bearer $API_KEY" \
  -F "client_id=CLIENT_123456" \
  -F "contract_type=surgery" \
  -F "file=@contract.pdf"
```

**Ожидаемый ответ (200):**
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_url": "https://contracts.your-domain.com/api/v1/download/550e8400-e29b-41d4-a716-446655440000/original",
  "message": "File uploaded successfully"
}
```

---

### 3. Загрузка подписанного файла
```bash
curl -X POST "$API_BASE/api/v1/sign/$CONTRACT_ID" \
  -H "Authorization: Bearer $API_KEY" \
  -F "signer_id=SIGNER_789123" \
  -F "file=@signed_contract.pdf"
```

---

### 4. Проверка статуса
```bash
curl -X GET "$API_BASE/api/v1/status/$CONTRACT_ID" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Accept: application/json"
```

---

### 5. Скачивание файлов (без авторизации)
```bash
# Скачать оригинал
curl -X GET "$API_BASE/api/v1/download/$CONTRACT_ID/original" \
  -o "downloaded_original.pdf"

# Скачать подписанный
curl -X GET "$API_BASE/api/v1/download/$CONTRACT_ID/signed" \
  -o "downloaded_signed.pdf"
```

---

## 🚨 Примеры ошибок

### Неверный API ключ (401)
```bash
curl -X GET "$API_BASE/api/v1/status/$CONTRACT_ID" \
  -H "Authorization: Bearer wrong-key"
```

### Договор не найден (404)
```bash
curl -X GET "$API_BASE/api/v1/status/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $API_KEY"
```

### Неправильный тип файла (400)
```bash
curl -X POST "$API_BASE/api/v1/upload" \
  -H "Authorization: Bearer $API_KEY" \
  -F "client_id=CLIENT_123456" \
  -F "contract_type=surgery" \
  -F "file=@document.txt"  # НЕ PDF файл
```

---

## 🎯 Скрипт для полного тестирования

Создайте файл `test_api.sh`:

```bash
#!/bin/bash

# Конфигурация
API_BASE="https://contracts.your-domain.com"
API_KEY="your-secret-api-key-here"

echo "🧪 Тестирование API интеграции с 1С"
echo "=================================="

# 1. Проверка доступности
echo "1. Проверка health check..."
HEALTH=$(curl -s "$API_BASE/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Сервис доступен"
else
    echo "❌ Сервис недоступен"
    exit 1
fi

# 2. Создание тестового PDF
echo "2. Создание тестового PDF..."
cat > test_contract.pdf << 'EOF'
%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF
EOF

# 3. Загрузка оригинала
echo "3. Загрузка оригинального файла..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/upload" \
  -H "Authorization: Bearer $API_KEY" \
  -F "client_id=CLIENT_TEST_$(date +%s)" \
  -F "contract_type=surgery" \
  -F "file=@test_contract.pdf")

echo "Ответ загрузки: $UPLOAD_RESPONSE"

# Извлекаем contract_id
CONTRACT_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"contract_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$CONTRACT_ID" ]; then
    echo "❌ Не удалось получить contract_id"
    exit 1
fi

echo "✅ Получен contract_id: $CONTRACT_ID"

# 4. Проверка статуса
echo "4. Проверка статуса договора..."
STATUS_RESPONSE=$(curl -s -X GET "$API_BASE/api/v1/status/$CONTRACT_ID" \
  -H "Authorization: Bearer $API_KEY")

echo "Статус: $STATUS_RESPONSE"

# 5. Скачивание оригинала
echo "5. Скачивание оригинального файла..."
curl -s -X GET "$API_BASE/api/v1/download/$CONTRACT_ID/original" \
  -o "downloaded_original.pdf"

if [ -f "downloaded_original.pdf" ]; then
    echo "✅ Файл скачан успешно"
    FILE_SIZE=$(wc -c < "downloaded_original.pdf")
    echo "Размер файла: $FILE_SIZE байт"
else
    echo "❌ Ошибка скачивания файла"
fi

# 6. Подписание (создаем "подписанную" версию)
echo "6. Создание подписанной версии..."
cp test_contract.pdf signed_contract.pdf
echo "% Digital signature added" >> signed_contract.pdf

SIGN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/sign/$CONTRACT_ID" \
  -H "Authorization: Bearer $API_KEY" \
  -F "signer_id=SIGNER_TEST_$(date +%s)" \
  -F "file=@signed_contract.pdf")

echo "Ответ подписания: $SIGN_RESPONSE"

# 7. Финальная проверка статуса
echo "7. Финальная проверка статуса..."
FINAL_STATUS=$(curl -s -X GET "$API_BASE/api/v1/status/$CONTRACT_ID" \
  -H "Authorization: Bearer $API_KEY")

echo "Финальный статус: $FINAL_STATUS"

# Очистка
rm -f test_contract.pdf signed_contract.pdf downloaded_original.pdf

echo ""
echo "✅ Тестирование завершено!"
echo "🔗 Contract ID для дальнейших тестов: $CONTRACT_ID"
```

Сделайте скрипт исполняемым:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 💡 Полезные команды для отладки

### Детальный вывод ошибок
```bash
curl -v -X POST "$API_BASE/api/v1/upload" \
  -H "Authorization: Bearer $API_KEY" \
  -F "client_id=CLIENT_123456" \
  -F "contract_type=surgery" \
  -F "file=@contract.pdf"
```

### Проверка заголовков ответа
```bash
curl -I "$API_BASE/api/v1/download/$CONTRACT_ID/original"
```

### Измерение времени ответа
```bash
curl -w "Time: %{time_total}s\n" -o /dev/null -s \
  "$API_BASE/health"
```

### Проверка SSL сертификата
```bash
curl -vI "$API_BASE/health" 2>&1 | grep -E "(SSL|TLS|certificate)"
```

---

## 🔧 Troubleshooting

| Проблема | Команда проверки | Решение |
|----------|------------------|---------|
| Сервис недоступен | `curl $API_BASE/health` | Проверить URL и сеть |
| 401 ошибка | `echo $API_KEY` | Проверить API ключ |
| 413 ошибка | `ls -lh file.pdf` | Уменьшить размер файла |
| 429 ошибка | `sleep 60` | Подождать минуту |
| SSL ошибки | `curl -k $API_BASE/health` | Проверить сертификаты |