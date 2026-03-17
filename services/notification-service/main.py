# -*- coding: utf-8 -*-
"""
Notification Service - Serviço de Notificações
Responsável por enviar notificações via Telegram, email e webhooks
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.notification_config import router as config_router
from routes.notification_logs import router as logs_router
from services.notification_worker import NotificationWorker
from shared.database import DatabaseManager
from shared.rabbitmq import RabbitMQClient
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__, level=settings.LOG_LEVEL)

# Database manager para notification_schema
db_manager = DatabaseManager("notification_schema")

# RabbitMQ client para consumir eventos
rabbitmq_client = None

# Notification worker
notification_worker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação.
    Inicializa e fecha conexões com banco e RabbitMQ.
    """
    global rabbitmq_client, notification_worker
    
    # Startup
    logger.info("Iniciando notification-service...")
    
    # Inicializa database
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    logger.info("Database inicializado")
    
    # Inicializa RabbitMQ
    rabbitmq_client = RabbitMQClient()
    await rabbitmq_client.connect()
    logger.info("RabbitMQ conectado")
    
    # Inicia notification worker
    notification_worker = NotificationWorker(db_manager, rabbitmq_client)
    notification_worker.start()
    logger.info("NotificationWorker iniciado")
    
    logger.info("Notification-service iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando notification-service...")
    
    # Para notification worker
    if notification_worker:
        notification_worker.stop()
    
    # Fecha RabbitMQ
    if rabbitmq_client:
        await rabbitmq_client.close()
    
    await db_manager.close()
    logger.info("Notification-service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense Notification Service",
    description="Serviço de notificações multi-canal (Telegram, Email, Webhook)",
    version="1.0.0",
    lifespan=lifespan
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra routers
app.include_router(config_router)
app.include_router(logs_router)


@app.get("/health")
async def health_check():
    """
    Endpoint de health check.
    Verifica saúde do serviço e conexões.
    """
    # Verifica conexão com banco
    db_healthy = await db_manager.health_check()
    
    # Verifica conexão com RabbitMQ
    rabbitmq_healthy = rabbitmq_client and rabbitmq_client.is_connected
    
    # Verifica notification worker
    worker_running = notification_worker and notification_worker.running
    
    # Determina status geral
    if db_healthy and rabbitmq_healthy and worker_running:
        status_str = "healthy"
    elif db_healthy and rabbitmq_healthy:
        status_str = "degraded"
    else:
        status_str = "unhealthy"
    
    return {
        "status": status_str,
        "service": "notification-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "rabbitmq": "healthy" if rabbitmq_healthy else "unhealthy",
        "notification_worker": "running" if worker_running else "stopped"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "notification-service",
        "version": "1.0.0",
        "description": "Serviço de notificações multi-canal (Telegram, Email, Webhook)",
        "endpoints": {
            "health": "/health",
            "get_config": "GET /api/notifications/config",
            "update_config": "PUT /api/notifications/config",
            "test_channel": "POST /api/notifications/test",
            "get_logs": "GET /api/notifications/logs"
        },
        "channels": ["telegram", "email", "webhook"],
        "features": [
            "Multi-tenant com isolamento completo",
            "Tokens criptografados (bot_token, API keys, secrets)",
            "Filtros: min_confidence, quiet_hours, cooldown",
            "Retry com exponential backoff",
            "Logs de todas as tentativas de envio"
        ]
    }

