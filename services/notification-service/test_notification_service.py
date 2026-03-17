# -*- coding: utf-8 -*-
"""
Testes Unitários - Notification Service
Testa funcionalidades básicas do serviço de notificações
"""

import pytest
import sys
import os
from uuid import uuid4
from datetime import datetime

# Adiciona o diretório raiz ao path para importar shared
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Testes básicos de importação
def test_imports():
    """Testa se todos os módulos podem ser importados"""
    from models.notification_config import NotificationConfig
    from models.notification_log import NotificationLog
    from schemas.notification_config import NotificationConfigUpdate, QuietHours
    from schemas.notification_log import NotificationLogResponse
    from utils.encryption import encrypt_token, decrypt_token
    from channels.telegram_channel import TelegramChannel
    from channels.email_channel import EmailChannel
    from channels.webhook_channel import WebhookChannel
    from services.notification_service import NotificationService
    from services.notification_worker import NotificationWorker
    
    assert NotificationConfig is not None
    assert NotificationLog is not None
    assert NotificationConfigUpdate is not None
    assert QuietHours is not None
    assert NotificationLogResponse is not None
    assert encrypt_token is not None
    assert decrypt_token is not None
    assert TelegramChannel is not None
    assert EmailChannel is not None
    assert WebhookChannel is not None
    assert NotificationService is not None
    assert NotificationWorker is not None


def test_encryption_roundtrip():
    """Testa criptografia e descriptografia de tokens"""
    from utils.encryption import encrypt_token, decrypt_token
    
    # Token original
    original_token = "123456:ABC-DEF-GHI-JKL"
    
    # Criptografa
    encrypted = encrypt_token(original_token)
    
    # Verifica que foi criptografado (diferente do original)
    assert encrypted != original_token
    assert len(encrypted) > 0
    
    # Descriptografa
    decrypted = decrypt_token(encrypted)
    
    # Verifica que voltou ao original
    assert decrypted == original_token


def test_quiet_hours_validation():
    """Testa validação de quiet hours"""
    from schemas.notification_config import QuietHours
    from pydantic import ValidationError
    
    # Válido
    quiet_hours = QuietHours(start="22:00", end="07:00")
    assert quiet_hours.start == "22:00"
    assert quiet_hours.end == "07:00"
    
    # Inválido - formato errado
    with pytest.raises(ValidationError):
        QuietHours(start="25:00", end="07:00")
    
    with pytest.raises(ValidationError):
        QuietHours(start="22:00", end="99:99")


def test_notification_config_update_validation():
    """Testa validação de atualização de configuração"""
    from schemas.notification_config import NotificationConfigUpdate
    from pydantic import ValidationError
    
    # Válido
    update = NotificationConfigUpdate(
        enabled=True,
        channels=["telegram", "email"],
        min_confidence=0.8,
        cooldown_seconds=300
    )
    assert update.enabled is True
    assert "telegram" in update.channels
    assert update.min_confidence == 0.8
    
    # Inválido - canal não permitido
    with pytest.raises(ValidationError):
        NotificationConfigUpdate(channels=["invalid_channel"])
    
    # Inválido - min_confidence fora do range
    with pytest.raises(ValidationError):
        NotificationConfigUpdate(min_confidence=1.5)
    
    # Inválido - webhook URL sem HTTPS
    with pytest.raises(ValidationError):
        NotificationConfigUpdate(webhook_urls=["http://example.com"])


def test_telegram_channel_message_formatting():
    """Testa formatação de mensagens do Telegram"""
    from channels.telegram_channel import TelegramChannel
    
    # Cria canal (sem bot_token real)
    channel = TelegramChannel("fake_token", ["123456789"])
    
    # Dados do evento
    event_data = {
        "event_type": "fall_suspected",
        "confidence": 0.95,
        "device_name": "Sala de Estar",
        "timestamp": "2024-01-01T12:00:00",
        "metadata": {"details": "Movimento brusco detectado"}
    }
    
    # Formata mensagem
    message = channel._format_message(event_data)
    
    # Verifica conteúdo
    assert "Queda Detectada" in message
    assert "95%" in message
    assert "Sala de Estar" in message
    assert "2024-01-01T12:00:00" in message
    assert "🚨" in message  # Emoji de alerta


def test_email_channel_subject_generation():
    """Testa geração de assunto de email"""
    from channels.email_channel import EmailChannel
    
    # Cria canal (sem API key real)
    channel = EmailChannel("fake_api_key", ["user@example.com"])
    
    # Dados do evento
    event_data = {
        "event_type": "fall_suspected",
        "device_name": "Sala de Estar"
    }
    
    # Gera assunto
    subject = channel._generate_subject(event_data)
    
    # Verifica conteúdo
    assert "WiFiSense" in subject
    assert "Queda Detectada" in subject
    assert "Sala de Estar" in subject


def test_webhook_channel_payload_format():
    """Testa formato de payload do webhook"""
    from channels.webhook_channel import WebhookChannel
    
    # Cria canal
    channel = WebhookChannel(["https://example.com/webhook"])
    
    # Dados do evento
    event_data = {
        "event_type": "fall_suspected",
        "confidence": 0.95,
        "timestamp": "2024-01-01T12:00:00",
        "device_id": str(uuid4()),
        "device_name": "Sala de Estar",
        "metadata": {"details": "Teste"}
    }
    
    # Verifica que o canal foi criado
    assert len(channel.webhook_urls) == 1
    assert channel.webhook_urls[0] == "https://example.com/webhook"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
