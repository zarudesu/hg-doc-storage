from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.contract_service import ContractService
from app.core.security import get_client_ip
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Short Links"])


@router.get("/{file_identifier}")
async def get_document_universal(
    file_identifier: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    📎 Универсальная короткая ссылка для получения документа
    
    Публичный эндпоинт, не требует авторизации
    
    Логика:
    - Если есть подписанная версия - возвращает её
    - Если нет подписанной - возвращает оригинал
    
    Поддерживает:
    - Короткий ID (8 символов): abc12345
    - Полный UUID (36 символов): 65d694a2-20bf-4df8-bff4-72ef9b7eeb7c
    """
    
    client_ip = get_client_ip(request)
    logger.info(f"Universal download request from IP: {client_ip}, identifier: {file_identifier}")
    
    try:
        # Ищем договор по идентификатору
        contract = await ContractService.resolve_contract_id(db, file_identifier)
        if not contract:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Получаем актуальную версию файла
        file_result = await ContractService.get_latest_file_content(contract)
        if not file_result:
            raise HTTPException(status_code=404, detail="File content not found")
        
        file_content, file_type = file_result
        
        # Формируем имя файла
        status_suffix = "signed" if file_type == "signed" else "original"
        filename = f"contract_{contract.short_id}_{status_suffix}.pdf"
        
        # Возвращаем файл с заголовками для кэширования
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-File-Type": file_type,
                "X-Contract-Status": contract.status,
                "X-Short-ID": contract.short_id,
                # Кэширование для оптимизации
                "Cache-Control": "public, max-age=300" if contract.status == "signed" else "no-cache",
                "ETag": f'"{contract.id}-{file_type}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in universal download: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
