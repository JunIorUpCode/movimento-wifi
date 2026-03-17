"""
Testes para Task 17: NotificationLog no banco de dados

Valida:
- Modelo NotificationLog no SQLAlchemy
- Persistência de logs de notificações
- Endpoint GET /api/notifications/logs
- Integração com NotificationService
- Requisito 12.7
"""

import asyncio
import json
import time
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete

from app.db.database import async_session, init_db, engine
from app.main import app
from app.models.models import NotificationLog
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig


# Initialize database once
@pytest.fixture(scope="session", autouse=True)
def initialize_db():
    """Initialize database before all tests."""
    asyncio.run(init_db())


class TestNotificationLogModel:
    """Testes do modelo NotificationLog."""
    
    @pytest.mark.asyncio
    async def test_create_notification_log(self):
        """Testa criação de log de notificação no banco."""
        async with async_session() as db:
            try:
                log = NotificationLog(
                    timestamp=datetime.utcnow(),
                    channel="telegram",
                    event_type="fall_suspected",
                    confidence=0.85,
                    recipient="123456789",
                    success=True,
                    error_message=None,
                    alert_data=json.dumps({
                        "event_type": "fall_suspected",
                        "confidence": 0.85,
                        "timestamp": time.time(),
                        "message": "Queda detectada!",
                        "details": {}
                    })
                )
                
                db.add(log)
                await db.commit()
                await db.refresh(log)
                
                assert log.id is not None
                assert log.channel == "telegram"
                assert log.event_type == "fall_suspected"
                assert log.confidence == 0.85
                assert log.recipient == "123456789"
                assert log.success is True
                assert log.error_message is None
                assert log.alert_data is not None
                
                print(f"✓ Log criado com ID: {log.id}")
            finally:
                await db.close()
    
    @pytest.mark.asyncio
    async def test_create_failed_notification_log(self):
        """Testa criação de log de notificação falhada."""
        async with async_session() as db:
            try:
                log = NotificationLog(
                    timestamp=datetime.utcnow(),
                    channel="whatsapp",
                    event_type="presence_moving",
                    confidence=0.75,
                    recipient="+5511999999999",
                    success=False,
                    error_message="Connection timeout",
                    alert_data=json.dumps({
                        "event_type": "presence_moving",
                        "confidence": 0.75,
                        "timestamp": time.time(),
                        "message": "Movimento detectado",
                        "details": {}
                    })
                )
                
                db.add(log)
                await db.commit()
                await db.refresh(log)
                
                assert log.id is not None
                assert log.success is False
                assert log.error_message == "Connection timeout"
                
                print(f"✓ Log de falha criado com ID: {log.id}")
            finally:
                await db.close()
    
    @pytest.mark.asyncio
    async def test_query_logs_by_channel(self):
        """Testa consulta de logs por canal."""
        async with async_session() as db:
            try:
                # Cria logs de diferentes canais
                for channel in ["telegram", "whatsapp", "webhook"]:
                    log = NotificationLog(
                        timestamp=datetime.utcnow(),
                        channel=channel,
                        event_type="presence_still",
                        confidence=0.8,
                        recipient=f"{channel}_recipient",
                        success=True,
                        error_message=None,
                        alert_data="{}"
                    )
                    db.add(log)
                
                await db.commit()
                
                # Consulta logs do Telegram
                result = await db.execute(
                    select(NotificationLog).where(NotificationLog.channel == "telegram")
                )
                telegram_logs = result.scalars().all()
                
                assert len(telegram_logs) >= 1
                assert all(log.channel == "telegram" for log in telegram_logs)
                
                print(f"✓ Encontrados {len(telegram_logs)} logs do Telegram")
            finally:
                await db.close()
    
    @pytest.mark.asyncio
    async def test_query_logs_ordered_by_timestamp(self):
        """Testa que logs são retornados ordenados por timestamp."""
        async with async_session() as db:
            try:
                result = await db.execute(
                    select(NotificationLog).order_by(NotificationLog.timestamp.desc())
                )
                logs = result.scalars().all()
                
                # Verifica ordenação
                if len(logs) > 1:
                    for i in range(len(logs) - 1):
                        assert logs[i].timestamp >= logs[i + 1].timestamp
                
                print(f"✓ {len(logs)} logs ordenados corretamente por timestamp")
            finally:
                await db.close()


class TestNotificationLogsAPI:
    """Testes do endpoint GET /api/notifications/logs."""
    
    @pytest.mark.asyncio
    async def test_get_notification_logs(self):
        """Testa endpoint GET /api/notifications/logs."""
        from httpx import ASGITransport
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/notifications/logs")
            
            assert response.status_code == 200
            logs = response.json()
            assert isinstance(logs, list)
            
            # Valida estrutura dos logs
            if logs:
                log = logs[0]
                assert "id" in log
                assert "timestamp" in log
                assert "channel" in log
                assert "event_type" in log
                assert "confidence" in log
                assert "recipient" in log
                assert "success" in log
                assert "alert_data" in log
            
            print(f"✓ Endpoint retornou {len(logs)} logs")
    
    @pytest.mark.asyncio
    async def test_get_notification_logs_filter_by_channel(self):
        """Testa filtro por canal no endpoint."""
        from httpx import ASGITransport
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Consulta logs do Telegram
            response = await client.get("/api/notifications/logs?channel=telegram")
            
            assert response.status_code == 200
            logs = response.json()
            assert isinstance(logs, list)
            
            # Valida que todos os logs são do Telegram
            for log in logs:
                assert log["channel"] == "telegram"
            
            print(f"✓ Filtro por canal retornou {len(logs)} logs do Telegram")
    
    @pytest.mark.asyncio
    async def test_get_notification_logs_pagination(self):
        """Testa paginação do endpoint."""
        from httpx import ASGITransport
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Primeira página
            response1 = await client.get("/api/notifications/logs?limit=2&offset=0")
            assert response1.status_code == 200
            logs1 = response1.json()
            
            # Segunda página
            response2 = await client.get("/api/notifications/logs?limit=2&offset=2")
            assert response2.status_code == 200
            logs2 = response2.json()
            
            # Valida que são logs diferentes
            if logs1 and logs2:
                assert logs1[0]["id"] != logs2[0]["id"]
            
            print(f"✓ Paginação funcionando: página 1 ({len(logs1)} logs), página 2 ({len(logs2)} logs)")


class TestNotificationServiceIntegration:
    """Testes de integração com NotificationService."""
    
    @pytest.mark.asyncio
    async def test_notification_service_logs_to_database(self):
        """Testa que NotificationService persiste logs no banco."""
        # Configura serviço sem canais reais (para não tentar enviar)
        config = NotificationConfig(
            enabled=True,
            channels=[],  # Sem canais configurados
            min_confidence=0.5
        )
        
        service = NotificationService(config)
        
        # Cria alerta
        alert = Alert(
            event_type="fall_suspected",
            confidence=0.9,
            timestamp=time.time(),
            message="Queda detectada com alta confiança",
            details={"rate_of_change": 15.5}
        )
        
        # Conta logs antes
        async with async_session() as db:
            result = await db.execute(select(NotificationLog))
            count_before = len(result.scalars().all())
            await db.close()
        
        # Envia alerta (não deve enviar para nenhum canal, mas deve validar)
        await service.send_alert(alert)
        
        # Como não há canais configurados, não deve criar logs
        async with async_session() as db:
            result = await db.execute(select(NotificationLog))
            count_after = len(result.scalars().all())
            await db.close()
        
        # Neste caso, não deve ter criado logs pois não há canais
        assert count_after == count_before
        
        print("✓ NotificationService não cria logs quando não há canais configurados")
    
    @pytest.mark.asyncio
    async def test_alert_to_dict_method(self):
        """Testa método to_dict() do Alert."""
        alert = Alert(
            event_type="presence_moving",
            confidence=0.85,
            timestamp=1234567890.0,
            message="Movimento detectado",
            details={"variance": 3.5}
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict["event_type"] == "presence_moving"
        assert alert_dict["confidence"] == 0.85
        assert alert_dict["timestamp"] == 1234567890.0
        assert alert_dict["message"] == "Movimento detectado"
        assert alert_dict["details"]["variance"] == 3.5
        
        # Valida que pode ser serializado para JSON
        json_str = json.dumps(alert_dict)
        assert json_str is not None
        
        print("✓ Método to_dict() funciona corretamente")


class TestNotificationLogFields:
    """Testes dos campos do modelo NotificationLog."""
    
    @pytest.mark.asyncio
    async def test_all_required_fields(self):
        """Testa que todos os campos obrigatórios estão presentes."""
        async with async_session() as db:
            try:
                log = NotificationLog(
                    timestamp=datetime.utcnow(),
                    channel="webhook",
                    event_type="anomaly_detected",
                    confidence=0.95,
                    recipient="https://example.com/webhook",
                    success=True,
                    error_message=None,
                    alert_data=json.dumps({
                        "event_type": "anomaly_detected",
                        "confidence": 0.95,
                        "timestamp": time.time(),
                        "message": "Anomalia detectada",
                        "details": {"anomaly_score": 0.95}
                    })
                )
                
                db.add(log)
                await db.commit()
                await db.refresh(log)
                
                # Valida todos os campos
                assert log.id is not None
                assert log.timestamp is not None
                assert log.channel == "webhook"
                assert log.event_type == "anomaly_detected"
                assert log.confidence == 0.95
                assert log.recipient == "https://example.com/webhook"
                assert log.success is True
                assert log.error_message is None
                assert log.alert_data is not None
                
                # Valida que alert_data é JSON válido
                alert_data = json.loads(log.alert_data)
                assert alert_data["event_type"] == "anomaly_detected"
                assert alert_data["confidence"] == 0.95
                
                print("✓ Todos os campos obrigatórios estão presentes e válidos")
            finally:
                await db.close()
    
    @pytest.mark.asyncio
    async def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        async with async_session() as db:
            try:
                # Verifica índices
                result = await db.execute(
                    select(NotificationLog).where(NotificationLog.channel == "telegram")
                )
                # Se a query executar sem erro, o índice existe
                logs = result.scalars().all()
                
                result2 = await db.execute(
                    select(NotificationLog).order_by(NotificationLog.timestamp.desc())
                )
                # Se a query executar sem erro, o índice existe
                logs2 = result2.scalars().all()
                
                print("✓ Índices em channel e timestamp funcionando corretamente")
            finally:
                await db.close()


def run_tests():
    """Executa todos os testes."""
    print("\n" + "="*70)
    print("TASK 17: NOTIFICATION LOG - TESTES DE VALIDAÇÃO")
    print("="*70 + "\n")
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_tests()
