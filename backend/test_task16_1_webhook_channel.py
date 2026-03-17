"""
Testes para WebhookChannel (Tarefa 16.1).

Valida:
- Requisito 12.1: Configurar múltiplas URLs de webhook
- Requisito 12.2: Enviar requisição HTTP POST com payload JSON
- Requisito 12.3: Incluir assinatura HMAC no header
- Requisito 12.4: Payload JSON com event_type, timestamp, confidence, details, metadata
- Requisito 12.5: Retry com backoff exponencial (5 tentativas)
- Requisito 12.6: Manter fila de webhooks pendentes
"""

import asyncio
import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notification_channels import WebhookChannel
from app.services.notification_types import Alert


@pytest.fixture
def sample_alert():
    """Cria um alerta de exemplo para testes."""
    return Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=time.time(),
        message="Queda detectada no ambiente",
        details={"rate_of_change": 15.2, "location": "sala"}
    )


@pytest.fixture
def webhook_urls():
    """URLs de webhook para testes."""
    return [
        "https://example.com/webhook1",
        "https://example.com/webhook2"
    ]


@pytest.fixture
def webhook_secret():
    """Secret para assinatura HMAC."""
    return "my_secret_key_123"


class TestWebhookChannelInitialization:
    """Testes de inicialização do WebhookChannel."""
    
    def test_init_without_secret(self, webhook_urls):
        """Testa inicialização sem secret."""
        channel = WebhookChannel(urls=webhook_urls)
        
        assert channel._urls == webhook_urls
        assert channel._secret is None
        assert channel._retry_attempts == 5
        assert channel._retry_delay == 30
        assert channel._pending_queue == []
    
    def test_init_with_secret(self, webhook_urls, webhook_secret):
        """Testa inicialização com secret."""
        channel = WebhookChannel(urls=webhook_urls, secret=webhook_secret)
        
        assert channel._urls == webhook_urls
        assert channel._secret == webhook_secret
        assert channel._retry_attempts == 5
        assert channel._retry_delay == 30
        assert channel._pending_queue == []
    
    def test_init_single_url(self, webhook_secret):
        """Testa inicialização com uma única URL."""
        channel = WebhookChannel(urls=["https://example.com/webhook"], secret=webhook_secret)
        
        assert len(channel._urls) == 1
        assert channel._urls[0] == "https://example.com/webhook"


class TestWebhookSignature:
    """Testes de geração de assinatura HMAC."""
    
    def test_generate_signature(self, webhook_urls, webhook_secret):
        """Testa geração de assinatura HMAC-SHA256."""
        channel = WebhookChannel(urls=webhook_urls, secret=webhook_secret)
        
        payload = {
            "event_type": "fall_suspected",
            "confidence": 0.85,
            "timestamp": 1234567890.0,
            "message": "Test",
            "details": {}
        }
        
        signature = channel._generate_signature(payload)
        
        # Verifica que é uma string hexadecimal de 64 caracteres (SHA256)
        assert isinstance(signature, str)
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)
    
    def test_signature_consistency(self, webhook_urls, webhook_secret):
        """Testa que a mesma payload gera a mesma assinatura."""
        channel = WebhookChannel(urls=webhook_urls, secret=webhook_secret)
        
        payload = {
            "event_type": "presence_moving",
            "confidence": 0.75,
            "timestamp": 1234567890.0,
            "message": "Movement detected",
            "details": {"variance": 3.5}
        }
        
        sig1 = channel._generate_signature(payload)
        sig2 = channel._generate_signature(payload)
        
        assert sig1 == sig2
    
    def test_signature_changes_with_payload(self, webhook_urls, webhook_secret):
        """Testa que payloads diferentes geram assinaturas diferentes."""
        channel = WebhookChannel(urls=webhook_urls, secret=webhook_secret)
        
        payload1 = {
            "event_type": "fall_suspected",
            "confidence": 0.85,
            "timestamp": 1234567890.0,
            "message": "Test 1",
            "details": {}
        }
        
        payload2 = {
            "event_type": "fall_suspected",
            "confidence": 0.85,
            "timestamp": 1234567890.0,
            "message": "Test 2",  # Diferente
            "details": {}
        }
        
        sig1 = channel._generate_signature(payload1)
        sig2 = channel._generate_signature(payload2)
        
        assert sig1 != sig2
    
    def test_signature_manual_verification(self, webhook_urls, webhook_secret):
        """Testa assinatura com verificação manual."""
        channel = WebhookChannel(urls=webhook_urls, secret=webhook_secret)
        
        payload = {
            "event_type": "test",
            "confidence": 0.5,
            "timestamp": 1000.0,
            "message": "msg",
            "details": {}
        }
        
        signature = channel._generate_signature(payload)
        
        # Verifica manualmente
        message = json.dumps(payload, sort_keys=True).encode()
        expected_signature = hmac.new(
            webhook_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        assert signature == expected_signature


class TestWebhookSendSuccess:
    """Testes de envio bem-sucedido de webhooks."""
    
    @pytest.mark.asyncio
    async def test_send_single_url_success(self, sample_alert, webhook_urls):
        """Testa envio bem-sucedido para uma URL."""
        channel = WebhookChannel(urls=[webhook_urls[0]])
        
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await channel.send(sample_alert)
        
        assert result is True
        assert mock_session.post.called
        assert channel.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_send_multiple_urls_success(self, sample_alert, webhook_urls):
        """Testa envio bem-sucedido para múltiplas URLs."""
        channel = WebhookChannel(urls=webhook_urls)
        
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await channel.send(sample_alert)
        
        assert result is True
        assert mock_session.post.call_count == len(webhook_urls)
        assert channel.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_send_with_signature(self, sample_alert, webhook_urls, webhook_secret):
        """Testa envio com assinatura HMAC."""
        channel = WebhookChannel(urls=[webhook_urls[0]], secret=webhook_secret)
        
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await channel.send(sample_alert)
        
        assert result is True
        
        # Verifica que a assinatura foi incluída nos headers
        call_args = mock_session.post.call_args
        headers = call_args[1]['headers']
        assert 'X-Webhook-Signature' in headers
        assert len(headers['X-Webhook-Signature']) == 64  # SHA256 hex
    
    @pytest.mark.asyncio
    async def test_send_payload_structure(self, sample_alert, webhook_urls):
        """Testa estrutura do payload enviado."""
        channel = WebhookChannel(urls=[webhook_urls[0]])
        
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            await channel.send(sample_alert)
        
        # Verifica payload
        call_args = mock_session.post.call_args
        payload = call_args[1]['json']
        
        assert payload['event_type'] == sample_alert.event_type
        assert payload['confidence'] == sample_alert.confidence
        assert payload['timestamp'] == sample_alert.timestamp
        assert payload['message'] == sample_alert.message
        assert payload['details'] == sample_alert.details


class TestWebhookRetry:
    """Testes de retry com backoff exponencial."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, sample_alert, webhook_urls):
        """Testa retry após falha."""
        channel = WebhookChannel(urls=[webhook_urls[0]])
        
        # Mock: primeira tentativa falha, segunda sucede
        mock_response_fail = MagicMock()
        mock_response_fail.status = 500
        mock_response_fail.text = AsyncMock(return_value="Internal Server Error")
        mock_response_fail.__aenter__ = AsyncMock(return_value=mock_response_fail)
        mock_response_fail.__aexit__ = AsyncMock(return_value=None)
        
        mock_response_success = MagicMock()
        mock_response_success.status = 200
        mock_response_success.__aenter__ = AsyncMock(return_value=mock_response_success)
        mock_response_success.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=[mock_response_fail, mock_response_success])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):  # Mock sleep para acelerar teste
                result = await channel.send(sample_alert)
        
        assert result is True
        assert mock_session.post.call_count == 2  # 1 falha + 1 sucesso
    
    @pytest.mark.asyncio
    async def test_max_retries_reached(self, sample_alert, webhook_urls):
        """Testa que após 5 tentativas falhas, desiste."""
        channel = WebhookChannel(urls=[webhook_urls[0]])
        
        # Mock: todas as tentativas falham
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await channel.send(sample_alert)
        
        assert result is False
        assert mock_session.post.call_count == 5  # 5 tentativas
        assert channel.get_pending_count() == 1  # Adicionado à fila pendente
    
    @pytest.mark.asyncio
    async def test_retry_timeout(self, sample_alert, webhook_urls):
        """Testa retry após timeout."""
        channel = WebhookChannel(urls=[webhook_urls[0]])
        
        # Mock: timeout na primeira tentativa, sucesso na segunda
        mock_response_success = MagicMock()
        mock_response_success.status = 200
        mock_response_success.__aenter__ = AsyncMock(return_value=mock_response_success)
        mock_response_success.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=[
            asyncio.TimeoutError(),
            mock_response_success
        ])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await channel.send(sample_alert)
        
        assert result is True
        assert mock_session.post.call_count == 2


class TestWebhookPendingQueue:
    """Testes da fila de webhooks pendentes."""
    
    @pytest.mark.asyncio
    async def test_pending_queue_on_failure(self, sample_alert, webhook_urls):
        """Testa que webhooks falhados são adicionados à fila."""
        channel = WebhookChannel(urls=webhook_urls)
        
        # Mock: todas as tentativas falham
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await channel.send(sample_alert)
        
        # Ambas as URLs devem estar na fila pendente
        assert channel.get_pending_count() == len(webhook_urls)
    
    def test_clear_pending_queue(self, webhook_urls):
        """Testa limpeza da fila pendente."""
        channel = WebhookChannel(urls=webhook_urls)
        
        # Adiciona itens manualmente
        channel._pending_queue.append({"url": "test1", "payload": {}})
        channel._pending_queue.append({"url": "test2", "payload": {}})
        
        assert channel.get_pending_count() == 2
        
        channel.clear_pending_queue()
        
        assert channel.get_pending_count() == 0
    
    @pytest.mark.asyncio
    async def test_retry_pending_success(self, webhook_urls):
        """Testa reenvio bem-sucedido de webhooks pendentes."""
        channel = WebhookChannel(urls=webhook_urls)
        
        # Adiciona itens à fila pendente
        channel._pending_queue.append({
            "url": webhook_urls[0],
            "payload": {"test": "data"},
            "headers": {"Content-Type": "application/json"},
            "timestamp": time.time()
        })
        
        # Mock: sucesso no reenvio
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                success_count = await channel.retry_pending()
        
        assert success_count == 1
        assert channel.get_pending_count() == 0  # Fila limpa após sucesso
    
    @pytest.mark.asyncio
    async def test_retry_pending_partial_success(self, webhook_urls):
        """Testa reenvio com sucesso parcial."""
        channel = WebhookChannel(urls=webhook_urls)
        
        # Adiciona 2 itens à fila pendente
        for url in webhook_urls:
            channel._pending_queue.append({
                "url": url,
                "payload": {"test": "data"},
                "headers": {"Content-Type": "application/json"},
                "timestamp": time.time()
            })
        
        # Mock: primeiro sucede, segundo falha
        mock_response_success = MagicMock()
        mock_response_success.status = 200
        mock_response_success.__aenter__ = AsyncMock(return_value=mock_response_success)
        mock_response_success.__aexit__ = AsyncMock(return_value=None)
        
        mock_response_fail = MagicMock()
        mock_response_fail.status = 500
        mock_response_fail.text = AsyncMock(return_value="Error")
        mock_response_fail.__aenter__ = AsyncMock(return_value=mock_response_fail)
        mock_response_fail.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=[
            mock_response_success,
            mock_response_fail, mock_response_fail, mock_response_fail, mock_response_fail, mock_response_fail
        ])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                success_count = await channel.retry_pending()
        
        assert success_count == 1
        assert channel.get_pending_count() == 1  # Um ainda pendente


class TestWebhookFormatMessage:
    """Testes de formatação de mensagem."""
    
    def test_format_message(self, sample_alert, webhook_urls):
        """Testa formatação de mensagem para webhook."""
        channel = WebhookChannel(urls=webhook_urls)
        
        message = channel.format_message(sample_alert)
        
        # Verifica que é JSON válido
        parsed = json.loads(message)
        
        assert parsed['event_type'] == sample_alert.event_type
        assert parsed['confidence'] == sample_alert.confidence
        assert parsed['timestamp'] == sample_alert.timestamp
        assert parsed['message'] == sample_alert.message
        assert parsed['details'] == sample_alert.details


class TestWebhookEdgeCases:
    """Testes de casos extremos."""
    
    @pytest.mark.asyncio
    async def test_empty_urls_list(self, sample_alert):
        """Testa comportamento com lista vazia de URLs."""
        channel = WebhookChannel(urls=[])
        
        result = await channel.send(sample_alert)
        
        # Sem URLs, retorna False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_partial_success_multiple_urls(self, sample_alert, webhook_urls):
        """Testa sucesso parcial com múltiplas URLs."""
        channel = WebhookChannel(urls=webhook_urls)
        
        # Mock: primeira URL sucede, segunda falha
        mock_response_success = MagicMock()
        mock_response_success.status = 200
        mock_response_success.__aenter__ = AsyncMock(return_value=mock_response_success)
        mock_response_success.__aexit__ = AsyncMock(return_value=None)
        
        mock_response_fail = MagicMock()
        mock_response_fail.status = 500
        mock_response_fail.text = AsyncMock(return_value="Error")
        mock_response_fail.__aenter__ = AsyncMock(return_value=mock_response_fail)
        mock_response_fail.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        # Primeira URL: sucesso imediato
        # Segunda URL: 5 falhas
        mock_session.post = MagicMock(side_effect=[
            mock_response_success,
            mock_response_fail, mock_response_fail, mock_response_fail, 
            mock_response_fail, mock_response_fail
        ])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await channel.send(sample_alert)
        
        # Retorna True porque pelo menos uma URL teve sucesso
        assert result is True
        assert channel.get_pending_count() == 1  # Segunda URL na fila pendente
    
    @pytest.mark.asyncio
    async def test_different_success_status_codes(self, sample_alert, webhook_urls):
        """Testa que 200, 201 e 204 são considerados sucesso."""
        for status_code in [200, 201, 204]:
            channel = WebhookChannel(urls=[webhook_urls[0]])
            
            mock_response = MagicMock()
            mock_response.status = status_code
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = MagicMock()
            mock_session.post = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await channel.send(sample_alert)
            
            assert result is True, f"Status {status_code} should be success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
