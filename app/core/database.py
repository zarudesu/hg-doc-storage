from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Async engine для основного приложения
async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug
)

# Session maker для async сессий
async_session = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Sync engine для Alembic migrations
sync_engine = create_engine(settings.database_url)


async def get_db():
    """Dependency для получения async сессии БД"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
