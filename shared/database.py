# -*- coding: utf-8 -*-
"""
Shared Database - Gerenciamento de Conexões com Banco de Dados
Fornece conexões assíncronas com PostgreSQL e isolamento por schema
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

# Base para modelos SQLAlchemy
Base = declarative_base()


class DatabaseManager:
    """
    Gerenciador de conexões com banco de dados
    Suporta múltiplos schemas para isolamento de microserviços
    """
    
    def __init__(self, schema: str):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            schema: Nome do schema PostgreSQL (auth_schema, tenant_schema, etc)
        """
        self.schema = schema
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        
        logger.info(
            f"DatabaseManager inicializado para schema: {schema}",
            schema=schema
        )
    
    async def initialize(self):
        """
        Inicializa a engine e session factory
        Deve ser chamado na inicialização do serviço
        """
        if self.engine is not None:
            logger.warning(
                "Engine já inicializada, pulando inicialização",
                schema=self.schema
            )
            return
        
        # Cria engine assíncrona
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.DEBUG,
            pool_size=20,  # Mínimo de 20 conexões conforme requisito 22.3
            max_overflow=10,
            pool_pre_ping=True,  # Verifica conexões antes de usar
            connect_args={
                "server_settings": {
                    "search_path": self.schema  # Define schema padrão
                }
            }
        )
        
        # Cria session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(
            f"Engine e session factory criadas para schema: {self.schema}",
            schema=self.schema,
            pool_size=20
        )
    
    async def close(self):
        """
        Fecha a engine e libera recursos
        Deve ser chamado no shutdown do serviço
        """
        if self.engine is not None:
            await self.engine.dispose()
            logger.info(
                f"Engine fechada para schema: {self.schema}",
                schema=self.schema
            )
            self.engine = None
            self.session_factory = None
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager para obter sessão do banco de dados
        Garante que a sessão seja fechada após uso
        
        Uso:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
        
        Yields:
            AsyncSession: Sessão do banco de dados
        """
        if self.session_factory is None:
            raise RuntimeError(
                "DatabaseManager não inicializado. Chame initialize() primeiro."
            )
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Erro na sessão do banco de dados: {str(e)}",
                    schema=self.schema,
                    error=str(e)
                )
                raise
            finally:
                await session.close()
    
    async def create_schema(self):
        """
        Cria o schema no PostgreSQL se não existir
        Deve ser executado durante setup inicial
        """
        if self.engine is None:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
            )
            logger.info(
                f"Schema criado ou já existe: {self.schema}",
                schema=self.schema
            )
    
    async def create_tables(self):
        """
        Cria todas as tabelas definidas nos modelos SQLAlchemy
        Deve ser executado após definir os modelos
        """
        if self.engine is None:
            await self.initialize()
        
        async with self.engine.begin() as conn:
            # Define o search_path para o schema correto
            await conn.execute(text(f"SET search_path TO {self.schema}"))
            
            # Cria todas as tabelas
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info(
                f"Tabelas criadas no schema: {self.schema}",
                schema=self.schema
            )
    
    async def health_check(self) -> bool:
        """
        Verifica se a conexão com o banco está saudável
        
        Returns:
            bool: True se conexão está OK, False caso contrário
        """
        try:
            if self.engine is None:
                return False
            
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            return True
        except Exception as e:
            logger.error(
                f"Health check falhou para schema {self.schema}: {str(e)}",
                schema=self.schema,
                error=str(e)
            )
            return False


# Factory functions para cada schema
def get_auth_db() -> DatabaseManager:
    """Retorna DatabaseManager para auth_schema"""
    return DatabaseManager("auth_schema")


def get_tenant_db() -> DatabaseManager:
    """Retorna DatabaseManager para tenant_schema"""
    return DatabaseManager("tenant_schema")


def get_device_db() -> DatabaseManager:
    """Retorna DatabaseManager para device_schema"""
    return DatabaseManager("device_schema")


def get_license_db() -> DatabaseManager:
    """Retorna DatabaseManager para license_schema"""
    return DatabaseManager("license_schema")


def get_event_db() -> DatabaseManager:
    """Retorna DatabaseManager para event_schema"""
    return DatabaseManager("event_schema")


def get_notification_db() -> DatabaseManager:
    """Retorna DatabaseManager para notification_schema"""
    return DatabaseManager("notification_schema")


def get_billing_db() -> DatabaseManager:
    """Retorna DatabaseManager para billing_schema"""
    return DatabaseManager("billing_schema")
