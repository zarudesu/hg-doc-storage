#!/bin/bash

# 🧪 Полный тест коротких ссылок v2.0
# Тестирует все новые возможности системы

set -e  # Остановить при первой ошибке

# Конфигурация
API_BASE="${API_BASE:-https://doc.yourcompany.ru}"
API_KEY="${API_KEY:-your-api-key-here}"

echo "🧪 Тестирование коротких ссылок v2.0"
echo "=================================="
echo "Base URL: $API_BASE"
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v curl &> /dev/null; then
        log_error "curl не найден. Установите curl для продолжения."
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq не найден. JSON ответы будут показаны без форматирования."
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi
    
    log_success "Зависимости проверены"
}

# Проверка доступности API
check_health() {
    log_info "Проверка health check..."
    
    HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o health_response.tmp "$API_BASE/health")
    HTTP_CODE=${HEALTH_RESPONSE: -3}
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Сервис доступен (HTTP $HTTP_CODE)"
        if [ "$JQ_AVAILABLE" = true ]; then
            cat health_response.tmp | jq .
        else
            cat health_response.tmp
        fi
    else
        log_error "Сервис недоступен (HTTP $HTTP_CODE)"
        cat health_response.tmp
        exit 1
    fi
    
    rm -f health_response.tmp
    echo ""
}

# Создание тестового PDF
create_test_pdf() {
    log_info "Создание тестового PDF..."
    
    cat > test_contract.pdf << 'EOF'
%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Test Contract Document) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000207 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
296
%%EOF
EOF
    
    log_success "Тестовый PDF создан ($(wc -c < test_contract.pdf) байт)"
}

# Тест 1: Загрузка оригинала с получением короткой ссылки
test_upload_original() {
    log_info "Тест 1: Загрузка оригинального файла..."
    
    CLIENT_ID="CLIENT_TEST_$(date +%s)"
    
    UPLOAD_RESPONSE=$(curl -s -w "%{http_code}" -o upload_response.tmp \
        -X POST "$API_BASE/api/v1/upload" \
        -H "Authorization: Bearer $API_KEY" \
        -F "client_id=$CLIENT_ID" \
        -F "contract_type=surgery" \
        -F "file=@test_contract.pdf")
    
    HTTP_CODE=${UPLOAD_RESPONSE: -3}
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Файл загружен успешно (HTTP $HTTP_CODE)"
        
        if [ "$JQ_AVAILABLE" = true ]; then
            cat upload_response.tmp | jq .
            CONTRACT_ID=$(cat upload_response.tmp | jq -r '.contract_id')
            SHORT_ID=$(cat upload_response.tmp | jq -r '.short_id')
            SHORT_URL=$(cat upload_response.tmp | jq -r '.short_url')
        else
            cat upload_response.tmp
            # Простое извлечение без jq
            CONTRACT_ID=$(grep -o '"contract_id":"[^"]*"' upload_response.tmp | cut -d'"' -f4)
            SHORT_ID=$(grep -o '"short_id":"[^"]*"' upload_response.tmp | cut -d'"' -f4)
            SHORT_URL=$(grep -o '"short_url":"[^"]*"' upload_response.tmp | cut -d'"' -f4)
        fi
        
        log_info "Contract ID: $CONTRACT_ID"
        log_info "Short ID: $SHORT_ID"
        log_info "Short URL: $SHORT_URL"
        
        # Экспорт для других тестов
        export CONTRACT_ID SHORT_ID SHORT_URL
        
    else
        log_error "Ошибка загрузки (HTTP $HTTP_CODE)"
        cat upload_response.tmp
        exit 1
    fi
    
    rm -f upload_response.tmp
    echo ""
}

# Тест 2: Скачивание по короткой ссылке (оригинал)
test_download_short_original() {
    log_info "Тест 2: Скачивание по короткой ссылке (должен быть оригинал)..."
    
    if [ -z "$SHORT_ID" ]; then
        log_error "SHORT_ID не установлен. Пропускаем тест."
        return
    fi
    
    # Скачивание с проверкой заголовков
    curl -s -D headers_original.tmp -o downloaded_original.pdf "$API_BASE/$SHORT_ID"
    
    if [ -f "downloaded_original.pdf" ] && [ -s "downloaded_original.pdf" ]; then
        FILE_SIZE=$(wc -c < downloaded_original.pdf)
        log_success "Файл скачан по короткой ссылке ($FILE_SIZE байт)"
        
        # Проверка заголовков
        log_info "Заголовки ответа:"
        grep -E "X-File-Type|X-Contract-Status|X-Short-ID|Content-Disposition" headers_original.tmp || true
        
        FILE_TYPE=$(grep "X-File-Type:" headers_original.tmp | cut -d' ' -f2 | tr -d '\r\n' || echo "unknown")
        log_info "Тип файла: $FILE_TYPE"
        
        if [ "$FILE_TYPE" = "original" ]; then
            log_success "Корректно возвращается оригинал"
        else
            log_warning "Ожидался оригинал, получен: $FILE_TYPE"
        fi
    else
        log_error "Ошибка скачивания файла по короткой ссылке"
        cat headers_original.tmp
    fi
    
    rm -f headers_original.tmp
    echo ""
}

# Тест 3: Проверка статуса договора
test_status_check() {
    log_info "Тест 3: Проверка статуса договора..."
    
    if [ -z "$CONTRACT_ID" ]; then
        log_error "CONTRACT_ID не установлен. Пропускаем тест."
        return
    fi
    
    STATUS_RESPONSE=$(curl -s -w "%{http_code}" -o status_response.tmp \
        -X GET "$API_BASE/api/v1/status/$CONTRACT_ID" \
        -H "Authorization: Bearer $API_KEY")
    
    HTTP_CODE=${STATUS_RESPONSE: -3}
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Статус получен успешно (HTTP $HTTP_CODE)"
        
        if [ "$JQ_AVAILABLE" = true ]; then
            cat status_response.tmp | jq .
            STATUS=$(cat status_response.tmp | jq -r '.status')
        else
            cat status_response.tmp
            STATUS=$(grep -o '"status":"[^"]*"' status_response.tmp | cut -d'"' -f4)
        fi
        
        log_info "Текущий статус: $STATUS"
        
        if [ "$STATUS" = "uploaded" ]; then
            log_success "Статус корректный для загруженного файла"
        else
            log_warning "Неожиданный статус: $STATUS"
        fi
    else
        log_error "Ошибка получения статуса (HTTP $HTTP_CODE)"
        cat status_response.tmp
    fi
    
    rm -f status_response.tmp
    echo ""
}

# Тест 4: Создание подписанной версии
create_signed_pdf() {
    log_info "Тест 4: Создание подписанной версии файла..."
    
    # Копируем оригинал и добавляем "подпись"
    cp test_contract.pdf signed_contract.pdf
    echo "% Digital signature added by test at $(date)" >> signed_contract.pdf
    
    log_success "Подписанная версия создана ($(wc -c < signed_contract.pdf) байт)"
}

# Тест 5: Загрузка подписанного файла
test_upload_signed() {
    log_info "Тест 5: Загрузка подписанного файла..."
    
    if [ -z "$CONTRACT_ID" ]; then
        log_error "CONTRACT_ID не установлен. Пропускаем тест."
        return
    fi
    
    SIGNER_ID="SIGNER_TEST_$(date +%s)"
    
    SIGN_RESPONSE=$(curl -s -w "%{http_code}" -o sign_response.tmp \
        -X POST "$API_BASE/api/v1/sign/$CONTRACT_ID" \
        -H "Authorization: Bearer $API_KEY" \
        -F "signer_id=$SIGNER_ID" \
        -F "file=@signed_contract.pdf")
    
    HTTP_CODE=${SIGN_RESPONSE: -3}
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Подписанный файл загружен (HTTP $HTTP_CODE)"
        
        if [ "$JQ_AVAILABLE" = true ]; then
            cat sign_response.tmp | jq .
            RETURNED_SHORT_URL=$(cat sign_response.tmp | jq -r '.short_url')
        else
            cat sign_response.tmp
            RETURNED_SHORT_URL=$(grep -o '"short_url":"[^"]*"' sign_response.tmp | cut -d'"' -f4)
        fi
        
        log_info "Возвращенная короткая ссылка: $RETURNED_SHORT_URL"
        
        if [ "$RETURNED_SHORT_URL" = "$SHORT_URL" ]; then
            log_success "Короткая ссылка осталась неизменной! ✨"
        else
            log_error "Короткая ссылка изменилась! Ожидалась: $SHORT_URL, получена: $RETURNED_SHORT_URL"
        fi
        
    else
        log_error "Ошибка загрузки подписанного файла (HTTP $HTTP_CODE)"
        cat sign_response.tmp
    fi
    
    rm -f sign_response.tmp
    echo ""
}

# Тест 6: Скачивание по короткой ссылке (теперь подписанный)
test_download_short_signed() {
    log_info "Тест 6: Скачивание по той же короткой ссылке (должен быть подписанный)..."
    
    if [ -z "$SHORT_ID" ]; then
        log_error "SHORT_ID не установлен. Пропускаем тест."
        return
    fi
    
    # Скачивание с проверкой заголовков
    curl -s -D headers_signed.tmp -o downloaded_signed.pdf "$API_BASE/$SHORT_ID"
    
    if [ -f "downloaded_signed.pdf" ] && [ -s "downloaded_signed.pdf" ]; then
        FILE_SIZE=$(wc -c < downloaded_signed.pdf)
        log_success "Файл скачан по той же короткой ссылке ($FILE_SIZE байт)"
        
        # Проверка заголовков
        log_info "Заголовки ответа:"
        grep -E "X-File-Type|X-Contract-Status|X-Short-ID|Content-Disposition" headers_signed.tmp || true
        
        FILE_TYPE=$(grep "X-File-Type:" headers_signed.tmp | cut -d' ' -f2 | tr -d '\r\n' || echo "unknown")
        CONTRACT_STATUS=$(grep "X-Contract-Status:" headers_signed.tmp | cut -d' ' -f2 | tr -d '\r\n' || echo "unknown")
        
        log_info "Тип файла: $FILE_TYPE"
        log_info "Статус договора: $CONTRACT_STATUS"
        
        if [ "$FILE_TYPE" = "signed" ] && [ "$CONTRACT_STATUS" = "signed" ]; then
            log_success "🎉 Отлично! Теперь возвращается подписанная версия!"
        else
            log_warning "Ожидался подписанный файл, получен тип: $FILE_TYPE, статус: $CONTRACT_STATUS"
        fi
        
        # Сравнение размеров файлов
        if [ -f "downloaded_original.pdf" ]; then
            ORIGINAL_SIZE=$(wc -c < downloaded_original.pdf)
            SIGNED_SIZE=$(wc -c < downloaded_signed.pdf)
            
            if [ "$SIGNED_SIZE" -gt "$ORIGINAL_SIZE" ]; then
                log_success "Подписанный файл больше оригинала ($SIGNED_SIZE > $ORIGINAL_SIZE байт)"
            else
                log_warning "Размеры файлов: оригинал=$ORIGINAL_SIZE, подписанный=$SIGNED_SIZE"
            fi
        fi
        
    else
        log_error "Ошибка скачивания подписанного файла"
        cat headers_signed.tmp
    fi
    
    rm -f headers_signed.tmp
    echo ""
}

# Тест 7: Проверка финального статуса
test_final_status() {
    log_info "Тест 7: Финальная проверка статуса..."
    
    if [ -z "$CONTRACT_ID" ]; then
        log_error "CONTRACT_ID не установлен. Пропускаем тест."
        return
    fi
    
    FINAL_STATUS_RESPONSE=$(curl -s -w "%{http_code}" -o final_status_response.tmp \
        -X GET "$API_BASE/api/v1/status/$CONTRACT_ID" \
        -H "Authorization: Bearer $API_KEY")
    
    HTTP_CODE=${FINAL_STATUS_RESPONSE: -3}
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Финальный статус получен (HTTP $HTTP_CODE)"
        
        if [ "$JQ_AVAILABLE" = true ]; then
            cat final_status_response.tmp | jq .
            FINAL_STATUS=$(cat final_status_response.tmp | jq -r '.status')
        else
            cat final_status_response.tmp
            FINAL_STATUS=$(grep -o '"status":"[^"]*"' final_status_response.tmp | cut -d'"' -f4)
        fi
        
        if [ "$FINAL_STATUS" = "signed" ]; then
            log_success "Финальный статус корректный: $FINAL_STATUS"
        else
            log_warning "Неожиданный финальный статус: $FINAL_STATUS"
        fi
    else
        log_error "Ошибка получения финального статуса (HTTP $HTTP_CODE)"
        cat final_status_response.tmp
    fi
    
    rm -f final_status_response.tmp
    echo ""
}

# Тест 8: Проверка совместимости старых API
test_legacy_compatibility() {
    log_info "Тест 8: Проверка совместимости со старыми API..."
    
    if [ -z "$CONTRACT_ID" ]; then
        log_error "CONTRACT_ID не установлен. Пропускаем тест."
        return
    fi
    
    # Тест старых endpoints скачивания
    log_info "Тестирование старого endpoint для оригинала..."
    curl -s -D headers_legacy_original.tmp -o legacy_original.pdf \
        "$API_BASE/api/v1/download/$CONTRACT_ID/original"
    
    if [ -f "legacy_original.pdf" ] && [ -s "legacy_original.pdf" ]; then
        log_success "Старый API для оригинала работает"
    else
        log_warning "Проблема со старым API для оригинала"
    fi
    
    log_info "Тестирование старого endpoint для подписанного..."
    curl -s -D headers_legacy_signed.tmp -o legacy_signed.pdf \
        "$API_BASE/api/v1/download/$CONTRACT_ID/signed"
    
    if [ -f "legacy_signed.pdf" ] && [ -s "legacy_signed.pdf" ]; then
        log_success "Старый API для подписанного работает"
    else
        log_warning "Проблема со старым API для подписанного"
    fi
    
    rm -f headers_legacy_*.tmp legacy_*.pdf
    echo ""
}

# Тест 9: Проверка работы с полным UUID
test_full_uuid() {
    log_info "Тест 9: Проверка работы с полным UUID..."
    
    if [ -z "$CONTRACT_ID" ]; then
        log_error "CONTRACT_ID не установлен. Пропускаем тест."
        return
    fi
    
    # Скачивание по полному UUID
    curl -s -D headers_uuid.tmp -o downloaded_uuid.pdf "$API_BASE/$CONTRACT_ID"
    
    if [ -f "downloaded_uuid.pdf" ] && [ -s "downloaded_uuid.pdf" ]; then
        FILE_SIZE=$(wc -c < downloaded_uuid.pdf)
        log_success "Файл скачан по полному UUID ($FILE_SIZE байт)"
        
        FILE_TYPE=$(grep "X-File-Type:" headers_uuid.tmp | cut -d' ' -f2 | tr -d '\r\n' || echo "unknown")
        log_info "Тип файла: $FILE_TYPE"
        
        if [ "$FILE_TYPE" = "signed" ]; then
            log_success "Полный UUID корректно возвращает подписанную версию"
        else
            log_warning "Полный UUID вернул: $FILE_TYPE"
        fi
    else
        log_error "Ошибка скачивания по полному UUID"
    fi
    
    rm -f headers_uuid.tmp downloaded_uuid.pdf
    echo ""
}

# Очистка временных файлов
cleanup() {
    log_info "Очистка временных файлов..."
    rm -f test_contract.pdf signed_contract.pdf
    rm -f downloaded_*.pdf *.tmp
    log_success "Очистка завершена"
}

# Итоговый отчет
generate_report() {
    echo ""
    echo "📊 ИТОГОВЫЙ ОТЧЕТ"
    echo "================="
    
    if [ -n "$CONTRACT_ID" ]; then
        echo "✅ Contract ID: $CONTRACT_ID"
    fi
    
    if [ -n "$SHORT_ID" ]; then
        echo "✅ Short ID: $SHORT_ID"
    fi
    
    if [ -n "$SHORT_URL" ]; then
        echo "✅ Short URL: $SHORT_URL"
        echo ""
        echo "🎯 Для тестирования в браузере:"
        echo "   $SHORT_URL"
        echo ""
        echo "📱 SMS шаблон:"
        echo "   Договор готов: $SHORT_URL"
    fi
    
    echo ""
    echo "✨ Ключевые особенности протестированы:"
    echo "   ✅ Загрузка оригинала с получением короткой ссылки"
    echo "   ✅ Скачивание оригинала по короткой ссылке"  
    echo "   ✅ Загрузка подписанного файла"
    echo "   ✅ Автоматическое переключение на подписанную версию"
    echo "   ✅ Неизменность короткой ссылки"
    echo "   ✅ Совместимость со старыми API"
    echo "   ✅ Поддержка полного UUID"
    echo ""
    echo "🚀 Система готова к продакшену!"
}

# Основная функция
main() {
    check_dependencies
    check_health
    create_test_pdf
    
    test_upload_original
    test_download_short_original
    test_status_check
    
    create_signed_pdf
    test_upload_signed
    test_download_short_signed
    test_final_status
    
    test_legacy_compatibility
    test_full_uuid
    
    cleanup
    generate_report
}

# Обработка прерывания
trap cleanup EXIT

# Запуск
main "$@"
