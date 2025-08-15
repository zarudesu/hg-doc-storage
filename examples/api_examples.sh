#!/bin/bash

# Упрощенные примеры API для 1С интеграции
# Основной workflow: загрузка → подписание → скачивание

BASE_URL="http://localhost:8000"

echo "🏥 1C Contract Service - API Examples"
echo "====================================="

# Проверка здоровья сервиса
echo ""
echo "1. Health Check:"
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json" | jq '.'

# Создание тестового PDF файла
echo ""
echo "2. Создание тестового PDF файла..."
cat > test_contract.pdf << 'EOF'
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 56
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Contract Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
290
%%EOF
EOF

# ШАГ 1: Загрузка оригинального файла (1С → Сервис)
echo ""
echo "3. ШАГ 1: Загрузка оригинального файла от 1С"
UPLOAD_RESPONSE=$(curl -X POST "$BASE_URL/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "client_id=CLIENT_12345" \
  -F "contract_type=surgery_gastroscopy" \
  -F "file=@test_contract.pdf" \
  -s)

echo $UPLOAD_RESPONSE | jq '.'

# Извлекаем UUID договора
CONTRACT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.contract_id')
echo ""
echo "📋 UUID договора: $CONTRACT_ID"
echo "🔗 Ссылка на файл: $(echo $UPLOAD_RESPONSE | jq -r '.file_url')"

# Создание подписанного PDF
echo ""
echo "4. Создание подписанного PDF (симуляция подписи в 1С)..."
cp test_contract.pdf test_contract_signed.pdf
echo "% DIGITALLY SIGNED BY DOCTOR_001" >> test_contract_signed.pdf
echo "% SIGNATURE TIMESTAMP: $(date)" >> test_contract_signed.pdf

# ШАГ 2: Загрузка подписанного файла (1С → Сервис)
echo ""
echo "5. ШАГ 2: Загрузка подписанного файла от 1С"
SIGN_RESPONSE=$(curl -X POST "$BASE_URL/api/v1/sign/$CONTRACT_ID" \
  -H "Content-Type: multipart/form-data" \
  -F "signer_id=DOCTOR_001_IVANOV" \
  -F "file=@test_contract_signed.pdf" \
  -s)

echo $SIGN_RESPONSE | jq '.'
echo ""
echo "🔗 Ссылка на подписанный файл: $(echo $SIGN_RESPONSE | jq -r '.signed_file_url')"

# Проверка статуса договора
echo ""
echo "6. Проверка статуса договора:"
curl -X GET "$BASE_URL/api/v1/status/$CONTRACT_ID" \
  -H "Content-Type: application/json" \
  -s | jq '.'

# Скачивание оригинального файла
echo ""
echo "7. Скачивание оригинального файла:"
curl -X GET "$BASE_URL/api/v1/download/$CONTRACT_ID/original" \
  -o "downloaded_original.pdf" \
  -s
if [ -f "downloaded_original.pdf" ]; then
    echo "✅ Оригинальный файл скачан: downloaded_original.pdf"
    ls -la downloaded_original.pdf
else
    echo "❌ Ошибка скачивания оригинального файла"
fi

# Скачивание подписанного файла
echo ""
echo "8. Скачивание подписанного файла:"
curl -X GET "$BASE_URL/api/v1/download/$CONTRACT_ID/signed" \
  -o "downloaded_signed.pdf" \
  -s
if [ -f "downloaded_signed.pdf" ]; then
    echo "✅ Подписанный файл скачан: downloaded_signed.pdf"
    ls -la downloaded_signed.pdf
else
    echo "❌ Ошибка скачивания подписанного файла"
fi

# Демонстрация ошибок
echo ""
echo "9. Тестирование обработки ошибок:"

echo ""
echo "9.1. Попытка загрузить не-PDF файл:"
echo "This is not a PDF" > test.txt
curl -X POST "$BASE_URL/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "client_id=CLIENT_001" \
  -F "contract_type=test" \
  -F "file=@test.txt" \
  -s | jq '.'

echo ""
echo "9.2. Попытка подписать несуществующий договор:"
FAKE_UUID="550e8400-e29b-41d4-a716-446655440000"
curl -X POST "$BASE_URL/api/v1/sign/$FAKE_UUID" \
  -H "Content-Type: multipart/form-data" \
  -F "signer_id=DOCTOR_001" \
  -F "file=@test_contract_signed.pdf" \
  -s | jq '.'

echo ""
echo "9.3. Попытка получить статус несуществующего договора:"
curl -X GET "$BASE_URL/api/v1/status/$FAKE_UUID" \
  -H "Content-Type: application/json" \
  -s | jq '.'

# Очистка временных файлов
echo ""
echo "10. Очистка временных файлов..."
rm -f test_contract.pdf test_contract_signed.pdf test.txt downloaded_original.pdf downloaded_signed.pdf

echo ""
echo "✅ Все примеры выполнены!"
echo ""
echo "📚 Документация API:"
echo "- Swagger UI: $BASE_URL/docs"
echo "- ReDoc: $BASE_URL/redoc"
echo ""
echo "🔄 Основной workflow для 1С:"
echo "1. POST /api/v1/upload           - загрузка оригинала"
echo "2. POST /api/v1/sign/{id}        - загрузка подписанного"
echo "3. GET  /api/v1/download/{id}/... - скачивание файлов"
echo "4. GET  /api/v1/status/{id}      - проверка статуса"
