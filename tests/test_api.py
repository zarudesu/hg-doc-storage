import pytest
from httpx import AsyncClient
import io


class TestContractAPI:
    
    async def test_health_check(self, client: AsyncClient):
        """Тест health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    async def test_root_endpoint(self, client: AsyncClient):
        """Тест главной страницы"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data
    
    async def test_upload_original_success(self, client: AsyncClient, sample_pdf):
        """Тест успешной загрузки оригинального файла"""
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "client_id": "CLIENT_001",
            "contract_type": "surgery"
        }
        
        response = await client.post("/api/v1/upload", files=files, data=data)
        assert response.status_code == 200
        
        result = response.json()
        assert "contract_id" in result
        assert "file_url" in result
        assert "message" in result
        assert result["message"] == "File uploaded successfully"
        
        return result["contract_id"]
    
    async def test_upload_invalid_file_type(self, client: AsyncClient):
        """Тест загрузки неправильного типа файла"""
        files = {
            "file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")
        }
        data = {
            "client_id": "CLIENT_001",
            "contract_type": "surgery"
        }
        
        response = await client.post("/api/v1/upload", files=files, data=data)
        assert response.status_code == 400
        assert "Only PDF files allowed" in response.json()["detail"]
    
    async def test_sign_contract_success(self, client: AsyncClient, sample_pdf):
        """Тест успешного подписания договора"""
        # Сначала загружаем оригинал
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "client_id": "CLIENT_002",
            "contract_type": "consultation"
        }
        
        upload_response = await client.post("/api/v1/upload", files=files, data=data)
        contract_id = upload_response.json()["contract_id"]
        
        # Теперь подписываем
        signed_files = {
            "file": ("signed.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        sign_data = {
            "signer_id": "DOCTOR_001"
        }
        
        sign_response = await client.post(
            f"/api/v1/sign/{contract_id}", 
            files=signed_files, 
            data=sign_data
        )
        assert sign_response.status_code == 200
        
        result = sign_response.json()
        assert result["contract_id"] == contract_id
        assert "signed_file_url" in result
        assert result["message"] == "File signed successfully"
    
    async def test_sign_nonexistent_contract(self, client: AsyncClient, sample_pdf):
        """Тест подписания несуществующего договора"""
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        files = {
            "file": ("signed.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "signer_id": "DOCTOR_001"
        }
        
        response = await client.post(f"/api/v1/sign/{fake_uuid}", files=files, data=data)
        assert response.status_code == 404
        assert "Contract not found" in response.json()["detail"]
    
    async def test_get_contract_status(self, client: AsyncClient, sample_pdf):
        """Тест получения статуса договора"""
        # Загружаем и подписываем договор
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "client_id": "CLIENT_003",
            "contract_type": "surgery"
        }
        
        upload_response = await client.post("/api/v1/upload", files=files, data=data)
        contract_id = upload_response.json()["contract_id"]
        
        # Проверяем статус после загрузки
        status_response = await client.get(f"/api/v1/status/{contract_id}")
        assert status_response.status_code == 200
        
        status = status_response.json()
        assert status["contract_id"] == contract_id
        assert status["client_id"] == "CLIENT_003"
        assert status["contract_type"] == "surgery"
        assert status["status"] == "uploaded"
        assert status["signed_file_url"] is None
        
        # Подписываем
        signed_files = {
            "file": ("signed.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        sign_data = {
            "signer_id": "DOCTOR_001"
        }
        
        await client.post(f"/api/v1/sign/{contract_id}", files=signed_files, data=sign_data)
        
        # Проверяем статус после подписания
        status_response = await client.get(f"/api/v1/status/{contract_id}")
        status = status_response.json()
        assert status["status"] == "signed"
        assert status["signer_id"] == "DOCTOR_001"
        assert status["signed_file_url"] is not None
    
    async def test_download_original_file(self, client: AsyncClient, sample_pdf):
        """Тест скачивания оригинального файла"""
        # Загружаем файл
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "client_id": "CLIENT_004",
            "contract_type": "surgery"
        }
        
        upload_response = await client.post("/api/v1/upload", files=files, data=data)
        contract_id = upload_response.json()["contract_id"]
        
        # Скачиваем оригинал
        download_response = await client.get(f"/api/v1/download/{contract_id}/original")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"
        assert len(download_response.content) > 0
    
    async def test_download_signed_file_not_available(self, client: AsyncClient, sample_pdf):
        """Тест скачивания подписанного файла когда он недоступен"""
        # Загружаем только оригинал
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "client_id": "CLIENT_005",
            "contract_type": "surgery"
        }
        
        upload_response = await client.post("/api/v1/upload", files=files, data=data)
        contract_id = upload_response.json()["contract_id"]
        
        # Пытаемся скачать подписанный файл
        download_response = await client.get(f"/api/v1/download/{contract_id}/signed")
        assert download_response.status_code == 404
        assert "not available" in download_response.json()["detail"]
    
    async def test_download_signed_file_success(self, client: AsyncClient, sample_pdf):
        """Тест успешного скачивания подписанного файла"""
        # Загружаем и подписываем
        files = {
            "file": ("test.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        data = {
            "client_id": "CLIENT_006",
            "contract_type": "surgery"
        }
        
        upload_response = await client.post("/api/v1/upload", files=files, data=data)
        contract_id = upload_response.json()["contract_id"]
        
        # Подписываем
        signed_files = {
            "file": ("signed.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        sign_data = {
            "signer_id": "DOCTOR_001"
        }
        
        await client.post(f"/api/v1/sign/{contract_id}", files=signed_files, data=sign_data)
        
        # Скачиваем подписанный файл
        download_response = await client.get(f"/api/v1/download/{contract_id}/signed")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"
        assert len(download_response.content) > 0
