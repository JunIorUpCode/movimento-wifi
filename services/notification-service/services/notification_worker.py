# -*- coding: utf-8 -*-
"""
Notification Worker - Worker de Processamento de Notificações
Consome eventos da fila RabbitMQ e envia notificações
"""

import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, time
import redis.asyncio as redis

from shared.database import DatabaseManager
from shared.rabbitmq import RabbitMQClient
from shared.config import settings
from shared.logging import get_logger
from services.notification_service import NotificationService
from channels.telegram_channel import TelegramChannel
from channels.email_channel import EmailChannel
from channels.webhook_channel import WebhookChannel

logger = get_logger(__name__)


class NotificationWorker:
    """
    Worker para processar notificações de eventos.
    
    **Responsabilidades**:
    - Consumir eventos da fila RabbitMQ
    - Carregar configuração de notificações do tenant
    - Aplicar filtros (min_confidence, quiet_hours, cooldown)
    - Enviar notificações para canais configurados
    - Registrar tentativas em notification_logs
    
    **Filtros Aplicados**:
    1. min_confidence: Só notifica se confidence >= threshold
    2. quiet_hours: Não notifica durante horários de silêncio
    3. cooldown: Evita spam com período de cooldown por tipo de evento
    """
    
    def __init__(self, db_manager: DatabaseManager, rabbitmq_client: RabbitMQClient):
        """
        Inicializa o worker de notificações.
        
        Args:
            db_manager: Gerenciador de banco de dados
            rabbitmq_client: Cliente RabbitMQ
        """
        self.db_manager = db_manager
        self.rabbitmq_client = rabbitmq_client
        self.running = False
        self.task = None
        
        # Redis para cooldown
        self.redis_client = None
        
        logger.info("NotificationWorker inicializado")
    
    async def _init_redis(self):
        """Inicializa conexão com Redis para cooldown"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis conectado para cooldown")
        except Exception as e:
            logger.error(f"Erro ao conectar Redis: {str(e)}", exc_info=True)
            raise
    
    def start(self):
        """
        Inicia o worker em background.
        
        Cria task assíncrona que consome mensagens da fila.
        """
        if self.running:
            logger.warning("Worker já está rodando")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run())
        
        logger.info("NotificationWorker iniciado")
    
    def stop(self):
        """
        Para o worker.
        
        Cancela task assíncrona e aguarda finalização.
        """
        if not self.running:
            logger.warning("Worker não está rodando")
            return
        
        self.running = False
        
        if self.task:
            self.task.cancel()
        
        logger.info("NotificationWorker parado")
    
    async def _run(self):
        """
        Loop principal do worker.
        
        Consome mensagens da fila 'notification_delivery' e processa.
        """
        try:
            # Inicializa Redis
            await self._init_redis()
            
            # Consome mensagens da fila
            await self.rabbitmq_client.consume(
                queue_name="notification_delivery",
                callback=self._process_notification,
                prefetch_count=5
            )
        
        except asyncio.CancelledError:
            logger.info("Worker cancelado")
        
        except Exception as e:
            logger.error(f"Erro no worker: {str(e)}", exc_info=True)
            self.running = False
    
    async def _process_notification(self, message: Dict[str, Any]):
        """
        Processa uma mensagem de notificação.
        
        **Pipeline**:
        1. Carrega configuração do tenant
        2. Aplica filtros (confidence, quiet_hours, cooldown)
        3. Envia para canais configurados
        4. Registra logs
        
        Args:
            message: Mensagem da fila com formato:
            {
                "tenant_id": "uuid",
                "event_id": "uuid",
                "event_type": "fall_suspected",
                "confidence": 0.95,
                "timestamp": "2024-01-01T12:00:00",
                "device_id": "uuid",
                "device_name": "Sala",
                "metadata": {}
            }
        """
        try:
            tenant_id = UUID(message["tenant_id"])
            event_id = UUID(message["event_id"])
            event_type = message["event_type"]
            confidence = message["confidence"]
            
            logger.info(
                "Processando notificação",
                tenant_id=str(tenant_id),
                event_id=str(event_id),
                event_type=event_type,
                confidence=confidence
            )
            
            # Carrega configuração do tenant
            async with self.db_manager.get_session() as session:
                config = await NotificationService.get_decrypted_config(session, tenant_id)
                
                if not config:
                    logger.warning(
                        "Configuração de notificação não encontrada",
                        tenant_id=str(tenant_id)
                    )
                    return
                
                # Verifica se notificações estão habilitadas
                if not config["enabled"]:
                    logger.debug(
                        "Notificações desabilitadas para tenant",
                        tenant_id=str(tenant_id)
                    )
                    return
                
                # Aplica filtro de confiança mínima
                if confidence < config["min_confidence"]:
                    logger.debug(
                        "Evento abaixo do threshold de confiança",
                        tenant_id=str(tenant_id),
                        confidence=confidence,
                        min_confidence=config["min_confidence"]
                    )
                    return
                
                # Aplica filtro de quiet hours
                if await self._is_quiet_hours(config["quiet_hours"]):
                    logger.debug(
                        "Notificação suprimida por quiet hours",
                        tenant_id=str(tenant_id)
                    )
                    return
                
                # Aplica filtro de cooldown
                if await self._is_in_cooldown(tenant_id, event_type, config["cooldown_seconds"]):
                    logger.debug(
                        "Notificação suprimida por cooldown",
                        tenant_id=str(tenant_id),
                        event_type=event_type
                    )
                    return
                
                # Envia para canais configurados
                await self._send_to_channels(
                    session=session,
                    config=config,
                    event_data=message
                )
                
                # Atualiza cooldown
                await self._set_cooldown(tenant_id, event_type, config["cooldown_seconds"])
        
        except Exception as e:
            logger.error(
                "Erro ao processar notificação",
                error=str(e),
                exc_info=True
            )
    
    async def _is_quiet_hours(self, quiet_hours: Optional[Dict[str, str]]) -> bool:
        """
        Verifica se está em horário de silêncio.
        
        Args:
            quiet_hours: Dict com "start" e "end" (formato HH:MM)
        
        Returns:
            bool: True se está em quiet hours, False caso contrário
        """
        if not quiet_hours:
            return False
        
        try:
            # Horário atual
            now = datetime.now().time()
            
            # Parse quiet hours
            start_str = quiet_hours["start"]
            end_str = quiet_hours["end"]
            
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
            
            # Verifica se está no intervalo
            if start_time <= end_time:
                # Intervalo normal (ex: 22:00 - 07:00 do dia seguinte)
                return start_time <= now <= end_time
            else:
                # Intervalo que cruza meia-noite (ex: 22:00 - 07:00)
                return now >= start_time or now <= end_time
        
        except Exception as e:
            logger.error(f"Erro ao verificar quiet hours: {str(e)}")
            return False
    
    async def _is_in_cooldown(
        self,
        tenant_id: UUID,
        event_type: str,
        cooldown_seconds: int
    ) -> bool:
        """
        Verifica se evento está em período de cooldown.
        
        **Cooldown**: Evita spam de notificações do mesmo tipo
        
        Args:
            tenant_id: ID do tenant
            event_type: Tipo do evento
            cooldown_seconds: Período de cooldown em segundos
        
        Returns:
            bool: True se está em cooldown, False caso contrário
        """
        if cooldown_seconds <= 0:
            return False
        
        try:
            # Chave Redis: cooldown:{tenant_id}:{event_type}
            key = f"cooldown:{tenant_id}:{event_type}"
            
            # Verifica se existe
            exists = await self.redis_client.exists(key)
            
            return exists > 0
        
        except Exception as e:
            logger.error(f"Erro ao verificar cooldown: {str(e)}")
            return False
    
    async def _set_cooldown(
        self,
        tenant_id: UUID,
        event_type: str,
        cooldown_seconds: int
    ):
        """
        Define cooldown para tipo de evento.
        
        Args:
            tenant_id: ID do tenant
            event_type: Tipo do evento
            cooldown_seconds: Período de cooldown em segundos
        """
        if cooldown_seconds <= 0:
            return
        
        try:
            # Chave Redis: cooldown:{tenant_id}:{event_type}
            key = f"cooldown:{tenant_id}:{event_type}"
            
            # Define com TTL
            await self.redis_client.setex(
                key,
                cooldown_seconds,
                "1"
            )
            
            logger.debug(
                "Cooldown definido",
                tenant_id=str(tenant_id),
                event_type=event_type,
                cooldown_seconds=cooldown_seconds
            )
        
        except Exception as e:
            logger.error(f"Erro ao definir cooldown: {str(e)}")
    
    async def _send_to_channels(
        self,
        session,
        config: Dict[str, Any],
        event_data: Dict[str, Any]
    ):
        """
        Envia notificação para todos os canais configurados.
        
        **Canais Suportados**: telegram, email, webhook
        
        **Logs**: Registra todas as tentativas em notification_logs
        
        Args:
            session: Sessão do banco de dados
            config: Configuração de notificações
            event_data: Dados do evento
        """
        tenant_id = UUID(event_data["tenant_id"])
        event_id = UUID(event_data["event_id"])
        channels = config["channels"]
        
        # Telegram
        if "telegram" in channels and config["telegram_bot_token"]:
            await self._send_telegram(
                session=session,
                tenant_id=tenant_id,
                event_id=event_id,
                bot_token=config["telegram_bot_token"],
                chat_ids=config["telegram_chat_ids"],
                event_data=event_data
            )
        
        # Email
        if "email" in channels and config["sendgrid_api_key"]:
            await self._send_email(
                session=session,
                tenant_id=tenant_id,
                event_id=event_id,
                api_key=config["sendgrid_api_key"],
                recipients=config["email_recipients"],
                event_data=event_data
            )
        
        # Webhook
        if "webhook" in channels and config["webhook_urls"]:
            await self._send_webhook(
                session=session,
                tenant_id=tenant_id,
                event_id=event_id,
                webhook_urls=config["webhook_urls"],
                webhook_secret=config["webhook_secret"],
                event_data=event_data
            )
    
    async def _send_telegram(
        self,
        session,
        tenant_id: UUID,
        event_id: UUID,
        bot_token: str,
        chat_ids: list,
        event_data: Dict[str, Any]
    ):
        """Envia notificação via Telegram"""
        try:
            channel = TelegramChannel(bot_token, chat_ids)
            result = await channel.send_notification(event_data)
            
            # Registra logs
            for chat_id in result.get("sent_to", []):
                await NotificationService.create_log(
                    session=session,
                    tenant_id=tenant_id,
                    event_id=event_id,
                    channel="telegram",
                    recipient=chat_id,
                    success=True,
                    alert_data=event_data,
                    response_data=result
                )
            
            for chat_id in result.get("failed", []):
                await NotificationService.create_log(
                    session=session,
                    tenant_id=tenant_id,
                    event_id=event_id,
                    channel="telegram",
                    recipient=chat_id,
                    success=False,
                    error_message=result.get("error"),
                    alert_data=event_data
                )
        
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {str(e)}", exc_info=True)
    
    async def _send_email(
        self,
        session,
        tenant_id: UUID,
        event_id: UUID,
        api_key: str,
        recipients: list,
        event_data: Dict[str, Any]
    ):
        """Envia notificação via Email"""
        try:
            channel = EmailChannel(api_key, recipients)
            result = await channel.send_notification(event_data)
            
            # Registra logs
            for recipient in result.get("sent_to", []):
                await NotificationService.create_log(
                    session=session,
                    tenant_id=tenant_id,
                    event_id=event_id,
                    channel="email",
                    recipient=recipient,
                    success=True,
                    alert_data=event_data,
                    response_data=result
                )
            
            for recipient in result.get("failed", []):
                await NotificationService.create_log(
                    session=session,
                    tenant_id=tenant_id,
                    event_id=event_id,
                    channel="email",
                    recipient=recipient,
                    success=False,
                    error_message=result.get("error"),
                    alert_data=event_data
                )
        
        except Exception as e:
            logger.error(f"Erro ao enviar Email: {str(e)}", exc_info=True)
    
    async def _send_webhook(
        self,
        session,
        tenant_id: UUID,
        event_id: UUID,
        webhook_urls: list,
        webhook_secret: Optional[str],
        event_data: Dict[str, Any]
    ):
        """Envia notificação via Webhook"""
        try:
            channel = WebhookChannel(webhook_urls, webhook_secret)
            result = await channel.send_notification(event_data)
            
            # Registra logs
            for url in result.get("sent_to", []):
                await NotificationService.create_log(
                    session=session,
                    tenant_id=tenant_id,
                    event_id=event_id,
                    channel="webhook",
                    recipient=url,
                    success=True,
                    alert_data=event_data,
                    response_data=result
                )
            
            for url in result.get("failed", []):
                await NotificationService.create_log(
                    session=session,
                    tenant_id=tenant_id,
                    event_id=event_id,
                    channel="webhook",
                    recipient=url,
                    success=False,
                    error_message=result.get("error"),
                    alert_data=event_data
                )
        
        except Exception as e:
            logger.error(f"Erro ao enviar Webhook: {str(e)}", exc_info=True)
