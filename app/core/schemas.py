from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional


class ContractUpload(BaseModel):
    """Запрос от 1С для загрузки оригинального файла"""
    client_id: str
    contract_type: str


class ContractUploadResponse(BaseModel):
    """Ответ с UUID и ссылкой на загруженный файл"""
    contract_id: UUID4
    short_id: str
    file_url: str
    short_url: str  # Короткая ссылка для SMS
    message: str = "File uploaded successfully"


class ContractSign(BaseModel):
    """Запрос от 1С для загрузки подписанного файла"""
    signer_id: str


class ContractSignResponse(BaseModel):
    """Ответ с ссылкой на подписанный файл"""
    contract_id: UUID4
    short_id: str
    signed_file_url: str
    short_url: str  # Короткая ссылка (та же, что и для оригинала)
    message: str = "File signed successfully"


class ContractInfo(BaseModel):
    """Информация о договоре"""
    contract_id: UUID4
    short_id: str
    client_id: str
    contract_type: str
    status: str  # "uploaded" or "signed"
    original_file_url: str
    signed_file_url: Optional[str] = None
    short_url: str  # Универсальная короткая ссылка
    created_at: datetime
    signed_at: Optional[datetime] = None
    signer_id: Optional[str] = None

    model_config = {"from_attributes": True}
