# -*- coding: utf-8 -*-
"""
Tenant Service - Serviço de Gerenciamento de Tenants
Responsável por CRUD de tenants e gerenciamento de contas
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.tenant import router as tenant_router
from services.trial_manager import TrialManager
from shared.database import DatabaseManager
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__, level=settings.LOG_LEVEL)

# Database manager para tenant_schema
db_manager = DatabaseManager("tenant_schema")

# Trial manager para gerenciar períodos de trial
trial_manager = TrialManager(db_manager)

# Task para verificações periódicas
trial_check_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação
    Inicializa e fecha conexões com banco
    """
    global trial_check_task
    
    # Startup
    logger.info("Iniciando tenant-service...")
    
    # Inicializa database
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    logger.info("Database inicializado")
    
    # Inicia verificações periódicas de trials
    trial_check_task = asyncio.create_task(trial_manager.run_periodic_checks())
    logger.info("Trial manager iniciado")
    
    logger.info("Tenant-service iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando tenant-service...")
    
    # Para verificações de trials
    trial_manager.stop()
    if trial_check_task:
        trial_check_task.cancel()
        try:
            await trial_check_task
        except asyncio.CancelledError:
            pass
    
    await db_manager.close()
    logger.info("Tenant-service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense Tenant Service",
    description="Serviço de gerenciamento de tenants multi-tenant",
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
app.include_router(tenant_router)


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
        "service": "tenant-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "trial_manager": "running" if trial_manager.running else "stopped"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "tenant-service",
        "version": "1.0.0",
        "description": "Serviço de gerenciamento de tenants multi-tenant",
        "endpoints": {
            "health": "/health",
            "create_tenant": "POST /api/admin/tenants",
            "list_tenants": "GET /api/admin/tenants",
            "get_tenant": "GET /api/admin/tenants/{id}",
            "update_tenant": "PUT /api/admin/tenants/{id}",
            "delete_tenant": "DELETE /api/admin/tenants/{id}",
            "suspend_tenant": "POST /api/admin/tenants/{id}/suspend",
            "activate_tenant": "POST /api/admin/tenants/{id}/activate"
        }
    }
