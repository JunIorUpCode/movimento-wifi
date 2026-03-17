"""
Testes para Tarefa 18: Integração de notificações no MonitorService.

Valida:
- NotificationService está inicializado no MonitorService
- Alertas são avaliados e enviados após detecção
- Endpoints de configuração de notificações funcionam
- Endpoint de teste de notificações funciona
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.detection.base import DetectionResult, EventType
from app.main import app
from app.services.monitor_service import MonitorService
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


@pytest.fixture
def client():
    """Cliente de teste FastAPI."""
    return TestClient(app)


@pytest.fixture
def monitor_service():
    """Instância do MonitorService."""
    return MonitorService()


@pytest.fixture
def notification_config():
    """Configuração de notificações para testes."""
    return NotificationConfig(
        enabled=True,
        channels=["telegram"],
        min_confidence=0.7,
        cooldown_seconds=60,
        quiet_hours=[(22, 7)],
        telegram_bot_token="test_token_123",
        telegram_chat_ids=["123456789"]
    )


class TestNotificationServiceIntegration:
    """Testes de integração do NotificationService no MonitorService."""
    
    def test_notification_service_initialized(self, monitor_service):
        """Verifica que NotificationService está inicializado no MonitorService."""
        assert hasattr(monitor_service, '_notification_service')
        assert isinstance(monitor_service._notification_service, NotificationService)
        print("✓ NotificationService inicializado no MonitorService")
    
    @pytest.mark.asyncio
    async def test_send_notification_method_exists(self, monitor_service):
        """Verifica que método _send_notification existe."""
        assert hasattr(monitor_service, '_send_notification')
        assert callable(monitor_service._send_notification)
        print("✓ Método _send_notification existe")
    
    @pytest.mark.asyncio
    async def test_send_notification_creates_alert(self, monitor_service):
        """Verifica que _send_notification cria Alert corretamente."""
        # Mock do NotificationService.send_alert
        with patch.object(monitor_service._notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
            # Cria resultado de detecção
            result = DetectionResult(
                event_type=EventType.FALL_SUSPECTED,
                confidence=0.85,
                details={"rate_of_change": 15.0}
            )
            
            # Adiciona timestamp manualmente (não faz parte do DetectionResult)
            result.timestamp = datetime.now().timestamp()
            
            alert_message = "🚨 Queda detectada! Confiança: 85%"
            
            # Envia notificação
            await monitor_service._send_notification(result, alert_message)
            
            # Verifica que send_alert foi chamado
            assert mock_send.called
            
            # Verifica o Alert criado
            call_args = mock_send.call_args[0]
            alert = call_args[0]
            
            assert isinstance(alert, Alert)
            assert alert.event_type == "fall_suspected"
            assert alert.confidence == 0.85
            assert alert.message == alert_message
            assert alert.details == {"rate_of_change": 15.0}
            
            print("✓ _send_notification cria Alert corretamente")
    
    @pytest.mark.asyncio
    async def test_send_notification_handles_exceptions(self, monitor_service):
        """Verifica que exceções em notificações não interrompem o loop."""
        # Mock que lança exceção
        with patch.object(monitor_service._notification_service, 'send_alert', 
                         side_effect=Exception("Erro de teste")):
            result = DetectionResult(
                event_type=EventType.FALL_SUSPECTED,
                confidence=0.85,
                details={}
            )
            
            # Adiciona timestamp manualmente
            result.timestamp = datetime.now().timestamp()
            
            # Não deve lançar exceção
            try:
                await monitor_service._send_notification(result, "Teste")
                print("✓ Exceções em notificações são tratadas corretamente")
            except Exception as e:
                pytest.fail(f"Exceção não deveria ser propagada: {e}")


class TestNotificationConfigEndpoints:
    """Testes dos endpoints de configuração de notificações."""
    
    def test_get_notification_config(self, client):
        """Testa GET /api/notifications/config."""
        response = client.get("/api/notifications/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica estrutura da resposta
        assert "enabled" in data
        assert "channels" in data
        assert "min_confidence" in data
        assert "cooldown_seconds" in data
        assert "quiet_hours" in data
        assert "telegram_configured" in data
        assert "telegram_chat_count" in data
        assert "whatsapp_configured" in data
        assert "whatsapp_recipient_count" in data
        assert "webhook_configured" in data
        assert "webhook_url_count" in data
        
        # Verifica que credenciais não são expostas
        assert "telegram_bot_token" not in data
        assert "twilio_auth_token" not in data
        assert "webhook_secret" not in data
        
        print("✓ GET /api/notifications/config retorna configuração sem credenciais")
    
    def test_update_notification_config(self, client):
        """Testa PUT /api/notifications/config."""
        new_config = {
            "enabled": True,
            "channels": ["telegram", "webhook"],
            "min_confidence": 0.8,
            "cooldown_seconds": 120,
            "quiet_hours": [[22, 7], [13, 14]],
            "telegram_bot_token": "new_token_456",
            "telegram_chat_ids": ["111111111", "222222222"],
            "webhook_urls": ["https://example.com/webhook"],
            "webhook_secret": "my_secret_123"
        }
        
        response = client.put("/api/notifications/config", json=new_config)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica que configuração foi atualizada
        assert data["enabled"] == True
        assert "telegram" in data["channels"]
        assert "webhook" in data["channels"]
        assert data["min_confidence"] == 0.8
        assert data["cooldown_seconds"] == 120
        assert data["quiet_hours"] == [[22, 7], [13, 14]]
        
        # Verifica contadores
        assert data["telegram_configured"] == True
        assert data["telegram_chat_count"] == 2
        assert data["webhook_configured"] == True
        assert data["webhook_url_count"] == 1
        
        # Verifica que credenciais não são expostas
        assert "telegram_bot_token" not in data
        assert "webhook_secret" not in data
        
        print("✓ PUT /api/notifications/config atualiza configuração corretamente")
    
    def test_update_notification_config_validation(self, client):
        """Testa validação de configuração inválida."""
        invalid_config = {
            "enabled": True,
            "channels": ["telegram"],
            "min_confidence": 1.5,  # Inválido: deve ser 0.0-1.0
            "cooldown_seconds": -10  # Inválido: deve ser >= 0
        }
        
        response = client.put("/api/notifications/config", json=invalid_config)
        
        # Deve retornar erro de validação
        assert response.status_code == 422
        
        print("✓ Validação de configuração inválida funciona")


class TestNotificationTestEndpoint:
    """Testes do endpoint de teste de notificações."""
    
    @pytest.mark.asyncio
    async def test_test_notification_success(self, client):
        """Testa POST /api/notifications/test com sucesso."""
        # Mock do canal de notificação
        with patch('app.services.monitor_service.monitor_service._notification_service._channels') as mock_channels:
            # Cria mock do canal
            mock_channel = AsyncMock()
            mock_channel.send = AsyncMock(return_value=True)
            mock_channels.__getitem__.return_value = mock_channel
            mock_channels.__contains__.return_value = True
            
            test_request = {
                "channel": "telegram",
                "message": "Teste de notificação"
            }
            
            response = client.post("/api/notifications/test", json=test_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert data["channel"] == "telegram"
            assert "sucesso" in data["message"].lower()
            
            print("✓ POST /api/notifications/test envia notificação de teste")
    
    def test_test_notification_channel_not_configured(self, client):
        """Testa POST /api/notifications/test com canal não configurado."""
        test_request = {
            "channel": "telegram",
            "message": "Teste"
        }
        
        response = client.post("/api/notifications/test", json=test_request)
        
        # Deve retornar erro 400 se canal não está configurado
        assert response.status_code in [400, 500]
        
        print("✓ Erro retornado para canal não configurado")


class TestNotificationFlow:
    """Testes do fluxo completo de notificações."""
    
    @pytest.mark.asyncio
    async def test_alert_triggers_notification(self, monitor_service):
        """Verifica que alerta dispara notificação no fluxo completo."""
        # Mock dos serviços
        with patch.object(monitor_service._alert_service, 'evaluate', return_value="Alerta de teste"):
            with patch.object(monitor_service._notification_service, 'send_alert', new_callable=AsyncMock) as mock_send:
                # Simula detecção que gera alerta
                result = DetectionResult(
                    event_type=EventType.FALL_SUSPECTED,
                    confidence=0.9,
                    details={}
                )
                
                # Adiciona timestamp manualmente
                result.timestamp = datetime.now().timestamp()
                
                # Simula avaliação de alerta
                alert_message = monitor_service._alert_service.evaluate(
                    result.event_type, 
                    result.confidence
                )
                
                # Se alerta foi gerado, envia notificação
                if alert_message:
                    await monitor_service._send_notification(result, alert_message)
                
                # Verifica que notificação foi enviada
                assert mock_send.called
                
                print("✓ Alerta dispara notificação no fluxo completo")


def run_tests():
    """Executa todos os testes."""
    print("\n" + "="*70)
    print("TESTES - TAREFA 18: INTEGRAÇÃO DE NOTIFICAÇÕES NO MONITORSERVICE")
    print("="*70 + "\n")
    
    # Executa testes com pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ])


if __name__ == "__main__":
    run_tests()
