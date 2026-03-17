# -*- coding: utf-8 -*-
"""
WebSocket Manager - Gerenciador de Conexões WebSocket
Gerencia broadcast de eventos para clientes conectados com isolamento multi-tenant
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional
from uuid import UUID
from fastapi import WebSocket
from shared.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Gerenciador de conexões WebSocket multi-tenant.
    
    Mantém conexões organizadas por tenant_id para garantir
    isolamento: tenant A não recebe eventos de tenant B.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de WebSocket"""
        # Dicionário: tenant_id -> Set[WebSocket]
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        
        logger.info("WebSocketManager inicializado")
    
    async def connect(self, websocket: WebSocket, tenant_id: UUID):
        """
        Registra nova conexão WebSocket para um tenant.
        
        Args:
            websocket: Conexão WebSocket
            tenant_id: ID do tenant
        """
        await websocket.accept()
        
        async with self._lock:
            tenant_key = str(tenant_id)
            
            if tenant_key not in self._connections:
                self._connections[tenant_key] = set()
            
            self._connections[tenant_key].add(websocket)
        
        logger.info(
            "WebSocket conectado",
            tenant_id=tenant_key,
            total_connections=len(self._connections[tenant_key])
        )
    
    async def disconnect(self, websocket: WebSocket, tenant_id: UUID):
        """
        Remove conexão WebSocket de um tenant.
        
        Args:
            websocket: Conexão WebSocket
            tenant_id: ID do tenant
        """
        async with self._lock:
            tenant_key = str(tenant_id)
            
            if tenant_key in self._connections:
                self._connections[tenant_key].discard(websocket)
                
                # Remove tenant se não há mais conexões
                if not self._connections[tenant_key]:
                    del self._connections[tenant_key]
        
        logger.info(
            "WebSocket desconectado",
            tenant_id=tenant_key
        )
    
    async def broadcast_to_tenant(self, tenant_id: UUID, message: Dict[str, Any]):
        """
        Envia mensagem para todas as conexões de um tenant específico.
        
        Garante isolamento multi-tenant: apenas clientes do tenant
        especificado recebem a mensagem.
        
        Args:
            tenant_id: ID do tenant
            message: Mensagem a ser enviada (será serializada para JSON)
        """
        tenant_key = str(tenant_id)
        
        async with self._lock:
            connections = self._connections.get(tenant_key, set()).copy()
        
        if not connections:
            logger.debug(
                "Nenhuma conexão WebSocket para tenant",
                tenant_id=tenant_key
            )
            return
        
        # Serializa mensagem
        message_json = json.dumps(message)
        
        # Envia para todas as conexões do tenant
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(
                    "Erro ao enviar mensagem WebSocket",
                    tenant_id=tenant_key,
                    error=str(e)
                )
                disconnected.append(websocket)
        
        # Remove conexões que falharam
        if disconnected:
            async with self._lock:
                if tenant_key in self._connections:
                    for ws in disconnected:
                        self._connections[tenant_key].discard(ws)
        
        logger.info(
            "Mensagem broadcast para tenant",
            tenant_id=tenant_key,
            connections=len(connections),
            failed=len(disconnected)
        )
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """
        Envia mensagem para todas as conexões (todos os tenants).
        
        Usado para mensagens globais do sistema.
        
        Args:
            message: Mensagem a ser enviada
        """
        async with self._lock:
            all_connections = []
            for connections in self._connections.values():
                all_connections.extend(connections)
        
        message_json = json.dumps(message)
        
        for websocket in all_connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning("Erro ao enviar mensagem broadcast", error=str(e))
        
        logger.info(
            "Mensagem broadcast para todos",
            total_connections=len(all_connections)
        )
    
    def get_connection_count(self, tenant_id: Optional[UUID] = None) -> int:
        """
        Retorna número de conexões ativas.
        
        Args:
            tenant_id: ID do tenant (opcional). Se None, retorna total global.
        
        Returns:
            Número de conexões ativas
        """
        if tenant_id:
            tenant_key = str(tenant_id)
            return len(self._connections.get(tenant_key, set()))
        else:
            return sum(len(conns) for conns in self._connections.values())


# Instância global (singleton)
websocket_manager = WebSocketManager()
