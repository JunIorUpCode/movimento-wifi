# -*- coding: utf-8 -*-
"""
Event Processor - Worker de Processamento de Eventos
Consome dados da fila RabbitMQ e processa eventos
"""

import asyncio
import json
from typing import Dict, Any
from datetime import datetime
from uuid import UUID

from shared.logging import get_logger
from shared.rabbitmq import RabbitMQClient
from shared.database import DatabaseManager
from shared.websocket import websocket_manager
from .event_detector import EventDetector
from models.event import Event

logger = get_logger(__name__)


class EventProcessor:
    """
    Worker que processa dados de dispositivos e detecta eventos.
    
    Consome mensagens da fila RabbitMQ, executa algoritmos de detecção,
    persiste eventos no banco e publica para WebSocket.
    """
    
    def __init__(self, db_manager: DatabaseManager, rabbitmq_client: RabbitMQClient):
        """
        Inicializa o processador de eventos.
        
        Args:
            db_manager: Gerenciador de banco de dados
            rabbitmq_client: Cliente RabbitMQ para consumir mensagens
        """
        self.db_manager = db_manager
        self.rabbitmq_client = rabbitmq_client
        self.running = False
        self._task = None
        
        logger.info("EventProcessor inicializado")
    
    def start(self):
        """Inicia o worker de processamento"""
        if not self.running:
            self.running = True
            self._task = asyncio.create_task(self._run())
            logger.info("EventProcessor iniciado")
    
    def stop(self):
        """Para o worker de processamento"""
        if self.running:
            self.running = False
            if self._task:
                self._task.cancel()
            logger.info("EventProcessor parado")
    
    async def _run(self):
        """Loop principal do worker"""
        try:
            await self.rabbitmq_client.consume(
                queue_name="event_processing",
                callback=self._process_message
            )
        except asyncio.CancelledError:
            logger.info("EventProcessor cancelado")
        except Exception as e:
            logger.error("Erro no EventProcessor", error=str(e), exc_info=True)
    
    async def _process_message(self, message: Dict[str, Any]):
        """
        Processa uma mensagem da fila.
        
        Args:
            message: Mensagem contendo dados do dispositivo
        """
        try:
            tenant_id = UUID(message["tenant_id"])
            device_id = UUID(message["device_id"])
            features = message["features"]
            timestamp = datetime.fromtimestamp(message["timestamp"])
            data_type = message.get("data_type", "rssi")
            
            logger.info(
                "Processando dados do dispositivo",
                tenant_id=str(tenant_id),
                device_id=str(device_id),
                data_type=data_type
            )
            
            # Carrega configuração do tenant
            config = await self._get_tenant_config(tenant_id)
            
            # Executa detecção
            detector = EventDetector(config)
            result = detector.detect(features, data_type)
            
            if result is None:
                logger.debug("Nenhum evento detectado")
                return
            
            # Verifica se deve persistir (confidence >= min_confidence_to_store)
            min_confidence_to_store = config.get("min_confidence_to_store", 0.7)
            if result.confidence < min_confidence_to_store:
                logger.debug(
                    "Evento descartado (confidence baixa)",
                    confidence=result.confidence,
                    min_confidence=min_confidence_to_store
                )
                return
            
            # Persiste evento no banco
            event_id = await self._store_event(
                tenant_id=tenant_id,
                device_id=device_id,
                event_type=result.event_type,
                confidence=result.confidence,
                timestamp=timestamp,
                event_metadata=result.metadata
            )
            
            logger.info(
                "Evento detectado e persistido",
                event_id=str(event_id),
                event_type=result.event_type,
                confidence=result.confidence
            )
            
            # Verifica se deve notificar
            min_confidence_to_notify = config.get("min_confidence_to_notify", 0.8)
            if result.confidence >= min_confidence_to_notify:
                await self._queue_notification(
                    tenant_id=tenant_id,
                    event_id=event_id,
                    event_type=result.event_type,
                    confidence=result.confidence
                )
            
            # Broadcast via WebSocket
            await self._broadcast_event(
                tenant_id=tenant_id,
                event_data={
                    "event_id": str(event_id),
                    "device_id": str(device_id),
                    "event_type": result.event_type,
                    "confidence": result.confidence,
                    "timestamp": timestamp.isoformat(),
                    "metadata": result.metadata
                }
            )
            
        except Exception as e:
            logger.error(
                "Erro ao processar mensagem",
                error=str(e),
                message=message,
                exc_info=True
            )
    
    async def _get_tenant_config(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Carrega configuração do tenant do banco de dados.
        
        Args:
            tenant_id: ID do tenant
        
        Returns:
            Dict com configuração do tenant
        """
        # TODO: Implementar cache Redis para configurações
        # Por enquanto, retorna configuração padrão
        
        async with self.db_manager.get_session() as session:
            # Query para buscar tenant e seu plano
            # Por simplicidade, retornando config padrão
            return {
                "plan_type": "basic",
                "presence_threshold": 0.6,
                "low_variance_threshold": 0.2,
                "high_variance_threshold": 0.4,
                "movement_threshold": 0.5,
                "fall_threshold": 0.7,
                "inactivity_threshold": 300,
                "min_confidence_to_store": 0.7,
                "min_confidence_to_notify": 0.8
            }
    
    async def _store_event(
        self,
        tenant_id: UUID,
        device_id: UUID,
        event_type: str,
        confidence: float,
        timestamp: datetime,
        event_metadata: Dict[str, Any]
    ) -> UUID:
        """
        Persiste evento no banco de dados.
        
        Args:
            tenant_id: ID do tenant
            device_id: ID do dispositivo
            event_type: Tipo do evento
            confidence: Confiança da detecção
            timestamp: Timestamp do evento
            event_metadata: Metadados do evento
        
        Returns:
            UUID do evento criado
        """
        async with self.db_manager.get_session() as session:
            event = Event(
                tenant_id=tenant_id,
                device_id=device_id,
                event_type=event_type,
                confidence=confidence,
                timestamp=timestamp,
                event_metadata=event_metadata
            )
            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            
            return event.id
    
    async def _queue_notification(
        self,
        tenant_id: UUID,
        event_id: UUID,
        event_type: str,
        confidence: float
    ):
        """
        Publica tarefa de notificação na fila.
        
        Args:
            tenant_id: ID do tenant
            event_id: ID do evento
            event_type: Tipo do evento
            confidence: Confiança da detecção
        """
        message = {
            "tenant_id": str(tenant_id),
            "event_id": str(event_id),
            "event_type": event_type,
            "confidence": confidence,
            "channels": ["telegram", "email", "webhook"]  # Configurável por tenant
        }
        
        await self.rabbitmq_client.publish(
            queue_name="notification_delivery",
            message=message
        )
        
        logger.info(
            "Notificação enfileirada",
            event_id=str(event_id),
            event_type=event_type
        )
    
    async def _broadcast_event(self, tenant_id: UUID, event_data: Dict[str, Any]):
        """
        Publica evento no canal WebSocket do tenant.
        
        Garante isolamento multi-tenant: apenas clientes conectados
        do tenant específico recebem o evento.
        
        Args:
            tenant_id: ID do tenant
            event_data: Dados do evento para broadcast
        """
        try:
            await websocket_manager.broadcast_to_tenant(
                tenant_id=tenant_id,
                message={
                    "type": "event",
                    "data": event_data
                }
            )
            
            logger.info(
                "Evento broadcast via WebSocket",
                tenant_id=str(tenant_id),
                event_type=event_data["event_type"]
            )
            
        except Exception as e:
            logger.error(
                "Erro ao fazer broadcast do evento",
                tenant_id=str(tenant_id),
                error=str(e),
                exc_info=True
            )
