"""
Testes para Task 13.1 - Dataclasses e interfaces de notificações.

Valida:
- NotificationConfig dataclass
- NotificationChannel interface abstrata
- Alert dataclass
"""

import pytest
import time
from app.services.notification_types import (
    NotificationConfig,
    NotificationChannel,
    Alert
)


class TestNotificationConfig:
    """Testes para NotificationConfig dataclass."""
    
    def test_default_values(self):
        """Testa valores padrão da configuração."""
        config = NotificationConfig()
        
        assert config.enabled is True
        assert config.channels == []
        assert config.min_confidence == 0.7
        assert config.cooldown_seconds == 300
        assert config.quiet_hours == []
        assert config.telegram_bot_token is None
        assert config.telegram_chat_ids == []
        assert config.twilio_account_sid is None
        assert config.webhook_urls == []
    
    def test_custom_values(self):
        """Testa criação com valores customizados."""
        config = NotificationConfig(
            enabled=False,
            channels=["telegram", "webhook"],
            min_confidence=0.8,
            cooldown_seconds=600,
            quiet_hours=[(22, 7), (13, 14)],
            telegram_bot_token="test_token",
            telegram_chat_ids=["123", "456"],
            webhook_urls=["https://example.com/webhook"]
        )
        
        assert config.enabled is False
        assert config.channels == ["telegram", "webhook"]
        assert config.min_confidence == 0.8
        assert config.cooldown_seconds == 600
        assert config.quiet_hours == [(22, 7), (13, 14)]
        assert config.telegram_bot_token == "test_token"
        assert config.telegram_chat_ids == ["123", "456"]
        assert config.webhook_urls == ["https://example.com/webhook"]
    
    def test_min_confidence_validation(self):
        """Testa validação de min_confidence."""
        # Valores válidos
        NotificationConfig(min_confidence=0.0)
        NotificationConfig(min_confidence=0.5)
        NotificationConfig(min_confidence=1.0)
        
        # Valores inválidos
        with pytest.raises(ValueError, match="min_confidence deve estar entre 0.0 e 1.0"):
            NotificationConfig(min_confidence=-0.1)
        
        with pytest.raises(ValueError, match="min_confidence deve estar entre 0.0 e 1.0"):
            NotificationConfig(min_confidence=1.1)
    
    def test_cooldown_validation(self):
        """Testa validação de cooldown_seconds."""
        # Valores válidos
        NotificationConfig(cooldown_seconds=0)
        NotificationConfig(cooldown_seconds=300)
        
        # Valores inválidos
        with pytest.raises(ValueError, match="cooldown_seconds deve ser não-negativo"):
            NotificationConfig(cooldown_seconds=-1)
    
    def test_quiet_hours_validation(self):
        """Testa validação de quiet_hours."""
        # Valores válidos
        NotificationConfig(quiet_hours=[(0, 6), (22, 23)])
        NotificationConfig(quiet_hours=[(22, 7)])  # Atravessa meia-noite
        
        # Valores inválidos
        with pytest.raises(ValueError, match="Horários inválidos em quiet_hours"):
            NotificationConfig(quiet_hours=[(-1, 6)])
        
        with pytest.raises(ValueError, match="Horários inválidos em quiet_hours"):
            NotificationConfig(quiet_hours=[(22, 24)])
        
        with pytest.raises(ValueError, match="Horários inválidos em quiet_hours"):
            NotificationConfig(quiet_hours=[(25, 6)])


class TestAlert:
    """Testes para Alert dataclass."""
    
    def test_basic_alert(self):
        """Testa criação de alerta básico."""
        timestamp = time.time()
        alert = Alert(
            event_type="fall_suspected",
            confidence=0.85,
            timestamp=timestamp,
            message="Queda detectada"
        )
        
        assert alert.event_type == "fall_suspected"
        assert alert.confidence == 0.85
        assert alert.timestamp == timestamp
        assert alert.message == "Queda detectada"
        assert alert.details == {}
    
    def test_alert_with_details(self):
        """Testa alerta com detalhes adicionais."""
        alert = Alert(
            event_type="presence_moving",
            confidence=0.75,
            timestamp=1234567890.0,
            message="Movimento detectado",
            details={
                "variance": 3.5,
                "location": "sala",
                "duration": 10.5
            }
        )
        
        assert alert.details["variance"] == 3.5
        assert alert.details["location"] == "sala"
        assert alert.details["duration"] == 10.5
    
    def test_confidence_validation(self):
        """Testa validação de confidence."""
        # Valores válidos
        Alert(event_type="test", confidence=0.0, timestamp=1.0, message="test")
        Alert(event_type="test", confidence=0.5, timestamp=1.0, message="test")
        Alert(event_type="test", confidence=1.0, timestamp=1.0, message="test")
        
        # Valores inválidos
        with pytest.raises(ValueError, match="confidence deve estar entre 0.0 e 1.0"):
            Alert(event_type="test", confidence=-0.1, timestamp=1.0, message="test")
        
        with pytest.raises(ValueError, match="confidence deve estar entre 0.0 e 1.0"):
            Alert(event_type="test", confidence=1.1, timestamp=1.0, message="test")
    
    def test_timestamp_validation(self):
        """Testa validação de timestamp."""
        # Valores válidos
        Alert(event_type="test", confidence=0.5, timestamp=0.0, message="test")
        Alert(event_type="test", confidence=0.5, timestamp=1234567890.0, message="test")
        
        # Valores inválidos
        with pytest.raises(ValueError, match="timestamp deve ser não-negativo"):
            Alert(event_type="test", confidence=0.5, timestamp=-1.0, message="test")
    
    def test_event_type_validation(self):
        """Testa validação de event_type."""
        # Valor válido
        Alert(event_type="test", confidence=0.5, timestamp=1.0, message="test")
        
        # Valor inválido
        with pytest.raises(ValueError, match="event_type não pode ser vazio"):
            Alert(event_type="", confidence=0.5, timestamp=1.0, message="test")


class TestNotificationChannel:
    """Testes para NotificationChannel interface."""
    
    def test_is_abstract(self):
        """Testa que NotificationChannel é abstrata."""
        with pytest.raises(TypeError):
            NotificationChannel()
    
    def test_concrete_implementation(self):
        """Testa implementação concreta da interface."""
        
        class TestChannel(NotificationChannel):
            async def send(self, alert: Alert) -> bool:
                return True
            
            def format_message(self, alert: Alert) -> str:
                return f"{alert.event_type}: {alert.message}"
        
        # Deve ser possível instanciar
        channel = TestChannel()
        assert channel is not None
    
    def test_missing_send_method(self):
        """Testa que send() é obrigatório."""
        
        class IncompleteChannel(NotificationChannel):
            def format_message(self, alert: Alert) -> str:
                return "test"
        
        with pytest.raises(TypeError):
            IncompleteChannel()
    
    def test_missing_format_message_method(self):
        """Testa que format_message() é obrigatório."""
        
        class IncompleteChannel(NotificationChannel):
            async def send(self, alert: Alert) -> bool:
                return True
        
        with pytest.raises(TypeError):
            IncompleteChannel()
    
    @pytest.mark.asyncio
    async def test_send_method_signature(self):
        """Testa assinatura do método send()."""
        
        class TestChannel(NotificationChannel):
            async def send(self, alert: Alert) -> bool:
                return alert.confidence > 0.5
            
            def format_message(self, alert: Alert) -> str:
                return "test"
        
        channel = TestChannel()
        alert = Alert(
            event_type="test",
            confidence=0.8,
            timestamp=1.0,
            message="test"
        )
        
        result = await channel.send(alert)
        assert result is True
    
    def test_format_message_signature(self):
        """Testa assinatura do método format_message()."""
        
        class TestChannel(NotificationChannel):
            async def send(self, alert: Alert) -> bool:
                return True
            
            def format_message(self, alert: Alert) -> str:
                return f"[{alert.event_type}] {alert.message} ({alert.confidence:.0%})"
        
        channel = TestChannel()
        alert = Alert(
            event_type="fall_suspected",
            confidence=0.85,
            timestamp=1.0,
            message="Queda detectada"
        )
        
        message = channel.format_message(alert)
        assert message == "[fall_suspected] Queda detectada (85%)"


class TestIntegration:
    """Testes de integração entre componentes."""
    
    @pytest.mark.asyncio
    async def test_complete_notification_flow(self):
        """Testa fluxo completo de notificação."""
        
        # Cria configuração
        config = NotificationConfig(
            enabled=True,
            channels=["test"],
            min_confidence=0.7,
            cooldown_seconds=60
        )
        
        # Cria canal de teste
        class TestChannel(NotificationChannel):
            def __init__(self):
                self.sent_alerts = []
            
            async def send(self, alert: Alert) -> bool:
                self.sent_alerts.append(alert)
                return True
            
            def format_message(self, alert: Alert) -> str:
                return f"{alert.event_type}: {alert.message}"
        
        channel = TestChannel()
        
        # Cria alerta
        alert = Alert(
            event_type="fall_suspected",
            confidence=0.85,
            timestamp=time.time(),
            message="Queda detectada com alta confiança",
            details={"rate_of_change": 15.2}
        )
        
        # Envia alerta
        result = await channel.send(alert)
        
        assert result is True
        assert len(channel.sent_alerts) == 1
        assert channel.sent_alerts[0].event_type == "fall_suspected"
        assert channel.sent_alerts[0].confidence == 0.85
        
        # Formata mensagem
        message = channel.format_message(alert)
        assert "fall_suspected" in message
        assert "Queda detectada" in message
