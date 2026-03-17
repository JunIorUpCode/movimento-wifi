# -*- coding: utf-8 -*-
"""
Device Service - Serviço de Gerenciamento de Dispositivos
Responsável por registro, configuração e monitoramento de dispositivos
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.device import router as device_router
from services.device_heartbeat import OfflineDetectionWorker
from shared.database import DatabaseManager
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__, level=settings.LOG_LEVEL)

# Database manager para device_schema
db_manager = DatabaseManager("device_schema")

# Worker para detecção de dispositivos offline
offline_worker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação
    Inicializa e fecha conexões com banco
    """
    global offline_worker
    
    # Startup
    logger.info("Iniciando device-service...")
    
    # Inicializa database
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    logger.info("Database inicializado")
    
    # Inicia worker de detecção de offline
    offline_worker = OfflineDetectionWorker(db_manager)
    offline_worker.start()
    logger.info("OfflineDetectionWorker iniciado")
    
    logger.info("Device-service iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando device-service...")
    
    # Para worker
    if offline_worker:
        offline_worker.stop()
    
    await db_manager.close()
    logger.info("Device-service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense Device Service",
    description="Serviço de gerenciamento de dispositivos multi-tenant",
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
app.include_router(device_router)


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
        "service": "device-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "offline_worker": "running" if (offline_worker and offline_worker.running) else "stopped"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "device-service",
        "version": "1.0.0",
        "description": "Serviço de gerenciamento de dispositivos multi-tenant",
        "endpoints": {
            "health": "/health",
            "register_device": "POST /api/devices/register",
            "list_devices": "GET /api/devices",
            "get_device": "GET /api/devices/{id}",
            "update_device": "PUT /api/devices/{id}",
            "deactivate_device": "DELETE /api/devices/{id}",
            "device_status": "GET /api/devices/{id}/status",
            "device_heartbeat": "POST /api/devices/{id}/heartbeat"
        }
    }
