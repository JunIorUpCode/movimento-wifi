"""
Canais de notificação concretos.

Implementações de NotificationChannel para diferentes plataformas:
- TelegramChannel: Envia notificações via Telegram Bot API
- WhatsAppChannel: Envia notificações via Twilio WhatsApp API
- WebhookChannel: Envia notificações via HTTP POST
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from typing import List, Optional

import aiohttp

from .notification_types import Alert, NotificationChannel

logger = logging.getLogger(__name__)


class TelegramChannel(NotificationChannel):
    """Canal de notificação via Telegram Bot API.
    
    Envia mensagens formatadas em Markdown para múltiplos chat_ids.
    Implementa retry com backoff exponencial (3 tentativas).
    """
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        """Inicializa canal Telegram.
        
        Args:
            bot_token: Token do bot Telegram
            chat_ids: Lista de chat IDs para enviar mensagens
        """
        self._bot_token = bot_token
        self._chat_ids = chat_ids
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._max_retries = 3
        
        logger.info(f"TelegramChannel initialized with {len(chat_ids)} chat(s)")
    
    async def send(self, alert: Alert) -> bool:
        """Envia alerta via Telegram.
        
        Envia para todos os chat_ids configurados com retry automático.
        
        Args:
            alert: Alerta a ser enviado
            
        Returns:
            True se enviou para pelo menos um chat, False caso contrário
        """
        message = self.format_message(alert)
        success_count = 0
        
        for chat_id in self._chat_ids:
            if await self._send_to_chat(chat_id, message):
                success_count += 1
        
        if success_count > 0:
            logger.info(
                f"Telegram alert sent successfully to {success_count}/{len(self._chat_ids)} chats"
            )
            return True
        else:
            logger.error("Failed to send Telegram alert to any chat")
            return False
    
    async def _send_to_chat(self, chat_id: str, message: str) -> bool:
        """Envia mensagem para um chat específico com retry.
        
        Args:
            chat_id: ID do chat
            message: Mensagem formatada
            
        Returns:
            True se enviou com sucesso, False caso contrário
        """
        url = f"{self._base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        for attempt in range(self._max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            logger.debug(f"Telegram message sent to chat {chat_id}")
                            return True
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"Telegram API error (attempt {attempt + 1}/{self._max_retries}): "
                                f"status={response.status}, error={error_text}"
                            )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Telegram request timeout (attempt {attempt + 1}/{self._max_retries})"
                )
            except Exception as e:
                logger.warning(
                    f"Telegram request failed (attempt {attempt + 1}/{self._max_retries}): {e}"
                )
            
            # Backoff exponencial: 1s, 2s, 4s
            if attempt < self._max_retries - 1:
                wait_time = 2 ** attempt
                logger.debug(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to send Telegram message to chat {chat_id} after {self._max_retries} attempts")
        return False
    
    def format_message(self, alert: Alert) -> str:
        """Formata mensagem do alerta em Markdown.
        
        Args:
            alert: Alerta a ser formatado
            
        Returns:
            Mensagem formatada em Markdown
        """
        # Emoji baseado no tipo de evento
        emoji_map = {
            "fall_suspected": "🚨",
            "presence_moving": "🚶",
            "presence_still": "👤",
            "no_presence": "✅",
            "prolonged_inactivity": "⏰",
            "anomaly_detected": "⚠️",
            "multiple_people": "👥"
        }
        
        emoji = emoji_map.get(alert.event_type, "📢")
        
        # Tradução de tipos de evento
        event_names = {
            "fall_suspected": "Queda Detectada",
            "presence_moving": "Movimento Detectado",
            "presence_still": "Presença Detectada",
            "no_presence": "Ambiente Vazio",
            "prolonged_inactivity": "Inatividade Prolongada",
            "anomaly_detected": "Comportamento Anormal",
            "multiple_people": "Múltiplas Pessoas"
        }
        
        event_name = event_names.get(alert.event_type, alert.event_type)
        
        # Formata mensagem
        lines = [
            f"{emoji} *ALERTA: {event_name}*",
            "",
            f"📊 Confiança: {alert.confidence:.0%}",
            f"🕐 Horário: {self._format_timestamp(alert.timestamp)}",
        ]
        
        # Adiciona detalhes específicos por tipo de evento
        if alert.event_type == "fall_suspected":
            lines.append("")
            lines.append("⚠️ *Ação recomendada:*")
            lines.append("Verifique imediatamente o local")
        elif alert.event_type == "presence_moving":
            lines.append("")
            lines.append("ℹ️ Atividade detectada no ambiente monitorado")
        elif alert.event_type == "presence_still":
            lines.append("")
            lines.append("ℹ️ Pessoa presente no ambiente")
        elif alert.event_type == "prolonged_inactivity":
            lines.append("")
            lines.append("⚠️ Sem movimento há mais de 30 segundos")
        
        # Adiciona detalhes técnicos se disponíveis (apenas para debug)
        if alert.details and len(alert.details) > 0:
            # Filtra detalhes relevantes
            relevant_details = {}
            if "rate_of_change" in alert.details:
                relevant_details["Taxa de mudança"] = f"{alert.details['rate_of_change']:.1f} dB/s"
            if "duration" in alert.details:
                duration_min = alert.details["duration"] / 60
                relevant_details["Duração"] = f"{duration_min:.1f} min"
            
            if relevant_details:
                lines.append("")
                lines.append("📋 *Detalhes:*")
                for key, value in relevant_details.items():
                    lines.append(f"  • {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Formata timestamp para exibição.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            String formatada (HH:MM:SS)
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")


class WhatsAppChannel(NotificationChannel):
    """Canal de notificação via WhatsApp (Twilio API).
    
    Envia mensagens via Twilio WhatsApp API para múltiplos destinatários.
    Implementa retry com backoff exponencial (3 tentativas).
    """
    
    def __init__(self, account_sid: str, auth_token: str, 
                 from_number: str, recipients: List[str]):
        """Inicializa canal WhatsApp.
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: Número WhatsApp do remetente (formato: +1234567890)
            recipients: Lista de números WhatsApp dos destinatários (formato: +1234567890)
        """
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from_number = from_number
        self._recipients = recipients
        self._max_retries = 3
        
        logger.info(f"WhatsAppChannel initialized with {len(recipients)} recipient(s)")
    
    async def send(self, alert: Alert) -> bool:
        """Envia alerta via WhatsApp.
        
        Envia para todos os destinatários configurados com retry automático.
        
        Args:
            alert: Alerta a ser enviado
            
        Returns:
            True se enviou para pelo menos um destinatário, False caso contrário
        """
        message = self.format_message(alert)
        success_count = 0
        
        for recipient in self._recipients:
            if await self._send_to_recipient(recipient, message):
                success_count += 1
        
        if success_count > 0:
            logger.info(
                f"WhatsApp alert sent successfully to {success_count}/{len(self._recipients)} recipient(s)"
            )
            return True
        else:
            logger.error("Failed to send WhatsApp alert to any recipient")
            return False
    
    async def _send_to_recipient(self, recipient: str, message: str) -> bool:
        """Envia mensagem para um destinatário específico com retry.
        
        Args:
            recipient: Número do destinatário (formato: +1234567890)
            message: Mensagem formatada
            
        Returns:
            True se enviou com sucesso, False caso contrário
        """
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}/Messages.json"
        
        for attempt in range(self._max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    auth = aiohttp.BasicAuth(self._account_sid, self._auth_token)
                    data = {
                        "From": f"whatsapp:{self._from_number}",
                        "To": f"whatsapp:{recipient}",
                        "Body": message
                    }
                    
                    async with session.post(
                        url, 
                        auth=auth, 
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 201:
                            logger.debug(f"WhatsApp message sent to {recipient}")
                            return True
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"Twilio API error (attempt {attempt + 1}/{self._max_retries}): "
                                f"status={response.status}, error={error_text}"
                            )
            except asyncio.TimeoutError:
                logger.warning(
                    f"WhatsApp request timeout (attempt {attempt + 1}/{self._max_retries})"
                )
            except Exception as e:
                logger.warning(
                    f"WhatsApp request failed (attempt {attempt + 1}/{self._max_retries}): {e}"
                )
            
            # Backoff exponencial: 1s, 2s, 4s
            if attempt < self._max_retries - 1:
                wait_time = 2 ** attempt
                logger.debug(f"Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to send WhatsApp message to {recipient} after {self._max_retries} attempts")
        return False
    
    def format_message(self, alert: Alert) -> str:
        """Formata mensagem do alerta para WhatsApp.
        
        Args:
            alert: Alerta a ser formatado
            
        Returns:
            Mensagem formatada como texto simples
        """
        # Emoji baseado no tipo de evento
        emoji_map = {
            "fall_suspected": "🚨",
            "presence_moving": "🚶",
            "presence_still": "🧍",
            "no_presence": "✅",
            "prolonged_inactivity": "⏰",
            "anomaly_detected": "⚠️",
            "multiple_people": "👥"
        }
        
        emoji = emoji_map.get(alert.event_type, "📢")
        
        # Tradução de tipos de evento
        event_names = {
            "fall_suspected": "Queda Suspeita",
            "presence_moving": "Movimento Detectado",
            "presence_still": "Presença Parada",
            "no_presence": "Sem Presença",
            "prolonged_inactivity": "Inatividade Prolongada",
            "anomaly_detected": "Anomalia Detectada",
            "multiple_people": "Múltiplas Pessoas"
        }
        
        event_name = event_names.get(alert.event_type, alert.event_type)
        
        # Formata mensagem (WhatsApp não suporta Markdown, usa texto simples)
        lines = [
            f"{emoji} WiFiSense Alert",
            "",
            f"Evento: {event_name}",
            f"Confiança: {alert.confidence:.0%}",
            f"Horário: {self._format_timestamp(alert.timestamp)}",
        ]
        
        if alert.message:
            lines.append("")
            lines.append(alert.message)
        
        # Adiciona detalhes se disponíveis
        if alert.details:
            lines.append("")
            lines.append("Detalhes:")
            for key, value in alert.details.items():
                lines.append(f"  • {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Formata timestamp para exibição.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            String formatada (HH:MM:SS)
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")



class WebhookChannel(NotificationChannel):
    """Canal de notificação via Webhook HTTP POST.
    
    Envia notificações via HTTP POST para múltiplas URLs configuradas.
    Suporta assinatura HMAC-SHA256 para validação de autenticidade.
    Implementa retry com backoff exponencial (5 tentativas).
    Mantém fila de webhooks pendentes em caso de falhas consecutivas.
    """
    
    def __init__(self, urls: List[str], secret: Optional[str] = None):
        """Inicializa canal Webhook.
        
        Args:
            urls: Lista de URLs para enviar webhooks
            secret: Chave secreta para assinatura HMAC (opcional)
        """
        self._urls = urls
        self._secret = secret
        self._retry_attempts = 5
        self._retry_delay = 30  # segundos
        self._pending_queue: List[dict] = []  # Fila de webhooks pendentes
        
        logger.info(f"WebhookChannel initialized with {len(urls)} URL(s)")
    
    async def send(self, alert: Alert) -> bool:
        """Envia alerta via webhook para todas as URLs.
        
        Envia para todas as URLs configuradas com retry automático.
        Webhooks que falharem após todas as tentativas são adicionados à fila pendente.
        
        Args:
            alert: Alerta a ser enviado
            
        Returns:
            True se enviou para pelo menos uma URL, False caso contrário
        """
        payload = {
            "event_type": alert.event_type,
            "confidence": alert.confidence,
            "timestamp": alert.timestamp,
            "message": alert.message,
            "details": alert.details
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Adiciona assinatura HMAC se secret configurado
        if self._secret:
            signature = self._generate_signature(payload)
            headers["X-Webhook-Signature"] = signature
        
        success_count = 0
        
        async with aiohttp.ClientSession() as session:
            for url in self._urls:
                if await self._send_with_retry(session, url, payload, headers):
                    success_count += 1
                else:
                    # Adiciona à fila de pendentes
                    self._pending_queue.append({
                        "url": url,
                        "payload": payload,
                        "headers": headers,
                        "timestamp": alert.timestamp
                    })
                    logger.error(f"Webhook failed for {url}, added to pending queue")
        
        if success_count > 0:
            logger.info(
                f"Webhook alert sent successfully to {success_count}/{len(self._urls)} URL(s)"
            )
            return True
        else:
            logger.error("Failed to send webhook alert to any URL")
            return False
    
    async def _send_with_retry(self, session: aiohttp.ClientSession, 
                               url: str, payload: dict, headers: dict) -> bool:
        """Envia webhook com retry exponencial.
        
        Tenta enviar o webhook até 5 vezes com backoff exponencial:
        - Tentativa 1: imediata
        - Tentativa 2: após 30s
        - Tentativa 3: após 60s
        - Tentativa 4: após 120s
        - Tentativa 5: após 240s
        
        Args:
            session: Sessão aiohttp
            url: URL de destino
            payload: Dados do webhook
            headers: Headers HTTP
            
        Returns:
            True se enviou com sucesso, False caso contrário
        """
        for attempt in range(self._retry_attempts):
            try:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in (200, 201, 204):
                        logger.debug(f"Webhook sent successfully to {url}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(
                            f"Webhook attempt {attempt + 1}/{self._retry_attempts} failed: "
                            f"status={response.status}, url={url}, error={error_text}"
                        )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Webhook timeout (attempt {attempt + 1}/{self._retry_attempts}): url={url}"
                )
            except Exception as e:
                logger.warning(
                    f"Webhook error (attempt {attempt + 1}/{self._retry_attempts}): "
                    f"url={url}, error={e}"
                )
            
            # Backoff exponencial: 30s, 60s, 120s, 240s
            if attempt < self._retry_attempts - 1:
                wait_time = self._retry_delay * (2 ** attempt)
                logger.debug(f"Retrying webhook in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        logger.error(
            f"Failed to send webhook to {url} after {self._retry_attempts} attempts"
        )
        return False
    
    def _generate_signature(self, payload: dict) -> str:
        """Gera assinatura HMAC-SHA256 do payload.
        
        A assinatura é calculada sobre o JSON serializado do payload
        com chaves ordenadas para garantir consistência.
        
        Args:
            payload: Dados do webhook
            
        Returns:
            Assinatura hexadecimal HMAC-SHA256
        """
        message = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            self._secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def format_message(self, alert: Alert) -> str:
        """Formata mensagem do alerta para webhook.
        
        Para webhooks, retorna o JSON do payload como string.
        
        Args:
            alert: Alerta a ser formatado
            
        Returns:
            JSON string do payload
        """
        payload = {
            "event_type": alert.event_type,
            "confidence": alert.confidence,
            "timestamp": alert.timestamp,
            "message": alert.message,
            "details": alert.details
        }
        return json.dumps(payload, indent=2)
    
    def get_pending_count(self) -> int:
        """Retorna número de webhooks pendentes na fila.
        
        Returns:
            Número de webhooks pendentes
        """
        return len(self._pending_queue)
    
    def clear_pending_queue(self) -> None:
        """Limpa a fila de webhooks pendentes."""
        self._pending_queue.clear()
        logger.info("Pending webhook queue cleared")
    
    async def retry_pending(self) -> int:
        """Tenta reenviar webhooks pendentes.
        
        Returns:
            Número de webhooks reenviados com sucesso
        """
        if not self._pending_queue:
            return 0
        
        success_count = 0
        failed_items = []
        
        async with aiohttp.ClientSession() as session:
            for item in self._pending_queue:
                if await self._send_with_retry(
                    session, 
                    item["url"], 
                    item["payload"], 
                    item["headers"]
                ):
                    success_count += 1
                else:
                    failed_items.append(item)
        
        # Atualiza fila com itens que ainda falharam
        self._pending_queue = failed_items
        
        logger.info(
            f"Retried {success_count} pending webhooks, "
            f"{len(failed_items)} still pending"
        )
        
        return success_count
