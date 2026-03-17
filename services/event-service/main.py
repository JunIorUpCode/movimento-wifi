# -*- coding: utf-8 -*-
"""
Event Service - Serviço de Processamento de Eventos
Responsável por processar dados de sinais Wi-Fi e detectar eventos
"""

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import jwt
from uuid import UUID
from datetime import datetime

from routes.event import router as event_router
from routes.device_data import router as device_data_router
from services.event_processor import EventProcessor
from shared.database import DatabaseManager
from shared.rabbitmq import RabbitMQClient
from shared.websocket import websocket_manager
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__, level=settings.LOG_LEVEL)

# Database manager para event_schema
db_manager = DatabaseManager("event_schema")

# RabbitMQ client para processamento assíncrono
rabbitmq_client = None

# Event processor worker
event_processor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação.
    Inicializa e fecha conexões com banco e RabbitMQ.
    """
    global rabbitmq_client, event_processor
    
    # Startup
    logger.info("Iniciando event-service...")
    
    # Inicializa database
    await db_manager.initialize()
    await db_manager.create_schema()
    await db_manager.create_tables()
    logger.info("Database inicializado")
    
    # Inicializa RabbitMQ
    rabbitmq_client = RabbitMQClient()
    await rabbitmq_client.connect()
    logger.info("RabbitMQ conectado")
    
    # Inicia event processor worker
    event_processor = EventProcessor(db_manager, rabbitmq_client)
    event_processor.start()
    logger.info("EventProcessor iniciado")
    
    logger.info("Event-service iniciado com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando event-service...")
    
    # Para event processor
    if event_processor:
        event_processor.stop()
    
    # Fecha RabbitMQ
    if rabbitmq_client:
        await rabbitmq_client.close()
    
    await db_manager.close()
    logger.info("Event-service encerrado")


# Cria aplicação FastAPI
app = FastAPI(
    title="WiFiSense Event Service",
    description="Serviço de processamento de eventos multi-tenant",
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
app.include_router(event_router)
app.include_router(device_data_router)


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
    
    # Verifica event processor
    processor_running = event_processor and event_processor.running
    
    # Determina status geral
    if db_healthy and rabbitmq_healthy and processor_running:
        status_str = "healthy"
    elif db_healthy and rabbitmq_healthy:
        status_str = "degraded"
    else:
        status_str = "unhealthy"
    
    return {
        "status": status_str,
        "service": "event-service",
        "version": "1.0.0",
        "database": "healthy" if db_healthy else "unhealthy",
        "rabbitmq": "healthy" if rabbitmq_healthy else "unhealthy",
        "event_processor": "running" if processor_running else "stopped"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações do serviço"""
    return {
        "service": "event-service",
        "version": "1.0.0",
        "description": "Serviço de processamento de eventos multi-tenant",
        "endpoints": {
            "health": "/health",
            "submit_data": "POST /api/devices/{id}/data",
            "list_events": "GET /api/events",
            "get_event": "GET /api/events/{id}",
            "event_timeline": "GET /api/events/timeline",
            "event_stats": "GET /api/events/stats",
            "event_feedback": "POST /api/events/{id}/feedback",
            "websocket": "WS /ws"
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    Endpoint WebSocket para receber eventos em tempo real.
    
    **Task 17.1**: Endpoint WebSocket no api-gateway (wss://api.wifisense.com/ws)
    **Requisitos**: 38.1-38.3, 1.5
    
    **Autenticação**: Requer JWT token como query parameter
    - Valida JWT token na conexão
    - Extrai tenant_id do payload
    - Verifica role (tenant ou admin)
    
    **Isolamento Multi-Tenant**: Cada tenant recebe apenas seus próprios eventos
    - Canal isolado por tenant: tenant:{tenant_id}
    - Tenant A não recebe eventos de tenant B
    
    **Formato de Mensagens**:
    ```json
    {
        "type": "event",
        "data": {
            "event_id": "uuid",
            "device_id": "uuid",
            "event_type": "presence|movement|fall_suspected|prolonged_inactivity",
            "confidence": 0.85,
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {}
        }
    }
    ```
    
    **Heartbeat** (Task 17.4): 
    - Cliente deve enviar ping a cada 30 segundos
    - Servidor responde com pong
    - Conexões idle são fechadas após 5 minutos (300 segundos)
    
    **Reconexão Automática** (Task 17.4):
    - Frontend deve implementar reconexão automática
    - Usar exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (máximo)
    
    Args:
        websocket: Conexão WebSocket
        token: JWT token para autenticação (query parameter)
    
    Raises:
        WebSocketDisconnect: Quando cliente desconecta
        jwt.ExpiredSignatureError: Token expirado
        jwt.InvalidTokenError: Token inválido
    """
    tenant_id = None
    last_heartbeat = datetime.utcnow()
    
    try:
        # Task 17.1: Validar JWT token na conexão
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Token WebSocket expirado")
            await websocket.close(code=1008, reason="Token expirado")
            return
        except jwt.InvalidTokenError as e:
            logger.warning("Token WebSocket inválido", error=str(e))
            await websocket.close(code=1008, reason="Token inválido")
            return
        
        # Extrai tenant_id do payload
        tenant_id = UUID(payload.get("sub"))
        role = payload.get("role")
        email = payload.get("email", "unknown")
        
        # Verifica role (tenant ou admin)
        if role not in ["tenant", "admin"]:
            logger.warning(
                "Role inválida para WebSocket",
                tenant_id=str(tenant_id),
                role=role
            )
            await websocket.close(code=1008, reason="Role inválida")
            return
        
        logger.info(
            "WebSocket autenticado com sucesso",
            tenant_id=str(tenant_id),
            role=role,
            email=email
        )
        
        # Task 17.1: Registra conexão no canal isolado por tenant
        await websocket_manager.connect(websocket, tenant_id)
        
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "connected",
            "message": "Conectado ao WiFiSense Event Stream",
            "tenant_id": str(tenant_id),
            "channel": f"tenant:{tenant_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "heartbeat_interval": 30,  # segundos
            "idle_timeout": 300  # segundos (5 minutos)
        })
        
        # Task 17.4: Loop de heartbeat e reconexão
        # Cliente deve enviar ping a cada 30 segundos
        # Servidor fecha conexão após 5 minutos (300s) sem heartbeat
        while True:
            try:
                # Aguarda mensagem do cliente com timeout de 300 segundos (5 minutos)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=300.0  # Task 17.4: Fechar idle após 5 minutos
                )
                
                # Atualiza timestamp do último heartbeat
                last_heartbeat = datetime.utcnow()
                
                # Task 17.4: Responde a ping com pong
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": last_heartbeat.isoformat()
                    })
                    logger.debug(
                        "Heartbeat recebido",
                        tenant_id=str(tenant_id)
                    )
                
            except asyncio.TimeoutError:
                # Task 17.4: Cliente não enviou heartbeat por 5 minutos
                # Fecha conexão idle
                idle_duration = (datetime.utcnow() - last_heartbeat).total_seconds()
                logger.warning(
                    "WebSocket idle timeout - fechando conexão",
                    tenant_id=str(tenant_id),
                    idle_duration_seconds=idle_duration
                )
                await websocket.close(
                    code=1000,
                    reason="Idle timeout - sem heartbeat por 5 minutos"
                )
                break
            
    except WebSocketDisconnect:
        logger.info(
            "WebSocket desconectado pelo cliente",
            tenant_id=str(tenant_id) if tenant_id else "unknown"
        )
    
    except Exception as e:
        logger.error(
            "Erro inesperado no WebSocket",
            tenant_id=str(tenant_id) if tenant_id else "unknown",
            error=str(e),
            exc_info=True
        )
        try:
            await websocket.close(code=1011, reason="Erro interno do servidor")
        except:
            pass
    
    finally:
        # Remove conexão do canal do tenant
        if tenant_id:
            await websocket_manager.disconnect(websocket, tenant_id)
            logger.info(
                "WebSocket removido do canal do tenant",
                tenant_id=str(tenant_id)
            )

