"""
Sistema de notificações - Serviço orquestrador.

O NotificationService é o orquestrador central de notificações:
- Gerencia múltiplos canais de notificação
- Valida se alerta deve ser enviado (confiança, cooldown, quiet hours)
- Envia alertas para todos os canais configurados
- Registra histórico de envios no banco de dados

Implementa:
- __init__ com setup de canais
- send_alert() com validações e logging
- _check_cooldown() para evitar spam
- _is_quiet_hours() para horários de silêncio
- _log_notification() para persistir logs no banco
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session
from app.models.models import NotificationLog

from .notification_types import Alert, NotificationChannel, NotificationConfig

logger = logging.getLogger(__name__)


class NotificationService:
    """Serviço de gerenciamento de notificações.
    
    Singleton pattern para instância global.
    Orquestra o envio de alertas para múltiplos canais com validações.
    """
    
    _instance: Optional['NotificationService'] = None
    
    def __new__(cls, config: Optional[NotificationConfig] = None):
        """Implementa singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        """Inicializa serviço de notificações.
        
        Args:
            config: Configuração de notificações. Se None, usa configuração padrão.
        """
        # Evita reinicialização em chamadas subsequentes (singleton)
        if self._initialized:
            return
        
        self._initialized = True
        self._config = config or self._load_config_from_env()
        self._channels: Dict[str, NotificationChannel] = {}
        self._last_notification: Dict[str, float] = {}

        # Setup inicial de canais
        self._setup_channels()
        
        logger.info(
            f"NotificationService initialized with {len(self._channels)} channels: "
            f"{list(self._channels.keys())}"
        )
    
    @staticmethod
    def _load_config_from_env() -> NotificationConfig:
        """Carrega configuração de notificação das variáveis de ambiente."""
        channels = []
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        raw_ids = os.getenv("TELEGRAM_CHAT_IDS", "").strip()
        chat_ids = [c.strip() for c in raw_ids.split(",") if c.strip()] if raw_ids else []

        if bot_token and chat_ids:
            channels.append("telegram")
            logger.info(f"[NotificationService] Telegram carregado do .env ({len(chat_ids)} chat(s))")

        return NotificationConfig(
            enabled=True,
            channels=channels,
            telegram_bot_token=bot_token or None,
            telegram_chat_ids=chat_ids,
            min_confidence=float(os.getenv("NOTIFICATION_MIN_CONFIDENCE", "0.7")),
            cooldown_seconds=int(os.getenv("NOTIFICATION_COOLDOWN", "300")),
        )

    def _setup_channels(self) -> None:
        """Configura canais de notificação baseado na configuração.

        Instancia canais apenas se estiverem configurados corretamente:
        - Telegram: requer bot_token e chat_ids
        - WhatsApp: requer account_sid, auth_token, from_number e recipients
        - Webhook: requer urls
        """
        # Telegram
        if "telegram" in self._config.channels and self._config.telegram_bot_token:
            if self._config.telegram_chat_ids:
                try:
                    # Import dinâmico para evitar dependências circulares
                    from .notification_channels import TelegramChannel
                    self._channels["telegram"] = TelegramChannel(
                        self._config.telegram_bot_token,
                        self._config.telegram_chat_ids
                    )
                    logger.info("Telegram channel configured")
                except ImportError:
                    logger.warning("TelegramChannel not available")
            else:
                logger.warning("Telegram enabled but no chat_ids configured")
        
        # WhatsApp
        if "whatsapp" in self._config.channels and self._config.twilio_account_sid:
            if (self._config.twilio_auth_token and 
                self._config.twilio_whatsapp_from and 
                self._config.whatsapp_recipients):
                try:
                    from .notification_channels import WhatsAppChannel
                    self._channels["whatsapp"] = WhatsAppChannel(
                        self._config.twilio_account_sid,
                        self._config.twilio_auth_token,
                        self._config.twilio_whatsapp_from,
                        self._config.whatsapp_recipients
                    )
                    logger.info("WhatsApp channel configured")
                except ImportError:
                    logger.warning("WhatsAppChannel not available")
            else:
                logger.warning("WhatsApp enabled but incomplete configuration")
        
        # Webhook
        if "webhook" in self._config.channels and self._config.webhook_urls:
            try:
                from .notification_channels import WebhookChannel
                self._channels["webhook"] = WebhookChannel(
                    self._config.webhook_urls,
                    self._config.webhook_secret
                )
                logger.info(f"Webhook channel configured with {len(self._config.webhook_urls)} URLs")
            except ImportError:
                logger.warning("WebhookChannel not available")
    
    async def send_alert(self, alert: Alert) -> None:
        """Envia alerta para todos os canais configurados.
        
        Aplica validações antes de enviar:
        1. Verifica se notificações estão habilitadas
        2. Verifica confiança mínima
        3. Verifica cooldown por tipo de evento
        4. Verifica quiet hours
        
        Args:
            alert: Alerta a ser enviado
        """
        if not self._config.enabled:
            logger.debug("Notifications disabled, skipping alert")
            return
        
        # Validação 1: Confiança mínima
        if alert.confidence < self._config.min_confidence:
            logger.debug(
                f"Alert confidence {alert.confidence:.2f} below minimum "
                f"{self._config.min_confidence:.2f}, skipping"
            )
            return
        
        # Validação 2: Cooldown
        if not self._check_cooldown(alert.event_type):
            logger.debug(
                f"Alert type '{alert.event_type}' in cooldown period, skipping"
            )
            return
        
        # Validação 3: Quiet hours
        if self._is_quiet_hours():
            logger.debug("Currently in quiet hours, skipping alert")
            return
        
        # Envia para todos os canais configurados
        if not self._channels:
            logger.warning("No notification channels configured")
            return
        
        logger.info(
            f"Sending alert: type={alert.event_type}, confidence={alert.confidence:.2f}, "
            f"channels={list(self._channels.keys())}"
        )
        
        # Envia para cada canal em paralelo
        tasks = []
        for channel_name, channel in self._channels.items():
            tasks.append(self._send_to_channel(channel_name, channel, alert))
        
        # Aguarda todos os envios (captura exceções individualmente)
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Atualiza timestamp do último envio para este tipo de evento
        self._last_notification[alert.event_type] = time.time()
        
        logger.info(f"Alert sent successfully to {len(self._channels)} channels")
    
    def _check_cooldown(self, event_type: str) -> bool:
        """Verifica se cooldown expirou para o tipo de evento.
        
        Implementa cooldown por tipo de evento para evitar spam.
        Cada tipo de evento tem seu próprio timer de cooldown.
        
        Args:
            event_type: Tipo do evento a verificar
            
        Returns:
            True se cooldown expirou (pode enviar), False caso contrário
        """
        last_time = self._last_notification.get(event_type, 0)
        elapsed = time.time() - last_time
        
        # Cooldown expirou se tempo decorrido >= cooldown configurado
        cooldown_expired = elapsed >= self._config.cooldown_seconds
        
        if not cooldown_expired:
            remaining = self._config.cooldown_seconds - elapsed
            logger.debug(
                f"Cooldown active for '{event_type}': {remaining:.0f}s remaining"
            )
        
        return cooldown_expired
    
    def _is_quiet_hours(self) -> bool:
        """Verifica se está em horário de silêncio.
        
        Quiet hours são períodos configurados onde notificações não devem ser enviadas.
        Suporta períodos que atravessam meia-noite (ex: 22h-7h).
        
        Returns:
            True se está em quiet hours, False caso contrário
        """
        if not self._config.quiet_hours:
            return False
        
        now = datetime.now()
        current_hour = now.hour
        
        for start, end in self._config.quiet_hours:
            if start < end:
                # Período normal (ex: 22h-23h)
                if start <= current_hour < end:
                    logger.debug(
                        f"In quiet hours: {start:02d}:00-{end:02d}:00 "
                        f"(current: {current_hour:02d}:00)"
                    )
                    return True
            else:
                # Período atravessa meia-noite (ex: 22h-7h)
                if current_hour >= start or current_hour < end:
                    logger.debug(
                        f"In quiet hours: {start:02d}:00-{end:02d}:00 "
                        f"(current: {current_hour:02d}:00)"
                    )
                    return True
        
        return False
    
    async def _send_to_channel(
        self, 
        name: str, 
        channel: NotificationChannel, 
        alert: Alert
    ) -> None:
        """Envia alerta para um canal específico e registra no banco.
        
        Captura e registra exceções para não interromper envio para outros canais.
        Persiste log de cada tentativa de envio no banco de dados.
        
        Args:
            name: Nome do canal
            channel: Instância do canal
            alert: Alerta a ser enviado
        """
        success = False
        error_message = None
        recipient = "unknown"
        
        try:
            # Extrai recipient baseado no tipo de canal
            recipient = self._get_recipient_for_channel(name, channel)
            
            # Tenta enviar
            success = await channel.send(alert)
            
            if success:
                logger.info(f"Alert sent successfully via {name}")
            else:
                error_message = "Channel returned False (send failed)"
                logger.error(f"Failed to send alert via {name}")
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error sending alert via {name}: {e}", exc_info=True)
        
        finally:
            # Registra log no banco de dados
            await self._log_notification(
                channel=name,
                event_type=alert.event_type,
                confidence=alert.confidence,
                recipient=recipient,
                success=success,
                error_message=error_message,
                alert_data=alert.to_dict()
            )
    
    def _get_recipient_for_channel(self, channel_name: str, channel: NotificationChannel) -> str:
        """Extrai informação do destinatário baseado no tipo de canal.
        
        Args:
            channel_name: Nome do canal
            channel: Instância do canal
            
        Returns:
            String representando o destinatário
        """
        if channel_name == "telegram":
            # Retorna primeiro chat_id ou lista de chat_ids
            chat_ids = self._config.telegram_chat_ids
            if chat_ids:
                return chat_ids[0] if len(chat_ids) == 1 else f"{len(chat_ids)} recipients"
            return "unknown"
        
        elif channel_name == "whatsapp":
            # Retorna primeiro recipient ou lista de recipients
            recipients = self._config.whatsapp_recipients
            if recipients:
                return recipients[0] if len(recipients) == 1 else f"{len(recipients)} recipients"
            return "unknown"
        
        elif channel_name == "webhook":
            # Retorna primeira URL ou número de URLs
            urls = self._config.webhook_urls
            if urls:
                return urls[0] if len(urls) == 1 else f"{len(urls)} webhooks"
            return "unknown"
        
        return "unknown"
    
    async def _log_notification(
        self,
        channel: str,
        event_type: str,
        confidence: float,
        recipient: str,
        success: bool,
        error_message: Optional[str],
        alert_data: dict
    ) -> None:
        """Persiste log de notificação no banco de dados.
        
        Args:
            channel: Nome do canal (telegram, whatsapp, webhook)
            event_type: Tipo do evento
            confidence: Confiança da detecção
            recipient: Destinatário da notificação
            success: Se o envio foi bem-sucedido
            error_message: Mensagem de erro (se houver)
            alert_data: Dados completos do alerta
        """
        try:
            # Garante que alert_data seja serializável
            # Converte valores não serializáveis para string
            serializable_data = {}
            for key, value in alert_data.items():
                try:
                    json.dumps(value)
                    serializable_data[key] = value
                except (TypeError, ValueError):
                    serializable_data[key] = str(value)
            
            async with async_session() as db:
                log_entry = NotificationLog(
                    timestamp=datetime.utcnow(),
                    channel=channel,
                    event_type=event_type,
                    confidence=confidence,
                    recipient=recipient,
                    success=success,
                    error_message=error_message,
                    alert_data=json.dumps(serializable_data)
                )
                db.add(log_entry)
                await db.commit()
                
                logger.debug(
                    f"Notification log saved: channel={channel}, "
                    f"event_type={event_type}, success={success}"
                )
        except Exception as e:
            # Não propaga exceção para não interromper fluxo de notificações
            logger.error(f"Failed to save notification log: {e}", exc_info=True)

        # Broadcast WebSocket — import tardio para evitar dependência circular
        try:
            from app.services.monitor_service import monitor_service  # noqa: PLC0415
            import asyncio as _asyncio
            if _asyncio.get_event_loop().is_running():
                _asyncio.ensure_future(
                    monitor_service.broadcast_notification_sent(
                        channel=channel,
                        event_type=event_type,
                        confidence=confidence,
                        success=success,
                        recipient=recipient,
                    )
                )
        except Exception as _ws_err:
            logger.debug(f"Broadcast WebSocket de notificação falhou (não crítico): {_ws_err}")

    def update_config(self, config: NotificationConfig) -> None:
        """Atualiza configuração e reconstrói canais.
        
        Args:
            config: Nova configuração
        """
        self._config = config
        self._channels.clear()
        self._setup_channels()
        logger.info("NotificationService configuration updated")
    
    def get_last_notification_time(self, event_type: str) -> Optional[float]:
        """Retorna timestamp da última notificação para um tipo de evento.
        
        Args:
            event_type: Tipo do evento
            
        Returns:
            Timestamp da última notificação ou None se nunca enviou
        """
        return self._last_notification.get(event_type)
    
    def reset_cooldown(self, event_type: Optional[str] = None) -> None:
        """Reseta cooldown para um tipo de evento ou todos.
        
        Args:
            event_type: Tipo do evento. Se None, reseta todos.
        """
        if event_type:
            self._last_notification.pop(event_type, None)
            logger.info(f"Cooldown reset for '{event_type}'")
        else:
            self._last_notification.clear()
            logger.info("All cooldowns reset")
