"""
🔒 Защищенный пример интеграции с 1С (Production)
Демонстрирует работу с API ключами и безопасными запросами
"""

import requests
import json
import os
from pathlib import Path


class Secure1CIntegration:
    """Защищенный класс для работы с API сервиса"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        # Устанавливаем заголовок авторизации для всех запросов
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': '1C-Integration/1.0'
        })
    
    def upload_original(self, client_id: str, contract_type: str, pdf_path: str) -> dict:
        """
        🔒 Защищенная загрузка оригинального файла
        Требует API ключ в заголовке Authorization
        """
        url = f"{self.base_url}/api/v1/upload"
        
        # Хешируем client_id для защиты персональных данных
        hashed_client_id = f"CLIENT_{hash(client_id) % 1000000:06d}"
        
        data = {
            'client_id': hashed_client_id,  # Хешированный ID
            'contract_type': contract_type
        }
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'file': ('contract.pdf', pdf_file, 'application/pdf')}
            response = self.session.post(url, data=data, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Файл загружен (защищенно):")
            print(f"   UUID: {result['contract_id']}")
            print(f"   Ссылка: {result['file_url']}")
            print(f"   Client ID (хешированный): {hashed_client_id}")
            return result
        elif response.status_code == 401:
            print(f"❌ Ошибка авторизации: Неверный API ключ")
            raise Exception("Invalid API key")
        elif response.status_code == 403:
            print(f"❌ Доступ запрещен: IP адрес не в whitelist")
            raise Exception("IP not allowed")
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"   {response.text}")
            raise Exception("Upload failed")
    
    def upload_signed(self, contract_id: str, signer_id: str, signed_pdf_path: str) -> dict:
        """
        🔒 Защищенная загрузка подписанного файла
        """
        url = f"{self.base_url}/api/v1/sign/{contract_id}"
        
        # Хешируем signer_id для защиты персональных данных
        hashed_signer_id = f"SIGNER_{hash(signer_id) % 1000000:06d}"
        
        data = {'signer_id': hashed_signer_id}
        
        with open(signed_pdf_path, 'rb') as pdf_file:
            files = {'file': ('signed_contract.pdf', pdf_file, 'application/pdf')}
            response = self.session.post(url, data=data, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Подписанный файл загружен (защищенно):")
            print(f"   UUID: {result['contract_id']}")
            print(f"   Ссылка: {result['signed_file_url']}")
            print(f"   Signer ID (хешированный): {hashed_signer_id}")
            return result
        elif response.status_code == 401:
            print(f"❌ Ошибка авторизации: Неверный API ключ")
            raise Exception("Invalid API key")
        elif response.status_code == 404:
            print(f"❌ Договор не найден")
            raise Exception("Contract not found")
        else:
            print(f"❌ Ошибка загрузки подписанного файла: {response.status_code}")
            print(f"   {response.text}")
            raise Exception("Signed upload failed")
    
    def get_status(self, contract_id: str) -> dict:
        """🔒 Защищенная проверка статуса договора"""
        url = f"{self.base_url}/api/v1/status/{contract_id}"
        response = self.session.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise Exception("Invalid API key")
        else:
            raise Exception(f"Status check failed: {response.status_code}")
    
    def download_file(self, contract_id: str, file_type: str, save_path: str):
        """
        📥 Публичное скачивание файла (без API ключа)
        Безопасность обеспечивается через UUID
        """
        url = f"{self.base_url}/api/v1/download/{contract_id}/{file_type}"
        
        # Для download не нужен API ключ, используем отдельную сессию
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Файл скачан: {save_path}")
        else:
            print(f"❌ Ошибка скачивания: {response.status_code}")


def create_test_pdf(filename: str):
    """Создает тестовый PDF файл"""
    pdf_content = b"""%PDF-1.4
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
/Length 88
>>
stream
BT
/F1 12 Tf
100 700 Td
(CONFIDENTIAL CONTRACT DOCUMENT) Tj
0 -20 Td
(Patient: *** PERSONAL DATA *** ) Tj
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
320
%%EOF"""
    
    with open(filename, 'wb') as f:
        f.write(pdf_content)


def main():
    """Демонстрация защищенного workflow"""
    print("🔒 Защищенная демонстрация 1С интеграции")
    print("=" * 60)
    
    # Конфигурация (в реальности из .env или конфига 1С)
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
    API_KEY = os.getenv('API_KEY', 'your-secret-api-key-change-in-production')
    
    print(f"🌐 API URL: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:10]}..." if API_KEY else "❌ API_KEY not set")
    
    if not API_KEY or API_KEY == 'your-secret-api-key-change-in-production':
        print("⚠️ Warning: Using default API key. Set API_KEY environment variable.")
    
    # Проверяем доступность сервиса
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Сервис недоступен")
            return
    except:
        print("❌ Сервис недоступен. Убедитесь что он запущен.")
        return
    
    api = Secure1CIntegration(BASE_URL, API_KEY)
    
    # Создаем тестовые файлы
    print(f"\n📄 Создание тестовых PDF файлов...")
    create_test_pdf("original_secure.pdf")
    create_test_pdf("signed_secure.pdf")
    
    # Добавляем "подпись" во второй файл
    with open("signed_secure.pdf", "ab") as f:
        f.write(b"\n% DIGITAL SIGNATURE - Dr. Ivan Petrov\n")
        f.write(b"% TIMESTAMP: 2025-08-15 12:00:00 UTC\n")
    
    try:
        # Шаг 1: Загружаем оригинальный файл (с хешированием данных)
        print(f"\n🔒 Шаг 1: Защищенная загрузка оригинального файла...")
        upload_result = api.upload_original(
            client_id="Иванов Иван Иванович",  # Реальные данные (будут хешированы)
            contract_type="surgery",
            pdf_path="original_secure.pdf"
        )
        
        contract_id = upload_result['contract_id']
        
        # Шаг 2: Загружаем подписанный файл
        print(f"\n🔒 Шаг 2: Защищенная загрузка подписанного файла...")
        sign_result = api.upload_signed(
            contract_id=contract_id,
            signer_id="Доктор Петров И.И.",  # Реальные данные (будут хешированы)
            signed_pdf_path="signed_secure.pdf"
        )
        
        # Шаг 3: Проверяем статус
        print(f"\n🔒 Шаг 3: Защищенная проверка статуса...")
        status = api.get_status(contract_id)
        print(f"   Статус: {status['status']}")
        print(f"   Тип: {status['contract_type']}")
        print(f"   Создан: {status['created_at']}")
        print(f"   Подписан: {status['signed_at']}")
        print(f"   Client ID (хешированный): {status['client_id']}")
        print(f"   Signer ID (хешированный): {status['signer_id']}")
        
        # Шаг 4: Публичное скачивание (через UUID)
        print(f"\n📥 Шаг 4: Публичное скачивание...")
        api.download_file(contract_id, "original", "downloaded_original_secure.pdf")
        api.download_file(contract_id, "signed", "downloaded_signed_secure.pdf")
        
        print(f"\n✅ Защищенный workflow завершен успешно!")
        print(f"\n🔐 Информация о безопасности:")
        print(f"   - Персональные данные хешированы")
        print(f"   - API защищен ключом авторизации")
        print(f"   - Файлы доступны только по UUID")
        print(f"   - Все действия логируются")
        
        print(f"\n🔗 Публичные ссылки для клиента:")
        print(f"   Оригинал: {upload_result['file_url']}")
        print(f"   Подписанный: {sign_result['signed_file_url']}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        
        # Демонстрация ошибки с неверным API ключом
        print(f"\n🧪 Демонстрация ошибки авторизации...")
        try:
            bad_api = Secure1CIntegration(BASE_URL, "wrong-api-key")
            bad_api.get_status("550e8400-e29b-41d4-a716-446655440000")
        except Exception as auth_error:
            print(f"✅ Правильно заблокирован неверный API ключ: {auth_error}")
    
    finally:
        # Очистка
        for file in ["original_secure.pdf", "signed_secure.pdf", 
                    "downloaded_original_secure.pdf", "downloaded_signed_secure.pdf"]:
            Path(file).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
