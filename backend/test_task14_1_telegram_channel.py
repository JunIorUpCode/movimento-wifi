"""
Testes para Task 14.1 - TelegramChannel

Testa:
- send() com Telegram Bot API
- _format_message() com formatação Markdown
- Retry com backoff exponencial (3 tentativas)
- Logging de sucesso/falha
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notification_channels import TelegramChannel
from app.services.notification_types import Alert


@pytest.fixture
def telegram_channel():
    """Canal Telegram para testes."""
    return TelegramChannel(
        bot_token="test_token_123",
        chat_ids=["123456", "789012"]
    )


@pytest.fixture
def alert_fall():
    """Alerta de queda para testes."""
    return Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=time.time(),
        message="Queda detectada com alta confiança",
        details={"rate_of_change": 15.2}
    )


@pytest.fixture
def alert_movement():
    """Alerta de movimento para testes."""
    return Alert(
        event_type="presence_moving",
        confidence=0.75,
        timestamp=time.time(),
        message="Movimento detectado"
    )


class TestTelegramChannelInit:
    """Testes para inicialização."""
    
    def test_init_basic(self):
        """Testa inicialização básica."""
        channel = TelegramChannel("token", ["123"])
        
        assert channel._bot_token == "token"
        assert channel._chat_ids == ["123"]
        assert channel._max_retries == 3
        assert "token" in channel._base_url
    
    def test_init_multiple_chats(self):
        """Testa inicialização com múltiplos chats."""
        channel = TelegramChannel("token", ["123", "456", "789"])
        
        assert len(channel._chat_ids) == 3
        assert channel._chat_ids == ["123", "456", "789"]


class TestFormatMessage:
    """Testes para formatação de mensagens."""
    
    def test_format_fall_alert(self, telegram_channel, alert_fall):
        """Testa formatação de alerta de queda."""
        message = telegram_channel.format_message(alert_fall)
        
        assert "🚨" in message  # Emoji de queda
        assert "Queda Suspeita" in message
        assert "85%" in message  # Confiança
        assert "Queda detectada" in message
        assert "rate_of_change" in message
        assert "15.2" in message
    
    def test_format_movement_alert(self, telegram_channel, alert_movement):
        """Testa formatação de alerta de movimento."""
        message = telegram_channel.format_message(alert_movement)
        
        assert "🚶" in message  # Emoji de movimento
        assert "Movimento Detectado" in message
        assert "75%" in message
        assert "Movimento detectado" in message
    
    def test_format_includes_timestamp(self, telegram_channel, alert_fall):
        """Testa que mensagem inclui timestamp formatado."""
        message = telegram_channel.format_message(alert_fall)
        
        assert "🕐" in message
        assert "Horário:" in message
        # Verifica formato HH:MM:SS
        import re
        assert re.search(r'\d{2}:\d{2}:\d{2}', message)
    
    def test_format_without_details(self, telegram_channel):
        """Testa formatação sem detalhes adicionais."""
        alert = Alert(
            event_type="no_presence",
            confidence=0.9,
            timestamp=time.time(),
            message="Ambiente vazio"
        )
        
        message = telegram_channel.format_message(alert)
        
        assert "✅" in message
        assert "Sem Presença" in message
        assert "90%" in message
        assert "Detalhes:" not in message
    
    def test_format_all_event_types(self, telegram_channel):
        """Testa formatação de todos os tipos de evento."""
        event_types = [
            "fall_suspected",
            "presence_moving",
            "presence_still",
            "no_presence",
            "prolonged_inactivity",
            "anomaly_detected",
            "multiple_people"
        ]
        
        for event_type in event_types:
            alert = Alert(
                event_type=event_type,
                confidence=0.8,
                timestamp=time.time(),
                message=f"Teste {event_type}"
            )
            
            message = telegram_channel.format_message(alert)
            
            # Verifica que mensagem foi formatada
            assert len(message) > 0
            assert "Confiança:" in message
            assert "80%" in message


class TestSendToChat:
    """Testes para envio a chat específico."""
    
    @pytest.mark.asyncio
    async def test_send_to_chat_success(self, telegram_channel):
        """Testa envio bem-sucedido."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Mock response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            # Mock session.post to return the response
            mock_post = MagicMock(return_value=mock_response)
            
            # Mock session
            mock_session = MagicMock()
            mock_session.post = mock_post
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            result = await telegram_channel._send_to_chat("123", "Test message")
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_to_chat_retry_on_error(self, telegram_channel):
        """Testa retry em caso de erro."""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock response com erro
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post = mock_post
            mock_session.return_value.__aexit__.return_value = None
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await telegram_channel._send_to_chat("123", "Test")
                
                assert result is False
                # Deve ter tentado 3 vezes
                assert mock_post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_send_to_chat_success_after_retry(self, telegram_channel):
        """Testa sucesso após retry."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Primeira tentativa falha, segunda sucede
            mock_response_fail = MagicMock()
            mock_response_fail.status = 500
            mock_response_fail.text = AsyncMock(return_value="Error")
            mock_response_fail.__aenter__ = AsyncMock(return_value=mock_response_fail)
            mock_response_fail.__aexit__ = AsyncMock(return_value=None)
            
            mock_response_success = MagicMock()
            mock_response_success.status = 200
            mock_response_success.__aenter__ = AsyncMock(return_value=mock_response_success)
            mock_response_success.__aexit__ = AsyncMock(return_value=None)
            
            mock_post = MagicMock(side_effect=[mock_response_fail, mock_response_success])
            
            mock_session = MagicMock()
            mock_session.post = mock_post
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await telegram_channel._send_to_chat("123", "Test")
                
                assert result is True
                assert mock_post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_to_chat_timeout(self, telegram_channel):
        """Testa timeout de requisição."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_post = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_session.return_value.__aenter__.return_value.post = mock_post
            mock_session.return_value.__aexit__.return_value = None
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await telegram_channel._send_to_chat("123", "Test")
                
                assert result is False
                assert mock_post.call_count == 3


class TestSend:
    """Testes para método send() principal."""
    
    @pytest.mark.asyncio
    async def test_send_success_all_chats(self, telegram_channel, alert_fall):
        """Testa envio bem-sucedido para todos os chats."""
        with patch.object(telegram_channel, '_send_to_chat', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            result = await telegram_channel.send(alert_fall)
            
            assert result is True
            assert mock_send.call_count == 2  # 2 chats
    
    @pytest.mark.asyncio
    async def test_send_partial_success(self, telegram_channel, alert_fall):
        """Testa envio com sucesso parcial."""
        with patch.object(telegram_channel, '_send_to_chat', new_callable=AsyncMock) as mock_send:
            # Primeiro chat sucede, segundo falha
            mock_send.side_effect = [True, False]
            
            result = await telegram_channel.send(alert_fall)
            
            assert result is True  # Pelo menos um sucedeu
            assert mock_send.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_all_fail(self, telegram_channel, alert_fall):
        """Testa envio com falha em todos os chats."""
        with patch.object(telegram_channel, '_send_to_chat', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False
            
            result = await telegram_channel.send(alert_fall)
            
            assert result is False
            assert mock_send.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_formats_message(self, telegram_channel, alert_fall):
        """Testa que send() formata mensagem corretamente."""
        with patch.object(telegram_channel, '_send_to_chat', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            await telegram_channel.send(alert_fall)
            
            # Verifica que mensagem foi formatada
            call_args = mock_send.call_args_list[0][0]
            message = call_args[1]
            
            assert "Queda Suspeita" in message
            assert "85%" in message


class TestBackoffExponential:
    """Testes para backoff exponencial."""
    
    @pytest.mark.asyncio
    async def test_backoff_timing(self, telegram_channel):
        """Testa que backoff segue progressão exponencial."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Error")
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = None
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post = mock_post
            mock_session.return_value.__aexit__.return_value = None
            
            sleep_times = []
            
            async def mock_sleep(duration):
                sleep_times.append(duration)
            
            with patch('asyncio.sleep', side_effect=mock_sleep):
                await telegram_channel._send_to_chat("123", "Test")
                
                # Deve ter dormido 2 vezes (entre 3 tentativas)
                assert len(sleep_times) == 2
                # Backoff exponencial: 1s, 2s
                assert sleep_times[0] == 1
                assert sleep_times[1] == 2


class TestIntegration:
    """Testes de integração."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Testa workflow completo de envio."""
        channel = TelegramChannel("test_token", ["123"])
        
        alert = Alert(
            event_type="fall_suspected",
            confidence=0.9,
            timestamp=time.time(),
            message="Queda crítica",
            details={"location": "sala"}
        )
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_post = MagicMock(return_value=mock_response)
            
            mock_session = MagicMock()
            mock_session.post = mock_post
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            result = await channel.send(alert)
            
            assert result is True
            
            # Verifica payload enviado
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs['json']
            
            assert payload['chat_id'] == "123"
            assert payload['parse_mode'] == "Markdown"
            assert "Queda" in payload['text']
            assert "90%" in payload['text']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
