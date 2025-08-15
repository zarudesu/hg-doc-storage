from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.schemas import (
    ContractUpload, ContractUploadResponse,
    ContractSign, ContractSignResponse,
    ContractInfo
)
from app.services.contract_service import ContractService
from app.core.config import settings
from app.core.security import security_dependencies, get_client_ip
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["1C Contract API"])


@router.post("/upload", response_model=ContractUploadResponse, dependencies=security_dependencies())
async def upload_original_file(
    request: Request,
    client_id: str = Form(..., description="ID клиента в 1С (хешированный)"),
    contract_type: str = Form(..., description="Тип договора"),
    file: UploadFile = File(..., description="PDF файл договора"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔒 Защищенный эндпоинт для 1С: загрузка оригинального файла
    
    Требует: Authorization: Bearer {API_KEY}
    
    Возвращает:
    - contract_id: UUID для дальнейших операций
    - file_url: ссылка для скачивания файла
    """
    
    client_ip = get_client_ip(request)
    logger.info(f"Upload request from IP: {client_ip}, client_id: {client_id[:10]}...")
    
    # Валидация файла
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.max_file_size} bytes")
    
    try:
        # Читаем файл
        file_content = await file.read()
        
        # Создаем данные контракта
        contract_data = ContractUpload(
            client_id=client_id,
            contract_type=contract_type
        )
        
        # Сохраняем файл
        contract = await ContractService.upload_original(
            db, contract_data, file_content
        )
        
        logger.info(f"File uploaded successfully: {contract.id}")
        
        # Формируем ответ
        return ContractUploadResponse(
            contract_id=contract.id,
            file_url=f"{settings.base_url}/api/v1/download/{contract.id}/original"
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sign/{contract_id}", response_model=ContractSignResponse, dependencies=security_dependencies())
async def upload_signed_file(
    contract_id: uuid.UUID,
    request: Request,
    signer_id: str = Form(..., description="ID подписавшего (хешированный)"),
    file: UploadFile = File(..., description="Подписанный PDF файл"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔒 Защищенный эндпоинт для 1С: загрузка подписанного файла
    
    Требует: Authorization: Bearer {API_KEY}
    
    Возвращает:
    - contract_id: UUID договора
    - signed_file_url: ссылка для скачивания подписанного файла
    """
    
    client_ip = get_client_ip(request)
    logger.info(f"Sign request from IP: {client_ip}, contract: {contract_id}, signer: {signer_id[:10]}...")
    
    # Валидация файла
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        # Читаем файл
        file_content = await file.read()
        
        # Создаем данные подписи
        sign_data = ContractSign(signer_id=signer_id)
        
        # Сохраняем подписанный файл
        contract = await ContractService.upload_signed(
            db, contract_id, sign_data, file_content
        )
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        logger.info(f"Contract signed successfully: {contract_id}")
        
        # Формируем ответ
        return ContractSignResponse(
            contract_id=contract.id,
            signed_file_url=f"{settings.base_url}/api/v1/download/{contract.id}/signed"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading signed file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download/{contract_id}/{file_type}")
async def download_file(
    contract_id: uuid.UUID,
    file_type: str,  # "original" или "signed"
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    📥 Публичный эндпоинт для скачивания файлов
    
    Не требует авторизации - безопасность через UUID
    file_type: "original" или "signed"
    """
    
    if file_type not in ["original", "signed"]:
        raise HTTPException(status_code=400, detail="file_type must be 'original' or 'signed'")
    
    client_ip = get_client_ip(request)
    logger.info(f"Download request from IP: {client_ip}, contract: {contract_id}, type: {file_type}")
    
    try:
        # Проверяем что договор существует
        contract = await ContractService.get_contract(db, contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Для подписанного файла проверяем что он есть
        if file_type == "signed" and contract.status != "signed":
            raise HTTPException(status_code=404, detail="Signed file not available")
        
        # Получаем файл
        file_content = await ContractService.get_file_content(contract_id, file_type)
        if not file_content:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Возвращаем файл
        filename = f"contract_{contract_id}_{file_type}.pdf"
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{contract_id}", response_model=ContractInfo, dependencies=security_dependencies())
async def get_contract_status(
    contract_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    🔒 Защищенный эндпоинт: получение статуса договора
    
    Требует: Authorization: Bearer {API_KEY}
    """
    
    client_ip = get_client_ip(request)
    logger.info(f"Status request from IP: {client_ip}, contract: {contract_id}")
    
    contract = await ContractService.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return ContractInfo(
        contract_id=contract.id,
        client_id=contract.client_id,
        contract_type=contract.contract_type,
        status=contract.status,
        original_file_url=f"{settings.base_url}/api/v1/download/{contract.id}/original",
        signed_file_url=f"{settings.base_url}/api/v1/download/{contract.id}/signed" if contract.status == "signed" else None,
        created_at=contract.created_at,
        signed_at=contract.signed_at,
        signer_id=contract.signer_id
    )
