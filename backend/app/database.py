from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from app.config import settings

async_engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
sync_engine = create_engine(settings.database_url_sync)


async def get_db():
    async with async_session() as session:
        yield session
