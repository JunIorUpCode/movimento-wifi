# -*- coding: utf-8 -*-
"""
Webhook Channel - Canal de Notificação via Webhook
Implementa envio de notificações via HTTP POST para URLs configuradas
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List

from shared.logging import get_logger

logger = get_logger(__name__)


class WebhookChannel:
    """
    Canal de notificação via Webhook.
    
    **Formato**: JSON com event_type, confidence, timestamp, device_id, metadata
    
    **Timeout**: 10 segundos por requisição
    
    **Retry**: Até 3 tentativas com exponential backoff
    """
    
    def __init__(self, webhook_urls: List[str], webhook_secret: str = None):
        """
        Inicializa canal de webhook.
        
        Args:
            webhook_urls: Lista de URLs de webhook
            webhook_secret: Secret para assinatura HMAC (opcional)
        """
        self.webhook_urls = webhook_urls
        self.webhook_secret = webhook_secret
        
        logger.info(
            "WebhookChannel inicializado",
            urls_count=len(webhook_urls)
        )
    
    async def send_notification(
        self,
        event_data: Dict[str, Any],
        max_retries: int = 3,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Envia notificação via webhook para todas as URLs configuradas.
        
        **Formato JSON**:
        ```json
        {
            "event_type": "fall_suspected",
            "confidence": 0.95,
            "timestamp": "2024-01-01T12:00:00",
            "device_id": "uuid",
            "device_name": "Sala de Estar",
            "metadata": {}
        }
        ```
        
        **Retry**: Tenta até max_retries vezes com exponential backoff
        
        **Timeout**: 10 segundos por requisição
        
        Args:
            event_data: Dados do evento
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos
        
        Returns:
            Dict com resultado do envio:
            {
                "success": bool,
                "sent_to": List[str],
                "failed": List[str],
                "error": str (opcional)
            }
        """
        # Prepara payload JSON
        payload = {
            "event_type": event_data.get("event_type"),
            "confidence": event_data.get("confidence"),
            "timestamp": event_data.get("timestamp"),
            "device_id": event_data.get("device_id"),
            "device_name": event_data.get("device_name"),
            "metadata": event_data.get("metadata", {})
        }
        
        sent_to = []
        failed = []
        
        # Envia para cada URL
        async with aiohttp.ClientSession() as session:
            for url in self.webhook_urls:
                success = await self._send_to_url(
                    session=session,
                    url=url,
                    payload=payload,
                    max_retries=max_retries,
                    timeout=timeout
                )
                
                if success:
                    sent_to.append(url)
                else:
                    failed.append(url)
        
        # Resultado
        result = {
            "success": len(sent_to) > 0,
            "sent_to": sent_to,
            "failed": failed
        }
        
        if failed:
            result["error"] = f"Falha ao enviar para {len(failed)} webhook(s)"
        
        logger.info(
            "Notificação Webhook enviada",
            sent_to_count=len(sent_to),
            failed_count=len(failed)
        )
        
        return result
    
    async def _send_to_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: Dict[str, Any],
        max_retries: int,
        timeout: int
    ) -> bool:
        """
        Envia POST para uma URL específica com retry.
        
        Args:
            session: Sessão aiohttp
            url: URL do webhook
            payload: Payload JSON
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "WiFiSense-Notification-Service/1.0"
        }
        
        # Adiciona assinatura HMAC se secret configurado
        if self.webhook_secret:
            import hmac
            import hashlib
            
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                self.webhook_secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers["X-Webhook-Signature"] = signature
        
        for attempt in range(max_retries):
            try:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    # Considera sucesso se status 2xx
                    if 200 <= response.status < 300:
                        logger.debug(
                            "Webhook enviado",
                            url=url,
                            attempt=attempt + 1,
                            status=response.status
                        )
                        return True
                    else:
                        logger.warning(
                            f"Webhook retornou status {response.status}",
                            url=url,
                            attempt=attempt + 1
                        )
            
            except asyncio.TimeoutError:
                logger.warning(
                    f"Webhook timeout (tentativa {attempt + 1}/{max_retries})",
                    url=url,
                    timeout=timeout
                )
            
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Erro ao enviar webhook (tentativa {attempt + 1}/{max_retries})",
                    url=url,
                    error=str(e)
                )
            
            except Exception as e:
                logger.error(
                    "Erro inesperado ao enviar webhook",
                    url=url,
                    error=str(e),
                    exc_info=True
                )
                break
            
            # Exponential backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com webhooks enviando payload de teste.
        
        Returns:
            Dict com resultado do teste
        """
        test_payload = {
            "event_type": "test",
            "confidence": 1.0,
            "timestamp": "2024-01-01T12:00:00",
            "device_id": "test-device",
            "device_name": "Teste",
            "metadata": {
                "test": True,
                "message": "Este é um teste de notificação WiFiSense"
            }
        }
        
        sent_count = 0
        
        async with aiohttp.ClientSession() as session:
            for url in self.webhook_urls:
                success = await self._send_to_url(
                    session=session,
                    url=url,
                    payload=test_payload,
                    max_retries=1,
                    timeout=10
                )
                
                if success:
                    sent_count += 1
        
        success = sent_count > 0
        
        return {
            "success": success,
            "message": f"Teste enviado para {sent_count}/{len(self.webhook_urls)} webhook(s)",
            "urls_tested": sent_count
        }
