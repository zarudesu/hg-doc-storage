#!/usr/bin/env python3
"""
Тест конфигурации Pydantic Settings
"""

import os
import tempfile
from pathlib import Path

def test_config():
    print("🧪 Тестирование конфигурации Pydantic...")
    
    # Создаем временный .env файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
DATABASE_URL=postgresql://test:test@localhost:5432/test_db
API_KEY=test-api-key
APP_NAME=Test App
POSTGRES_PASSWORD=should-be-ignored
EXTRA_VAR=should-be-ignored-too
""")
        env_file = f.name
    
    try:
        # Меняем рабочую директорию
        old_cwd = os.getcwd()
        test_dir = Path(env_file).parent
        os.chdir(test_dir)
        
        # Копируем .env файл в текущую директорию
        Path(".env").write_text(Path(env_file).read_text())
        
        # Импортируем Settings
        import sys
        sys.path.insert(0, "/users/zardes/Projects/hg-doc-storage")
        
        from app.core.config import Settings
        
        # Создаем экземпляр
        settings = Settings()
        
        print("✅ Settings создан успешно!")
        print(f"   database_url: {settings.database_url}")
        print(f"   api_key: {settings.api_key}")
        print(f"   app_name: {settings.app_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
        
    finally:
        # Очистка
        os.chdir(old_cwd)
        Path(env_file).unlink(missing_ok=True)
        Path(test_dir / ".env").unlink(missing_ok=True)

if __name__ == "__main__":
    test_config()
