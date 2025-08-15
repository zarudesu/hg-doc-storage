from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(Text, nullable=False, index=True)
    contract_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="uploaded", index=True)  # uploaded / signed
    
    # Пути к файлам в MinIO
    original_file_path = Column(Text, nullable=False)
    signed_file_path = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    signed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Информация о подписавшем
    signer_id = Column(Text, nullable=True)
