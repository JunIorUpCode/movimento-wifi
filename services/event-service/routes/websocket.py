# -*- coding: utf-8 -*-
"""
WebSocket Routes - Rotas WebSocket para Real-Time Updates
Task 17: Implementar WebSocket para real-time updates
Requisitos: 38.1-38.8, 1.5
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.logging import get_logger
from shared.websocket import websocket_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    Endpoint WebSocket para receber eventos em tempo real.
    
    **Task 17.1**: Endpoint WebSocket no api-gateway (wss://api.wifisense.com/ws)
    **Requisitos**: 38.1-38.3, 1.5
    
    **Autenticação**: Requer JWT token como query parameter
    - Valida JWT token na conexão
    - Extrai tenant_id do payload
    - Verifica role (tenant ou admin)
    
    **Isolamento Multi-Tenant** (Task 17.2): 
    - Canal isolado por tenant: tenant:{tenant_id}
    - Tenant A não recebe eventos de tenant B
    - Broadcast de eventos apenas para o canal do tenant
    
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
    
    Example:
        ```javascript
        // Frontend - Conectar ao WebSocket
        const token = localStorage.getItem('jwt_token');
        const ws = new WebSocket(`wss://api.wifisense.com/ws?token=${token}`);
        
        // Heartbeat a cada 30 segundos
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
        
        // Receber eventos
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'event') {
                console.log('Novo evento:', message.data);
            }
        };
        ```
    """
    tenant_id: Optional[UUID] = None
    last_heartbeat = datetime.utcnow()
    
    try:
        # ====================================================================
        # Task 17.1: Validar JWT token na conexão
        # ====================================================================
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
        
        # Extrai informações do payload
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
        
        # ====================================================================
        # Task 17.1: Registra conexão no canal isolado por tenant
        # ====================================================================
        await websocket_manager.connect(websocket, tenant_id)
        
        # Envia mensagem de boas-vindas
        await websocket.send_json({
            "type": "connected",
            "message": "Conectado ao WiFiSense Event Stream",
            "tenant_id": str(tenant_id),
            "channel": f"tenant:{tenant_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "heartbeat_interval": 30,  # segundos (Task 17.4)
            "idle_timeout": 300  # segundos - 5 minutos (Task 17.4)
        })
        
        # ====================================================================
        # Task 17.4: Loop de heartbeat e reconexão
        # ====================================================================
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


@router.get("/stats")
async def websocket_stats():
    """
    Retorna estatísticas das conexões WebSocket.
    
    Útil para monitoramento e debugging.
    
    Returns:
        dict: Estatísticas de conexões WebSocket
    """
    total_connections = websocket_manager.get_connection_count()
    
    return {
        "total_connections": total_connections,
        "timestamp": datetime.utcnow().isoformat()
    }
