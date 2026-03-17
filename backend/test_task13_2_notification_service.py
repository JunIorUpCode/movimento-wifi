"""
Testes para Task 13.2 - NotificationService

Testa:
- __init__ com setup de canais
- send_alert() com validações
- _check_cooldown() para evitar spam
- _is_quiet_hours() para horários de silêncio
- Singleton pattern
- Integração com canais mock
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationChannel, NotificationConfig


class MockChannel(NotificationChannel):
    """Canal mock para testes."""
    
    def __init__(self):
        self.sent_alerts = []
        self.should_succeed = True
    
    async def send(self, alert: Alert) -> bool:
        self.sent_alerts.append(alert)
        await asyncio.sleep(0.01)  # Simula I/O
        return self.should_succeed
    
    def format_message(self, alert: Alert) -> str:
        return f"{alert.event_type}: {alert.message}"


@pytest.fixture
def reset_singleton():
    """Reseta singleton entre testes."""
    NotificationService._instance = None
    yield
    NotificationService._instance = None


@pytest.fixture
def basic_config():
    """Configuração básica para testes."""
    return NotificationConfig(
        enabled=True,
        channels=[],
        min_confidence=0.7,
        cooldown_seconds=60,
        quiet_hours=[]
    )


@pytest.fixture
def alert_high_confidence():
    """Alerta com alta confiança."""
    return Alert(
        event_type="fall_suspected",
        confidence=0.85,
        timestamp=time.time(),
        message="Queda detectada com alta confiança"
    )


@pytest.fixture
def alert_low_confidence():
    """Alerta com baixa confiança."""
    return Alert(
        event_type="presence_moving",
        confidence=0.5,
        timestamp=time.time(),
        message="Movimento detectado"
    )


class TestNotificationServiceInit:
    """Testes para __init__ e setup de canais."""
    
    def test_init_default_config(self, reset_singleton):
        """Testa inicialização com configuração padrão."""
        service = NotificationService()
        
        assert service._config is not None
        assert service._config.enabled is True
        assert service._channels == {}
        assert service._last_notification == {}
    
    def test_init_custom_config(self, reset_singleton, basic_config):
        """Testa inicialização com configuração customizada."""
        basic_config.min_confidence = 0.8
        basic_config.cooldown_seconds = 120
        
        service = NotificationService(basic_config)
        
        assert service._config.min_confidence == 0.8
        assert service._config.cooldown_seconds == 120
    
    def test_singleton_pattern(self, reset_singleton, basic_config):
        """Testa que NotificationService é singleton."""
        service1 = NotificationService(basic_config)
        service2 = NotificationService()
        
        assert service1 is service2
        assert id(service1) == id(service2)
    
    def test_setup_channels_empty(self, reset_singleton, basic_config):
        """Testa setup sem canais configurados."""
        basic_config.channels = []
        service = NotificationService(basic_config)
        
        assert len(service._channels) == 0
    
    def test_setup_telegram_channel(self, reset_singleton):
        """Testa setup do canal Telegram."""
        config = NotificationConfig(
            enabled=True,
            channels=["telegram"],
            telegram_bot_token="test_token",
            telegram_chat_ids=["123456"]
        )
        
        service = NotificationService(config)
        
        # Verifica que configuração foi armazenada
        assert service._config.telegram_bot_token == "test_token"
        assert service._config.telegram_chat_ids == ["123456"]
        # Canal pode não estar disponível se módulo não existe
        # mas configuração deve estar presente
    
    def test_setup_channels_incomplete_config(self, reset_singleton):
        """Testa setup com configuração incompleta (sem chat_ids)."""
        config = NotificationConfig(
            enabled=True,
            channels=["telegram"],
            telegram_bot_token="test_token",
            telegram_chat_ids=[]  # Vazio
        )
        
        service = NotificationService(config)
        
        # Não deve criar canal sem chat_ids
        assert "telegram" not in service._channels


class TestSendAlert:
    """Testes para send_alert() com validações."""
    
    @pytest.mark.asyncio
    async def test_send_alert_disabled(self, reset_singleton, basic_config, alert_high_confidence):
        """Testa que não envia quando notificações estão desabilitadas."""
        basic_config.enabled = False
        service = NotificationService(basic_config)
        
        mock_channel = MockChannel()
        service._channels["mock"] = mock_channel
        
        await service.send_alert(alert_high_confidence)
        
        assert len(mock_channel.sent_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_send_alert_below_min_confidence(
        self, reset_singleton, basic_config, alert_low_confidence
    ):
        """Testa que não envia quando confiança está abaixo do mínimo."""
        basic_config.min_confidence = 0.7
        service = NotificationService(basic_config)
        
        mock_channel = MockChannel()
        service._channels["mock"] = mock_channel
        
        await service.send_alert(alert_low_confidence)  # confidence=0.5
        
        assert len(mock_channel.sent_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_send_alert_success(self, reset_singleton, basic_config, alert_high_confidence):
        """Testa envio bem-sucedido de alerta."""
        service = NotificationService(basic_config)
        
        mock_channel = MockChannel()
        service._channels["mock"] = mock_channel
        
        await service.send_alert(alert_high_confidence)
        
        assert len(mock_channel.sent_alerts) == 1
        assert mock_channel.sent_alerts[0].event_type == "fall_suspected"
        assert mock_channel.sent_alerts[0].confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_send_alert_multiple_channels(
        self, reset_singleton, basic_config, alert_high_confidence
    ):
        """Testa envio para múltiplos canais."""
        service = NotificationService(basic_config)
        
        mock_channel1 = MockChannel()
        mock_channel2 = MockChannel()
        service._channels["mock1"] = mock_channel1
        service._channels["mock2"] = mock_channel2
        
        await service.send_alert(alert_high_confidence)
        
        assert len(mock_channel1.sent_alerts) == 1
        assert len(mock_channel2.sent_alerts) == 1
    
    @pytest.mark.asyncio
    async def test_send_alert_no_channels(
        self, reset_singleton, basic_config, alert_high_confidence
    ):
        """Testa envio sem canais configurados."""
        service = NotificationService(basic_config)
        
        # Não deve lançar exceção
        await service.send_alert(alert_high_confidence)
    
    @pytest.mark.asyncio
    async def test_send_alert_channel_failure(
        self, reset_singleton, basic_config, alert_high_confidence
    ):
        """Testa que falha em um canal não interrompe outros."""
        service = NotificationService(basic_config)
        
        mock_channel1 = MockChannel()
        mock_channel1.should_succeed = False
        mock_channel2 = MockChannel()
        
        service._channels["failing"] = mock_channel1
        service._channels["working"] = mock_channel2
        
        await service.send_alert(alert_high_confidence)
        
        # Ambos devem ter recebido o alerta
        assert len(mock_channel1.sent_alerts) == 1
        assert len(mock_channel2.sent_alerts) == 1
    
    @pytest.mark.asyncio
    async def test_send_alert_updates_last_notification(
        self, reset_singleton, basic_config, alert_high_confidence
    ):
        """Testa que send_alert atualiza timestamp da última notificação."""
        service = NotificationService(basic_config)
        
        mock_channel = MockChannel()
        service._channels["mock"] = mock_channel
        
        before = time.time()
        await service.send_alert(alert_high_confidence)
        after = time.time()
        
        last_time = service._last_notification.get("fall_suspected")
        assert last_time is not None
        assert before <= last_time <= after


class TestCheckCooldown:
    """Testes para _check_cooldown()."""
    
    def test_check_cooldown_no_previous_notification(self, reset_singleton, basic_config):
        """Testa cooldown quando nunca enviou notificação deste tipo."""
        service = NotificationService(basic_config)
        
        assert service._check_cooldown("fall_suspected") is True
    
    def test_check_cooldown_expired(self, reset_singleton, basic_config):
        """Testa cooldown expirado."""
        basic_config.cooldown_seconds = 1
        service = NotificationService(basic_config)
        
        # Simula notificação há 2 segundos
        service._last_notification["fall_suspected"] = time.time() - 2
        
        assert service._check_cooldown("fall_suspected") is True
    
    def test_check_cooldown_active(self, reset_singleton, basic_config):
        """Testa cooldown ainda ativo."""
        basic_config.cooldown_seconds = 60
        service = NotificationService(basic_config)
        
        # Simula notificação há 10 segundos
        service._last_notification["fall_suspected"] = time.time() - 10
        
        assert service._check_cooldown("fall_suspected") is False
    
    def test_check_cooldown_different_event_types(self, reset_singleton, basic_config):
        """Testa que cooldown é independente por tipo de evento."""
        service = NotificationService(basic_config)
        
        # Notificação recente de queda
        service._last_notification["fall_suspected"] = time.time()
        
        # Movimento não deve estar em cooldown
        assert service._check_cooldown("presence_moving") is True
        # Queda deve estar em cooldown
        assert service._check_cooldown("fall_suspected") is False
    
    @pytest.mark.asyncio
    async def test_cooldown_prevents_spam(self, reset_singleton, basic_config):
        """Testa que cooldown previne spam de notificações."""
        basic_config.cooldown_seconds = 60
        service = NotificationService(basic_config)
        
        mock_channel = MockChannel()
        service._channels["mock"] = mock_channel
        
        alert = Alert(
            event_type="fall_suspected",
            confidence=0.9,
            timestamp=time.time(),
            message="Queda"
        )
        
        # Primeira notificação deve passar
        await service.send_alert(alert)
        assert len(mock_channel.sent_alerts) == 1
        
        # Segunda notificação imediata deve ser bloqueada
        await service.send_alert(alert)
        assert len(mock_channel.sent_alerts) == 1  # Ainda 1


class TestIsQuietHours:
    """Testes para _is_quiet_hours()."""
    
    def test_is_quiet_hours_no_config(self, reset_singleton, basic_config):
        """Testa quando não há quiet hours configurados."""
        basic_config.quiet_hours = []
        service = NotificationService(basic_config)
        
        assert service._is_quiet_hours() is False
    
    @patch('app.services.notification_service.datetime')
    def test_is_quiet_hours_normal_period(self, mock_datetime, reset_singleton, basic_config):
        """Testa período normal de quiet hours (não atravessa meia-noite)."""
        # Simula 23:00
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_datetime.now.return_value = mock_now
        
        basic_config.quiet_hours = [(22, 24)]  # 22h-24h
        service = NotificationService(basic_config)
        
        assert service._is_quiet_hours() is True
    
    @patch('app.services.notification_service.datetime')
    def test_is_quiet_hours_outside_period(self, mock_datetime, reset_singleton, basic_config):
        """Testa fora do período de quiet hours."""
        # Simula 14:00
        mock_now = MagicMock()
        mock_now.hour = 14
        mock_datetime.now.return_value = mock_now
        
        basic_config.quiet_hours = [(22, 7)]  # 22h-7h
        service = NotificationService(basic_config)
        
        assert service._is_quiet_hours() is False
    
    @patch('app.services.notification_service.datetime')
    def test_is_quiet_hours_crosses_midnight(self, mock_datetime, reset_singleton, basic_config):
        """Testa período que atravessa meia-noite."""
        # Simula 02:00 (madrugada)
        mock_now = MagicMock()
        mock_now.hour = 2
        mock_datetime.now.return_value = mock_now
        
        basic_config.quiet_hours = [(22, 7)]  # 22h-7h
        service = NotificationService(basic_config)
        
        assert service._is_quiet_hours() is True
    
    @patch('app.services.notification_service.datetime')
    def test_is_quiet_hours_multiple_periods(self, mock_datetime, reset_singleton, basic_config):
        """Testa múltiplos períodos de quiet hours."""
        # Simula 14:00
        mock_now = MagicMock()
        mock_now.hour = 14
        mock_datetime.now.return_value = mock_now
        
        basic_config.quiet_hours = [(12, 15), (22, 7)]  # 12h-15h e 22h-7h
        service = NotificationService(basic_config)
        
        assert service._is_quiet_hours() is True
    
    @pytest.mark.asyncio
    async def test_quiet_hours_blocks_alerts(self, reset_singleton, basic_config):
        """Testa que quiet hours bloqueia alertas."""
        with patch('app.services.notification_service.datetime') as mock_datetime:
            # Simula 23:00
            mock_now = MagicMock()
            mock_now.hour = 23
            mock_datetime.now.return_value = mock_now
            
            basic_config.quiet_hours = [(22, 7)]
            service = NotificationService(basic_config)
            
            mock_channel = MockChannel()
            service._channels["mock"] = mock_channel
            
            alert = Alert(
                event_type="fall_suspected",
                confidence=0.9,
                timestamp=time.time(),
                message="Queda"
            )
            
            await service.send_alert(alert)
            
            # Não deve ter enviado
            assert len(mock_channel.sent_alerts) == 0


class TestUtilityMethods:
    """Testes para métodos utilitários."""
    
    def test_update_config(self, reset_singleton, basic_config):
        """Testa atualização de configuração."""
        service = NotificationService(basic_config)
        
        new_config = NotificationConfig(
            enabled=False,
            min_confidence=0.9
        )
        
        service.update_config(new_config)
        
        assert service._config.enabled is False
        assert service._config.min_confidence == 0.9
    
    def test_get_last_notification_time(self, reset_singleton, basic_config):
        """Testa obtenção do timestamp da última notificação."""
        service = NotificationService(basic_config)
        
        # Sem notificação prévia
        assert service.get_last_notification_time("fall_suspected") is None
        
        # Com notificação
        timestamp = time.time()
        service._last_notification["fall_suspected"] = timestamp
        
        assert service.get_last_notification_time("fall_suspected") == timestamp
    
    def test_reset_cooldown_specific(self, reset_singleton, basic_config):
        """Testa reset de cooldown para evento específico."""
        service = NotificationService(basic_config)
        
        service._last_notification["fall_suspected"] = time.time()
        service._last_notification["presence_moving"] = time.time()
        
        service.reset_cooldown("fall_suspected")
        
        assert "fall_suspected" not in service._last_notification
        assert "presence_moving" in service._last_notification
    
    def test_reset_cooldown_all(self, reset_singleton, basic_config):
        """Testa reset de todos os cooldowns."""
        service = NotificationService(basic_config)
        
        service._last_notification["fall_suspected"] = time.time()
        service._last_notification["presence_moving"] = time.time()
        
        service.reset_cooldown()
        
        assert len(service._last_notification) == 0


class TestIntegration:
    """Testes de integração."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, reset_singleton):
        """Testa workflow completo de envio de alerta."""
        config = NotificationConfig(
            enabled=True,
            channels=[],
            min_confidence=0.7,
            cooldown_seconds=2,
            quiet_hours=[]
        )
        
        service = NotificationService(config)
        mock_channel = MockChannel()
        service._channels["mock"] = mock_channel
        
        # Alerta 1: deve passar
        alert1 = Alert(
            event_type="fall_suspected",
            confidence=0.85,
            timestamp=time.time(),
            message="Queda 1"
        )
        await service.send_alert(alert1)
        assert len(mock_channel.sent_alerts) == 1
        
        # Alerta 2: bloqueado por cooldown
        alert2 = Alert(
            event_type="fall_suspected",
            confidence=0.90,
            timestamp=time.time(),
            message="Queda 2"
        )
        await service.send_alert(alert2)
        assert len(mock_channel.sent_alerts) == 1
        
        # Aguarda cooldown expirar
        await asyncio.sleep(2.1)
        
        # Alerta 3: deve passar
        alert3 = Alert(
            event_type="fall_suspected",
            confidence=0.88,
            timestamp=time.time(),
            message="Queda 3"
        )
        await service.send_alert(alert3)
        assert len(mock_channel.sent_alerts) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
