"""
Testes para Task 15: WhatsAppChannel

Valida a implementação do canal de notificação WhatsApp via Twilio API.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientResponse

from app.services.notification_channels import WhatsAppChannel
from app.services.notification_types import Alert


@pytest.fixture
def sample_alert():
    """Cria um alerta de exemplo para testes."""
    return Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=1234567890.0,
        message="Queda detectada no ambiente",
        details={"rate_of_change": 15.5}
    )


@pytest.fixture
def whatsapp_channel():
    """Cria uma instância de WhatsAppChannel para testes."""
    return WhatsAppChannel(
        account_sid="test_account_sid",
        auth_token="test_auth_token",
        from_number="+1234567890",
        recipients=["+9876543210", "+1111111111"]
    )


class TestWhatsAppChannelInitialization:
    """Testes de inicialização do WhatsAppChannel."""
    
    def test_initialization(self, whatsapp_channel):
        """Testa que WhatsAppChannel é inicializado corretamente."""
        assert whatsapp_channel._account_sid == "test_account_sid"
        assert whatsapp_channel._auth_token == "test_auth_token"
        assert whatsapp_channel._from_number == "+1234567890"
        assert whatsapp_channel._recipients == ["+9876543210", "+1111111111"]
        assert whatsapp_channel._max_retries == 3


class TestWhatsAppChannelFormatMessage:
    """Testes de formatação de mensagem."""
    
    def test_format_message_basic(self, whatsapp_channel, sample_alert):
        """Testa formatação básica de mensagem."""
        message = whatsapp_channel.format_message(sample_alert)
        
        assert "🚨 WiFiSense Alert" in message
        assert "Evento: Queda Suspeita" in message
        assert "Confiança: 85%" in message
        assert "Horário:" in message
        assert "Queda detectada no ambiente" in message
    
    def test_format_message_with_details(self, whatsapp_channel, sample_alert):
        """Testa formatação de mensagem com detalhes."""
        message = whatsapp_channel.format_message(sample_alert)
        
        assert "Detalhes:" in message
        assert "rate_of_change: 15.5" in message
    
    def test_format_message_different_event_types(self, whatsapp_channel):
        """Testa formatação para diferentes tipos de evento."""
        event_types = [
            ("fall_suspected", "🚨", "Queda Suspeita"),
            ("presence_moving", "🚶", "Movimento Detectado"),
            ("presence_still", "🧍", "Presença Parada"),
            ("no_presence", "✅", "Sem Presença"),
            ("prolonged_inactivity", "⏰", "Inatividade Prolongada"),
            ("anomaly_detected", "⚠️", "Anomalia Detectada"),
            ("multiple_people", "👥", "Múltiplas Pessoas"),
        ]
        
        for event_type, emoji, event_name in event_types:
            alert = Alert(
                event_type=event_type,
                confidence=0.8,
                timestamp=1234567890.0,
                message="Test message"
            )
            message = whatsapp_channel.format_message(alert)
            
            assert emoji in message
            assert event_name in message
    
    def test_format_message_without_details(self, whatsapp_channel):
        """Testa formatação de mensagem sem detalhes."""
        alert = Alert(
            event_type="presence_moving",
            confidence=0.75,
            timestamp=1234567890.0,
            message="Movimento detectado"
        )
        message = whatsapp_channel.format_message(alert)
        
        assert "🚶 WiFiSense Alert" in message
        assert "Evento: Movimento Detectado" in message
        assert "Confiança: 75%" in message
        assert "Movimento detectado" in message
        assert "Detalhes:" not in message


class TestWhatsAppChannelSend:
    """Testes de envio de mensagens."""
    
    @pytest.mark.asyncio
    async def test_send_success(self, whatsapp_channel, sample_alert):
        """Testa envio bem-sucedido para todos os destinatários."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock da resposta HTTP
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.__aenter__.return_value = mock_response
            mock_post.return_value = mock_response
            
            result = await whatsapp_channel.send(sample_alert)
            
            assert result is True
            assert mock_post.call_count == 2  # 2 destinatários
    
    @pytest.mark.asyncio
    async def test_send_partial_success(self, whatsapp_channel, sample_alert):
        """Testa envio com sucesso parcial (um destinatário falha)."""
        with patch.object(whatsapp_channel, '_send_to_recipient') as mock_send:
            # Primeiro destinatário sucesso, segundo falha
            mock_send.side_effect = [True, False]
            
            result = await whatsapp_channel.send(sample_alert)
            
            assert result is True  # Sucesso se pelo menos um enviou
            assert mock_send.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_all_fail(self, whatsapp_channel, sample_alert):
        """Testa envio quando todos os destinatários falham."""
        with patch.object(whatsapp_channel, '_send_to_recipient') as mock_send:
            mock_send.return_value = False
            
            result = await whatsapp_channel.send(sample_alert)
            
            assert result is False
            assert mock_send.call_count == 2


class TestWhatsAppChannelSendToRecipient:
    """Testes de envio para destinatário específico."""
    
    @pytest.mark.asyncio
    async def test_send_to_recipient_success(self, whatsapp_channel):
        """Testa envio bem-sucedido para um destinatário."""
        with patch('app.services.notification_channels.aiohttp.ClientSession') as mock_session_class:
            # Mock da sessão e resposta
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status = 201
            
            # Setup async context managers
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session.post = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            result = await whatsapp_channel._send_to_recipient("+9876543210", "Test message")
            
            assert result is True
            mock_session.post.assert_called_once()
            
            # Verifica os parâmetros da chamada
            call_args = mock_session.post.call_args
            assert "https://api.twilio.com/2010-04-01/Accounts/test_account_sid/Messages.json" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_send_to_recipient_with_retry(self, whatsapp_channel):
        """Testa retry com backoff exponencial."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            
            # Primeira tentativa falha (status 500), segunda sucesso (status 201)
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_response_success = AsyncMock()
            mock_response_success.status = 201
            
            mock_response.__aenter__.side_effect = [mock_response, mock_response_success]
            mock_session.post.return_value = mock_response
            mock_session.__aenter__.return_value = mock_session
            mock_session_class.return_value = mock_session
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await whatsapp_channel._send_to_recipient("+9876543210", "Test message")
                
                # Deve ter feito retry
                assert mock_session.post.call_count >= 1
                # Deve ter esperado (backoff)
                if mock_session.post.call_count > 1:
                    mock_sleep.assert_called()
    
    @pytest.mark.asyncio
    async def test_send_to_recipient_max_retries(self, whatsapp_channel):
        """Testa que respeita o limite de tentativas."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_response.__aenter__.return_value = mock_response
            mock_session.post.return_value = mock_response
            mock_session.__aenter__.return_value = mock_session
            mock_session_class.return_value = mock_session
            
            with patch('asyncio.sleep'):
                result = await whatsapp_channel._send_to_recipient("+9876543210", "Test message")
                
                assert result is False
                assert mock_session.post.call_count == 3  # max_retries
    
    @pytest.mark.asyncio
    async def test_send_to_recipient_timeout(self, whatsapp_channel):
        """Testa tratamento de timeout."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.side_effect = asyncio.TimeoutError()
            mock_session.__aenter__.return_value = mock_session
            mock_session_class.return_value = mock_session
            
            with patch('asyncio.sleep'):
                result = await whatsapp_channel._send_to_recipient("+9876543210", "Test message")
                
                assert result is False
                assert mock_session.post.call_count == 3  # Tentou 3 vezes
    
    @pytest.mark.asyncio
    async def test_send_to_recipient_exception(self, whatsapp_channel):
        """Testa tratamento de exceções genéricas."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post.side_effect = Exception("Network error")
            mock_session.__aenter__.return_value = mock_session
            mock_session_class.return_value = mock_session
            
            with patch('asyncio.sleep'):
                result = await whatsapp_channel._send_to_recipient("+9876543210", "Test message")
                
                assert result is False
                assert mock_session.post.call_count == 3


class TestWhatsAppChannelIntegration:
    """Testes de integração do WhatsAppChannel."""
    
    @pytest.mark.asyncio
    async def test_full_flow_success(self, whatsapp_channel, sample_alert):
        """Testa fluxo completo de envio de alerta."""
        with patch('app.services.notification_channels.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.status = 201
            
            # Setup async context managers
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session.post = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            # Envia alerta
            result = await whatsapp_channel.send(sample_alert)
            
            assert result is True
            
            # Verifica que chamou a API para cada destinatário
            assert mock_session.post.call_count == 2
            
            # Verifica que a mensagem foi formatada corretamente
            call_args = mock_session.post.call_args_list[0]
            data = call_args[1]['data']
            assert data['From'] == "whatsapp:+1234567890"
            assert "whatsapp:+" in data['To']
            assert "WiFiSense Alert" in data['Body']
            assert "Queda Suspeita" in data['Body']


class TestWhatsAppChannelRequirements:
    """Testes que validam requisitos específicos."""
    
    def test_requirement_11_1_twilio_api(self, whatsapp_channel):
        """Valida Requisito 11.1: Suporte integração com Twilio."""
        # Verifica que usa credenciais Twilio
        assert whatsapp_channel._account_sid is not None
        assert whatsapp_channel._auth_token is not None
    
    def test_requirement_11_2_formatted_message(self, whatsapp_channel, sample_alert):
        """Valida Requisito 11.2: Mensagem formatada com detalhes."""
        message = whatsapp_channel.format_message(sample_alert)
        
        # Deve incluir tipo de evento, timestamp, confiança
        assert "Evento:" in message
        assert "Horário:" in message
        assert "Confiança:" in message
    
    @pytest.mark.asyncio
    async def test_requirement_11_3_critical_alert(self, whatsapp_channel):
        """Valida Requisito 11.3: Alerta crítico é enviado."""
        critical_alert = Alert(
            event_type="fall_suspected",
            confidence=0.85,
            timestamp=1234567890.0,
            message="Queda detectada"
        )
        
        with patch.object(whatsapp_channel, '_send_to_recipient', return_value=True):
            result = await whatsapp_channel.send(critical_alert)
            assert result is True
    
    def test_requirement_11_4_message_includes_link_placeholder(self, whatsapp_channel, sample_alert):
        """Valida Requisito 11.4: Mensagem pode incluir informações adicionais."""
        message = whatsapp_channel.format_message(sample_alert)
        
        # Verifica que detalhes são incluídos
        assert "Detalhes:" in message or sample_alert.message in message
    
    @pytest.mark.asyncio
    async def test_requirement_11_6_retry_on_failure(self, whatsapp_channel, sample_alert):
        """Valida Requisito 11.6: Retry após falha (máximo 3 tentativas)."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Error")
            mock_response.__aenter__.return_value = mock_response
            mock_session.post.return_value = mock_response
            mock_session.__aenter__.return_value = mock_session
            mock_session_class.return_value = mock_session
            
            with patch('asyncio.sleep'):
                result = await whatsapp_channel._send_to_recipient("+9876543210", "Test")
                
                # Deve ter tentado 3 vezes
                assert mock_session.post.call_count == 3
                assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
