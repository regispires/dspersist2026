import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração assíncrona do banco de dados
engine = create_async_engine(os.getenv("DATABASE_URL"), echo=True)

# Factory de sessões assíncronas
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.url.get_backend_name() == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
