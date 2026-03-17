# -*- coding: utf-8 -*-
"""
RabbitMQ Client - Cliente para Mensageria Assíncrona
Gerencia conexões e operações com RabbitMQ
"""

import asyncio
import json
from typing import Dict, Any, Callable, Optional
import aio_pika
from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel, AbstractQueue

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class RabbitMQClient:
    """
    Cliente RabbitMQ para publicação e consumo de mensagens.
    
    Gerencia conexão robusta com RabbitMQ, suporta reconexão automática
    e fornece métodos para publicar e consumir mensagens.
    """
    
    def __init__(self):
        """Inicializa o cliente RabbitMQ"""
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.is_connected = False
        
        logger.info("RabbitMQClient inicializado")
    
    async def connect(self):
        """
        Conecta ao RabbitMQ.
        
        Estabelece conexão robusta que reconecta automaticamente
        em caso de falha.
        """
        try:
            # Conecta ao RabbitMQ
            self.connection = await connect_robust(
                settings.rabbitmq_url,
                loop=asyncio.get_event_loop()
            )
            
            # Cria canal
            self.channel = await self.connection.channel()
            
            # Configura QoS (prefetch)
            await self.channel.set_qos(prefetch_count=10)
            
            self.is_connected = True
            
            logger.info(
                "Conectado ao RabbitMQ",
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT
            )
            
        except Exception as e:
            logger.error("Erro ao conectar ao RabbitMQ", error=str(e), exc_info=True)
            self.is_connected = False
            raise
    
    async def close(self):
        """Fecha conexão com RabbitMQ"""
        try:
            if self.channel:
                await self.channel.close()
            
            if self.connection:
                await self.connection.close()
            
            self.is_connected = False
            
            logger.info("Conexão com RabbitMQ fechada")
            
        except Exception as e:
            logger.error("Erro ao fechar conexão com RabbitMQ", error=str(e))
    
    async def publish(self, queue_name: str, message: Dict[str, Any]):
        """
        Publica mensagem em uma fila.
        
        Args:
            queue_name: Nome da fila
            message: Mensagem a ser publicada (será serializada para JSON)
        
        Raises:
            Exception: Se não estiver conectado ou houver erro na publicação
        """
        if not self.is_connected or not self.channel:
            raise Exception("RabbitMQ não está conectado")
        
        try:
            # Declara fila (idempotente)
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True
            )
            
            # Serializa mensagem para JSON
            body = json.dumps(message).encode()
            
            # Cria mensagem com delivery_mode=2 (persistente)
            aio_message = Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Publica mensagem
            await self.channel.default_exchange.publish(
                aio_message,
                routing_key=queue_name
            )
            
            logger.debug(
                "Mensagem publicada",
                queue=queue_name,
                message_size=len(body)
            )
            
        except Exception as e:
            logger.error(
                "Erro ao publicar mensagem",
                queue=queue_name,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def consume(
        self,
        queue_name: str,
        callback: Callable[[Dict[str, Any]], Any],
        prefetch_count: int = 10
    ):
        """
        Consome mensagens de uma fila.
        
        Args:
            queue_name: Nome da fila
            callback: Função assíncrona para processar mensagens
            prefetch_count: Número de mensagens para prefetch
        
        Raises:
            Exception: Se não estiver conectado ou houver erro no consumo
        """
        if not self.is_connected or not self.channel:
            raise Exception("RabbitMQ não está conectado")
        
        try:
            # Declara fila (idempotente)
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True
            )
            
            # Configura QoS
            await self.channel.set_qos(prefetch_count=prefetch_count)
            
            logger.info(
                "Iniciando consumo de mensagens",
                queue=queue_name,
                prefetch_count=prefetch_count
            )
            
            # Processa mensagens
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            # Deserializa mensagem
                            body = json.loads(message.body.decode())
                            
                            logger.debug(
                                "Mensagem recebida",
                                queue=queue_name,
                                message_id=message.message_id
                            )
                            
                            # Chama callback
                            await callback(body)
                            
                        except Exception as e:
                            logger.error(
                                "Erro ao processar mensagem",
                                queue=queue_name,
                                error=str(e),
                                exc_info=True
                            )
                            # Mensagem será reprocessada (nack)
                            raise
            
        except Exception as e:
            logger.error(
                "Erro ao consumir mensagens",
                queue=queue_name,
                error=str(e),
                exc_info=True
            )
            raise


# Instância global (singleton)
_rabbitmq_client: Optional[RabbitMQClient] = None


async def get_rabbitmq_client() -> RabbitMQClient:
    """
    Retorna instância global do RabbitMQClient.
    
    Usado como dependency injection no FastAPI.
    
    Returns:
        RabbitMQClient: Instância do cliente
    """
    global _rabbitmq_client
    
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient()
        await _rabbitmq_client.connect()
    
    return _rabbitmq_client
