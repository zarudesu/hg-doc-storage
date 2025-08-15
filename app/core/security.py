from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """
    Проверка API ключа
    """
    if credentials.credentials != settings.api_key:
        logger.warning(f"Invalid API key attempt: {credentials.credentials[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return True


def verify_ip_whitelist(request: Request) -> bool:
    """
    Проверка IP адреса (опционально)
    """
    if not settings.allowed_ips:
        return True
        
    client_ip = get_client_ip(request)
    
    if client_ip not in settings.allowed_ips:
        logger.warning(f"Access denied for IP: {client_ip}")
        raise HTTPException(
            status_code=403,
            detail="Access denied for your IP address"
        )
    return True


def get_client_ip(request: Request) -> str:
    """Получает реальный IP клиента"""
    # Проверяем заголовки прокси
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
        
    return request.client.host


def security_dependencies():
    """Зависимости безопасности для endpoints"""
    return [
        Depends(verify_api_key),
        # Depends(verify_ip_whitelist)  # Раскомментировать если нужна IP защита
    ]
