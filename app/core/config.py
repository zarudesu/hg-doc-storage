from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@db:5432/contract_db"
    
    # MinIO/S3
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "contracts"
    minio_secure: bool = False
    
    # Security
    api_key: str = "your-secret-api-key-change-in-production"
    allowed_ips: List[str] = ["127.0.0.1", "::1"]  # IP whitelist для дополнительной защиты
    
    # Application
    app_name: str = "1C Contract Service"
    environment: str = "production"
    debug: bool = False
    base_url: str = "https://your-domain.com"
    
    # File settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()
