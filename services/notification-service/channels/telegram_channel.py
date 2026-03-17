# -*- coding: utf-8 -*-
"""
Telegram Channel - Canal de Notificação via Telegram
Implementa envio de notificações via Telegram Bot API (multi-tenant)
"""

import asyncio
from typing import Dict, Any, List
from telegram import Bot
from telegram.error import TelegramError

from shared.logging import get_logger

logger = get_logger(__name__)


class TelegramChannel:
    """
    Canal de notificação via Telegram.
    
    **Multi-Tenant**: Usa bot_token específico do tenant
    
    **Retry**: Implementa retry com exponential backoff
    
    **Formato**: Mensagens formatadas em português com detalhes do evento
    """
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        """
        Inicializa canal Telegram.
        
        Args:
            bot_token: Token do bot Telegram (específico do tenant)
            chat_ids: Lista de chat IDs para enviar mensagens
        """
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.bot = Bot(token=bot_token)
        
        logger.info(
            "TelegramChannel inicializado",
            chat_ids_count=len(chat_ids)
        )
    
    async def send_notification(
        self,
        event_data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Envia notificação via Telegram para todos os chat IDs configurados.
        
        **Retry**: Tenta até max_retries vezes com exponential backoff
        
        **Formato da Mensagem**:
        ```
        🚨 Alerta WiFiSense
        
        Tipo: Queda Detectada
        Confiança: 95%
        Dispositivo: Sala de Estar
        Horário: 15:30:45
        
        Detalhes: Movimento brusco detectado
        ```
        
        Args:
            event_data: Dados do evento
            max_retries: Número máximo de tentativas
        
        Returns:
            Dict com resultado do envio:
            {
                "success": bool,
                "sent_to": List[str],  # Chat IDs que receberam
                "failed": List[str],   # Chat IDs que falharam
                "error": str (opcional)
            }
        """
        # Formata mensagem em português
        message = self._format_message(event_data)
        
        sent_to = []
        failed = []
        
        # Envia para cada chat ID
        for chat_id in self.chat_ids:
            success = await self._send_to_chat(
                chat_id=chat_id,
                message=message,
                max_retries=max_retries
            )
            
            if success:
                sent_to.append(chat_id)
            else:
                failed.append(chat_id)
        
        # Resultado
        result = {
            "success": len(sent_to) > 0,
            "sent_to": sent_to,
            "failed": failed
        }
        
        if failed:
            result["error"] = f"Falha ao enviar para {len(failed)} chat(s)"
        
        logger.info(
            "Notificação Telegram enviada",
            sent_to_count=len(sent_to),
            failed_count=len(failed)
        )
        
        return result
    
    async def _send_to_chat(
        self,
        chat_id: str,
        message: str,
        max_retries: int
    ) -> bool:
        """
        Envia mensagem para um chat ID específico com retry.
        
        Args:
            chat_id: ID do chat
            message: Mensagem formatada
            max_retries: Número máximo de tentativas
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        for attempt in range(max_retries):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML"
                )
                
                logger.debug(
                    "Mensagem Telegram enviada",
                    chat_id=chat_id,
                    attempt=attempt + 1
                )
                
                return True
            
            except TelegramError as e:
                logger.warning(
                    f"Erro ao enviar Telegram (tentativa {attempt + 1}/{max_retries})",
                    chat_id=chat_id,
                    error=str(e)
                )
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                logger.error(
                    "Erro inesperado ao enviar Telegram",
                    chat_id=chat_id,
                    error=str(e),
                    exc_info=True
                )
                break
        
        return False
    
    def _format_message(self, event_data: Dict[str, Any]) -> str:
        """
        Formata mensagem em português com detalhes do evento.
        
        Args:
            event_data: Dados do evento
        
        Returns:
            str: Mensagem formatada em HTML
        """
        # Mapeia tipos de evento para português
        event_type_map = {
            "presence": "Presença Detectada",
            "movement": "Movimento Detectado",
            "fall_suspected": "Queda Detectada",
            "prolonged_inactivity": "Inatividade Prolongada"
        }
        
        event_type = event_data.get("event_type", "unknown")
        event_type_pt = event_type_map.get(event_type, event_type)
        
        confidence = event_data.get("confidence", 0.0)
        confidence_pct = int(confidence * 100)
        
        device_name = event_data.get("device_name", "Desconhecido")
        timestamp = event_data.get("timestamp", "")
        
        # Emoji baseado no tipo
        emoji_map = {
            "presence": "👤",
            "movement": "🚶",
            "fall_suspected": "🚨",
            "prolonged_inactivity": "⏰"
        }
        emoji = emoji_map.get(event_type, "📡")
        
        # Monta mensagem
        message = f"""
{emoji} <b>Alerta WiFiSense</b>

<b>Tipo:</b> {event_type_pt}
<b>Confiança:</b> {confidence_pct}%
<b>Dispositivo:</b> {device_name}
<b>Horário:</b> {timestamp}
"""
        
        # Adiciona detalhes se disponíveis
        metadata = event_data.get("metadata", {})
        if metadata:
            details = metadata.get("details", "")
            if details:
                message += f"\n<b>Detalhes:</b> {details}"
        
        return message.strip()
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com Telegram enviando mensagem de teste.
        
        Returns:
            Dict com resultado do teste:
            {
                "success": bool,
                "message": str,
                "chat_ids_tested": int
            }
        """
        test_message = "🧪 <b>Teste de Notificação WiFiSense</b>\n\nSe você recebeu esta mensagem, as notificações estão funcionando corretamente!"
        
        sent_count = 0
        
        for chat_id in self.chat_ids:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=test_message,
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                logger.error(
                    "Erro ao testar Telegram",
                    chat_id=chat_id,
                    error=str(e)
                )
        
        success = sent_count > 0
        
        return {
            "success": success,
            "message": f"Teste enviado para {sent_count}/{len(self.chat_ids)} chat(s)",
            "chat_ids_tested": sent_count
        }
