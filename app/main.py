from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.api.contracts import router as contracts_router
from app.core.config import settings
import logging
import time
import uuid

# Настройка логирования для продакшена
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title=settings.app_name,
    description="🔒 Secure service for 1C contract file processing with API key protection",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # Отключаем docs в продакшене
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)

# Security middleware - только доверенные хосты
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Настройте под ваши домены
    )

# CORS middleware - ограниченный для продакшена
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Подключение роутеров
app.include_router(contracts_router)


# Request ID middleware для трейсинга
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Получаем IP клиента
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
    
    # Логируем запрос (без чувствительных данных)
    logger.info(
        f"Request started - ID: {request_id}, "
        f"Method: {request.method}, "
        f"Path: {request.url.path}, "
        f"IP: {client_ip}"
    )
    
    response = await call_next(request)
    
    # Логируем ответ
    process_time = time.time() - start_time
    logger.info(
        f"Request completed - ID: {request_id}, "
        f"Status: {response.status_code}, "
        f"Time: {process_time:.4f}s"
    )
    
    response.headers["X-Request-ID"] = request_id
    return response


# Rate limiting middleware (простая версия)
request_counts = {}

@app.middleware("http")
async def rate_limiting(request: Request, call_next):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    
    # Простое rate limiting: 100 запросов в минуту на IP
    current_time = int(time.time() / 60)  # Текущая минута
    key = f"{client_ip}:{current_time}"
    
    request_counts[key] = request_counts.get(key, 0) + 1
    
    if request_counts[key] > 100:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Очистка старых записей
    if len(request_counts) > 10000:
        old_keys = [k for k in request_counts.keys() if int(k.split(':')[1]) < current_time - 5]
        for old_key in old_keys:
            del request_counts[old_key]
    
    return await call_next(request)


@app.get("/")
async def root():
    """Главная страница с минимальной информацией"""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment
    }


@app.on_event("startup")
async def startup_event():
    """Инициализация приложения"""
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    logger.info(f"Base URL: {settings.base_url}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """Завершение работы приложения"""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
