# -*- coding: utf-8 -*-
"""
Auth Service - Serviço de Autenticação e Autorização
Responsável por gerenciar autenticação JWT, registro e login de tenants
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from services.auth_service import auth_service
from services.rate_limiter import rate_limiter
from shared.database import DatabaseManager
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__, level=settings.LOG_LEVEL)

# Database manager para auth_schema
db_manager = DatabaseManager("auth_schema")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação
    Inicializa e fecha conexões com banco e Redis
    """
    # Startup
    logger.info("Iniciando auth-service...")
    
    # Inicializa database
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    logger.info("Database inicializado")
    
    # Inicializa serviços
    await auth_service.initialize()
    await rate_limiter.initialize()
    logger.info("Serviços inicializados")
    
    logger.info("Auth-service iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando auth-service...")
    await auth_service.close()
    await rate_limiter.close()
    await db_manager.close()
    logger.info("Auth-service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense Auth Service",
    description="Serviço de autenticação e autorização multi-tenant",
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

# Adiciona middleware de rate limiting
app.middleware("http")(rate_limiter.middleware)

# Registra routers
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """
    Endpoint de health check
    Verifica saúde do serviço e conexões
    """
    # Verifica conexão com banco
    db_healthy = await db_manager.health_check()
    
    # Verifica conexão com Redis
    redis_healthy = False
    try:
        if auth_service.redis_client:
            await auth_service.redis_client.ping()
            redis_healthy = True
    except Exception:
        pass
    
    status = "healthy" if (db_healthy and redis_healthy) else "degraded"
    
    return {
        "status": status,
        "service": "auth-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "description": "Serviço de autenticação e autorização multi-tenant",
        "endpoints": {
            "health": "/health",
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "refresh": "POST /api/auth/refresh",
            "logout": "POST /api/auth/logout"
        }
    }
