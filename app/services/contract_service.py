from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.contract import Contract
from app.core.schemas import ContractUpload, ContractSign
from app.services.minio_service import minio_service
from app.core.config import settings
import uuid
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ContractService:
    
    @staticmethod
    async def upload_original(
        db: AsyncSession,
        contract_data: ContractUpload,
        pdf_content: bytes
    ) -> Contract:
        """
        1С загружает оригинальный файл
        Возвращает UUID и ссылку
        """
        contract_id = uuid.uuid4()
        
        # Путь к файлу: contracts/{uuid}/original.pdf
        file_path = f"contracts/{contract_id}/original.pdf"
        
        # Сохраняем в MinIO
        await minio_service.upload_file(pdf_content, file_path)
        
        # Создаем запись в БД
        contract = Contract(
            id=contract_id,
            client_id=contract_data.client_id,
            contract_type=contract_data.contract_type,
            status="uploaded",
            original_file_path=file_path
        )
        
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        
        logger.info(f"Original file uploaded: {contract_id}")
        return contract
    
    @staticmethod
    async def upload_signed(
        db: AsyncSession,
        contract_id: uuid.UUID,
        sign_data: ContractSign,
        signed_pdf_content: bytes
    ) -> Optional[Contract]:
        """
        1С загружает подписанный файл
        Возвращает ссылку на подписанный файл
        """
        # Проверяем что договор существует
        result = await db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = result.scalar_one_or_none()
        
        if not contract:
            return None
            
        if contract.status == "signed":
            raise ValueError("Contract already signed")
        
        # Путь к подписанному файлу: contracts/{uuid}/signed.pdf
        signed_file_path = f"contracts/{contract_id}/signed.pdf"
        
        # Сохраняем в MinIO
        await minio_service.upload_file(signed_pdf_content, signed_file_path)
        
        # Обновляем запись в БД
        await db.execute(
            update(Contract)
            .where(Contract.id == contract_id)
            .values(
                status="signed",
                signed_file_path=signed_file_path,
                signed_at=datetime.utcnow(),
                signer_id=sign_data.signer_id
            )
        )
        
        await db.commit()
        
        # Получаем обновленный договор
        result = await db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        updated_contract = result.scalar_one()
        
        logger.info(f"Signed file uploaded: {contract_id}")
        return updated_contract
    
    @staticmethod
    async def get_contract(db: AsyncSession, contract_id: uuid.UUID) -> Optional[Contract]:
        """Получает договор по ID"""
        result = await db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_file_content(contract_id: uuid.UUID, file_type: str) -> Optional[bytes]:
        """
        Получает содержимое файла
        file_type: 'original' или 'signed'
        """
        if file_type == "original":
            file_path = f"contracts/{contract_id}/original.pdf"
        elif file_type == "signed":
            file_path = f"contracts/{contract_id}/signed.pdf"
        else:
            return None
            
        return await minio_service.get_file(file_path)
