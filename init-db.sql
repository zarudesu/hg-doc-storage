-- Инициализация базы данных для продакшена
-- Создание индексов для производительности

-- Убеждаемся что база данных использует UTF-8
ALTER DATABASE contract_db SET client_encoding TO 'utf8';
ALTER DATABASE contract_db SET default_text_search_config TO 'pg_catalog.russian';

-- Создание дополнительных индексов для производительности
-- (будут созданы после миграций Alembic)

-- Настройки для логирования (для аудита)
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
