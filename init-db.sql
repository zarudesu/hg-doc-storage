-- Инициализация базы данных для продакшена
-- Базовая настройка без изменений конфигурации

-- Убеждаемся что база данных использует UTF-8
-- ALTER DATABASE contract_db SET client_encoding TO 'utf8';
-- ALTER DATABASE contract_db SET default_text_search_config TO 'pg_catalog.russian';

-- Базовая настройка завершена
SELECT 'Database initialized successfully' as status;
