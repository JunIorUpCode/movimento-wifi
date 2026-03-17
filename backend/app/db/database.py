"""
Configuração do banco de dados com SQLAlchemy.
Suporta PostgreSQL e SQLite (fallback).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Carregar variáveis de ambiente
load_dotenv()

# Obter DATABASE_URL do .env ou usar SQLite como fallback
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback para SQLite se não houver DATABASE_URL
    _DB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(_DB_DIR, 'wifisense.db')}"
    print("[DB] DATABASE_URL nao encontrada, usando SQLite como fallback")
else:
    # Converter postgresql:// para postgresql+asyncpg:// para suporte assíncrono
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        print(f"[DB] Conectando ao PostgreSQL: {DATABASE_URL.split('@')[1]}")

_is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    **({} if _is_sqlite else {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    })
)

async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,  # Evita flush automático
    autocommit=False  # Controle manual de commits
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Cria todas as tabelas no banco."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency para injeção de sessão nas rotas."""
    async with async_session() as session:
        yield session
