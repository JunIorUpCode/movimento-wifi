# -*- coding: utf-8 -*-
"""
License Service - Serviço de Licenciamento
Responsável por geração, validação e revogação de licenças
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.license import router as license_router
from services.license_validator import create_license_validator
from shared.database import DatabaseManager
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__, level=settings.LOG_LEVEL)

# Database manager para license_schema
db_manager = DatabaseManager("license_schema")

# License validator para validações periódicas
license_validator = create_license_validator(db_manager)

# Task para validações periódicas
validation_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação
    Inicializa e fecha conexões com banco
    """
    global validation_task
    
    # Startup
    logger.info("Iniciando license-service...")
    
    # Inicializa database
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    logger.info("Database inicializado")
    
    # Inicia validações periódicas de licenças (24h)
    license_validator.start()
    logger.info("License validator iniciado")
    
    logger.info("License-service iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando license-service...")
    
    # Para validações de licenças
    license_validator.stop()
    
    await db_manager.close()
    logger.info("License-service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense License Service",
    description="Serviço de gerenciamento de licenças multi-tenant",
    version="1.0.0",
    lifespan=lifespan
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routers
app.include_router(license_router)


@app.get("/health")
async def health_check():
    """
    Endpoint de health check
    Verifica saúde do serviço e conexões
    """
    # Verifica conexão com banco
    db_healthy = await db_manager.health_check()
    
    status_str = "healthy" if db_healthy else "degraded"
    
    return {
        "status": status_str,
        "service": "license-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "license_validator": "running" if license_validator.running else "stopped"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "license-service",
        "version": "1.0.0",
        "description": "Serviço de gerenciamento de licenças multi-tenant",
        "endpoints": {
            "health": "/health",
            "create_license": "POST /api/admin/licenses",
            "list_licenses": "GET /api/admin/licenses",
            "get_license": "GET /api/admin/licenses/{id}",
            "revoke_license": "PUT /api/admin/licenses/{id}/revoke",
            "extend_license": "PUT /api/admin/licenses/{id}/extend",
            "validate_license": "POST /api/licenses/validate"
        }
    }
