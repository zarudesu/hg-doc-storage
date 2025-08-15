import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings
import logging
from typing import Optional
import uuid
from datetime import timedelta

logger = logging.getLogger(__name__)


class MinIOService:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Создает bucket если он не существует"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Created bucket: {self.bucket}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    async def upload_file(self, file_content: bytes, file_path: str, content_type: str = "application/pdf") -> str:
        """Загружает файл в MinIO"""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=file_path,
                Body=file_content,
                ContentType=content_type
            )
            logger.info(f"File uploaded successfully: {file_path}")
            return file_path
        except ClientError as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Получает файл из MinIO"""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=file_path)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: {file_path}")
                return None
            logger.error(f"Failed to get file {file_path}: {e}")
            raise
    
    def generate_signed_url(self, file_path: str, expiration: int = None) -> str:
        """Генерирует подписанную ссылку для доступа к файлу"""
        if expiration is None:
            expiration = settings.signed_url_expire_hours * 3600
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': file_path},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL for {file_path}: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Удаляет файл из MinIO"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False


# Singleton instance
minio_service = MinIOService()
