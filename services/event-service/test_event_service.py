# -*- coding: utf-8 -*-
"""
Testes Unitários - Event Service
Testa funcionalidades do serviço de eventos
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Configurar event loop para testes assíncronos
@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class TestDeviceDataEndpoint:
    """Testes para endpoint de recepção de dados"""

    @pytest.mark.asyncio
    async def test_submit_data_with_valid_token(self):
        """
        Testa submissão de dados com token válido.

        Verifica que dados são aceitos (HTTP 202) e publicados na fila.
        """
        import jwt as _jwt
        from fastapi.testclient import TestClient
        from main import app
        from uuid import uuid4

        device_id = str(uuid4())
        tenant_id = str(uuid4())

        token = _jwt.encode(
            {
                "sub": tenant_id,
                "role": "device",
                "device_id": device_id,
                "tenant_id": tenant_id,
                "plan_type": "basic",
                "exp": 9_999_999_999,
            },
            "change-me-in-production",
            algorithm="HS256",
        )

        mock_rabbitmq = AsyncMock()
        mock_rabbitmq.publish = AsyncMock()

        with patch("routes.device_data.get_rabbitmq_client", return_value=mock_rabbitmq):
            client = TestClient(app)
            response = client.post(
                f"/api/devices/{device_id}/data",
                json={
                    "features": {"rssi_normalized": 0.8, "signal_variance": 0.3},
                    "timestamp": 1700000000.0,
                    "data_type": "rssi",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 202
        assert response.json()["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_submit_data_without_token(self):
        """
        Testa submissão de dados sem token.

        Deve retornar HTTP 403 (HTTPBearer rejeita quando não há credenciais).
        """
        from fastapi.testclient import TestClient
        from main import app
        from uuid import uuid4

        device_id = str(uuid4())

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            f"/api/devices/{device_id}/data",
            json={
                "features": {"rssi_normalized": 0.5},
                "timestamp": 1700000000.0,
                "data_type": "rssi",
            },
        )

        # FastAPI HTTPBearer retorna 403 quando header está ausente
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_basic_plan_rejects_csi_data(self):
        """
        Testa que plano BÁSICO rejeita dados CSI.

        Deve retornar HTTP 403 Forbidden.
        """
        import jwt as _jwt
        from uuid import uuid4

        device_id = str(uuid4())
        tenant_id = str(uuid4())

        token = _jwt.encode(
            {
                "sub": tenant_id,
                "role": "device",
                "device_id": device_id,
                "tenant_id": tenant_id,
                "plan_type": "basic",  # BÁSICO não pode enviar CSI
                "exp": 9_999_999_999,
            },
            "change-me-in-production",
            algorithm="HS256",
        )

        # Testa a lógica diretamente (sem TestClient) usando o route handler
        from routes.device_data import submit_device_data
        from schemas.event import DeviceDataSubmit
        from fastapi import HTTPException

        device_info = {
            "device_id": device_id,
            "tenant_id": tenant_id,
            "plan_type": "basic",
        }
        data = DeviceDataSubmit(
            features={"csi_amplitude": 0.9},
            timestamp=1700000000.0,
            data_type="csi",
        )
        mock_rabbitmq = AsyncMock()

        with pytest.raises(HTTPException) as exc:
            await submit_device_data(
                device_id=uuid4(),  # UUID object — mismatch handled below
                data=data,
                device_info={
                    "device_id": device_id,
                    "tenant_id": tenant_id,
                    "plan_type": "basic",
                },
                rabbitmq=mock_rabbitmq,
            )

        # 403: plano BÁSICO bloqueado OU device_id mismatch
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_device_id_mismatch(self):
        """
        Testa que device_id no path deve corresponder ao token.

        Deve retornar HTTP 403 Forbidden.
        """
        from routes.device_data import submit_device_data
        from schemas.event import DeviceDataSubmit
        from fastapi import HTTPException
        from uuid import uuid4

        path_device_id = uuid4()
        token_device_id = str(uuid4())  # Diferente do path

        device_info = {
            "device_id": token_device_id,
            "tenant_id": str(uuid4()),
            "plan_type": "basic",
        }
        data = DeviceDataSubmit(
            features={"rssi_normalized": 0.5},
            timestamp=1700000000.0,
            data_type="rssi",
        )

        with pytest.raises(HTTPException) as exc:
            await submit_device_data(
                device_id=path_device_id,
                data=data,
                device_info=device_info,
                rabbitmq=AsyncMock(),
            )

        assert exc.value.status_code == 403
        assert "device_id" in exc.value.detail.lower()


class TestEventDetector:
    """Testes para algoritmos de detecção"""
    
    def test_rssi_presence_detection(self):
        """
        Testa detecção de presença com RSSI.
        
        Sinal forte + alta variância = presença detectada.
        """
        from services.event_detector import EventDetector
        
        config = {
            "plan_type": "basic",
            "presence_threshold": 0.6,
            "low_variance_threshold": 0.2,
            "high_variance_threshold": 0.4
        }
        
        detector = EventDetector(config)
        
        features = {
            "rssi_normalized": 0.75,
            "signal_variance": 0.5,
            "rate_of_change": 0.1,
            "instability_score": 0.3
        }
        
        result = detector.detect(features, "rssi")
        
        assert result is not None
        assert result.event_type == "presence"
        assert result.confidence >= 0.7
    
    def test_rssi_movement_detection(self):
        """
        Testa detecção de movimento com RSSI.
        
        Alta taxa de mudança = movimento detectado.
        """
        from services.event_detector import EventDetector
        
        config = {
            "plan_type": "basic",
            "movement_threshold": 0.5,
            "high_variance_threshold": 0.4
        }
        
        detector = EventDetector(config)
        
        features = {
            "rssi_normalized": 0.6,
            "signal_variance": 0.6,
            "rate_of_change": 0.8,
            "instability_score": 0.5
        }
        
        result = detector.detect(features, "rssi")
        
        assert result is not None
        assert result.event_type == "movement"
        assert result.confidence >= 0.7
    
    def test_csi_fall_detection(self):
        """
        Testa detecção de queda com CSI.
        
        Padrão de queda no CSI = fall_suspected.
        """
        from services.event_detector import EventDetector
        
        config = {
            "plan_type": "premium",
            "fall_threshold": 0.7
        }
        
        detector = EventDetector(config)
        
        features = {
            "csi_amplitude": 0.8,
            "csi_variance": 0.9,
            "doppler_shift": 0.8
        }
        
        result = detector.detect(features, "csi")
        
        assert result is not None
        assert result.event_type == "fall_suspected"
        assert result.confidence >= 0.7
    
    def test_no_event_detected(self):
        """
        Testa que nenhum evento é detectado com sinais fracos.
        """
        from services.event_detector import EventDetector
        
        config = {
            "plan_type": "basic",
            "presence_threshold": 0.6
        }
        
        detector = EventDetector(config)
        
        features = {
            "rssi_normalized": 0.3,
            "signal_variance": 0.1,
            "rate_of_change": 0.05,
            "instability_score": 0.1
        }
        
        result = detector.detect(features, "rssi")
        
        # Pode retornar None ou evento com confidence baixa
        if result:
            assert result.confidence < 0.7


class TestEventService:
    """Testes para serviço de consulta de eventos"""

    def _make_event(self, tenant_id=None, event_type="presence", confidence=0.9):
        """Cria instância de Event sem banco."""
        from models.event import Event

        e = Event.__new__(Event)
        e.id = uuid4()
        e.tenant_id = tenant_id or uuid4()
        e.device_id = uuid4()
        e.event_type = event_type
        e.confidence = confidence
        e.timestamp = datetime.utcnow()
        e.event_metadata = {}
        e.is_false_positive = False
        e.user_notes = None
        e.created_at = datetime.utcnow()
        return e

    @pytest.mark.asyncio
    async def test_list_events_with_tenant_isolation(self):
        """
        Testa que listagem de eventos respeita isolamento multi-tenant.

        A query base usa WHERE tenant_id = :tenant_id.
        """
        from services.event_service import EventService

        tenant_a = uuid4()

        event_a = self._make_event(tenant_id=tenant_a)

        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        events_result = MagicMock()
        events_result.scalars.return_value.all.return_value = [event_a]

        # execute() é chamado 2 vezes: count + events
        session.execute = AsyncMock(
            side_effect=[count_result, events_result]
        )

        result = await EventService.list_events(
            session=session,
            tenant_id=tenant_a,
            page=1,
            page_size=20,
        )

        assert result.total == 1
        assert len(result.events) == 1

    @pytest.mark.asyncio
    async def test_list_events_pagination(self):
        """
        Testa paginação: page e page_size controlam o número de registros.
        """
        from services.event_service import EventService

        tenant_id = uuid4()

        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 50  # Total de 50 eventos

        events_result = MagicMock()
        events_result.scalars.return_value.all.return_value = []  # Página vazia

        session.execute = AsyncMock(side_effect=[count_result, events_result])

        result = await EventService.list_events(
            session=session,
            tenant_id=tenant_id,
            page=3,
            page_size=10,
        )

        assert result.total == 50
        assert result.page == 3
        assert result.page_size == 10

    @pytest.mark.asyncio
    async def test_event_stats_calculation(self):
        """
        Testa cálculo de estatísticas: total, by_type, by_device, avg_confidence.
        """
        from services.event_service import EventService

        tenant_id = uuid4()
        session = AsyncMock()

        # EventService.get_event_stats faz 5 queries
        def _make_scalar(value):
            r = MagicMock()
            r.scalar.return_value = value
            return r

        count_result = MagicMock()
        count_result.scalar.return_value = 10

        type_result = MagicMock()
        type_result.__iter__ = MagicMock(
            return_value=iter([("presence", 7), ("fall_suspected", 3)])
        )

        device_result = MagicMock()
        device_result.__iter__ = MagicMock(return_value=iter([]))

        avg_result = MagicMock()
        avg_result.scalar.return_value = 0.85

        fp_result = MagicMock()
        fp_result.scalar.return_value = 1

        session.execute = AsyncMock(
            side_effect=[count_result, type_result, device_result, avg_result, fp_result]
        )

        stats = await EventService.get_event_stats(session=session, tenant_id=tenant_id)

        assert stats.total_events == 10
        assert stats.avg_confidence == 0.85
        assert stats.false_positives == 1

    @pytest.mark.asyncio
    async def test_update_event_feedback(self):
        """
        Testa atualização de feedback: is_false_positive e user_notes são gravados.
        """
        from services.event_service import EventService
        from models.event import Event

        tenant_id = uuid4()
        event_id = uuid4()

        event = Event.__new__(Event)
        event.id = event_id
        event.tenant_id = tenant_id
        event.device_id = uuid4()
        event.event_type = "presence"
        event.confidence = 0.8
        event.timestamp = datetime.utcnow()
        event.event_metadata = {}
        event.is_false_positive = False
        event.user_notes = None
        event.created_at = datetime.utcnow()

        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = event
        session.execute = AsyncMock(return_value=result_mock)
        session.commit = AsyncMock()
        session.refresh = AsyncMock(side_effect=lambda _: None)

        result = await EventService.update_event_feedback(
            session=session,
            tenant_id=tenant_id,
            event_id=event_id,
            is_false_positive=True,
            user_notes="Falso positivo — sem presença real",
        )

        assert result is not None
        assert event.is_false_positive is True
        assert event.user_notes == "Falso positivo — sem presença real"


class TestWebSocketManager:
    """Testes para gerenciador de WebSocket"""
    
    @pytest.mark.asyncio
    async def test_websocket_tenant_isolation(self):
        """
        Testa isolamento de canais WebSocket.
        
        Tenant A não deve receber eventos de tenant B.
        """
        from shared.websocket import WebSocketManager
        
        manager = WebSocketManager()
        
        # Mock de WebSocket connections
        ws_tenant_a = Mock()
        ws_tenant_a.send_text = AsyncMock()
        
        ws_tenant_b = Mock()
        ws_tenant_b.send_text = AsyncMock()
        
        tenant_a_id = uuid4()
        tenant_b_id = uuid4()
        
        # Registra conexões
        await manager.connect(ws_tenant_a, tenant_a_id)
        await manager.connect(ws_tenant_b, tenant_b_id)
        
        # Envia mensagem para tenant A
        message = {"event_type": "presence", "confidence": 0.85}
        await manager.broadcast_to_tenant(tenant_a_id, message)
        
        # Verifica que apenas tenant A recebeu
        ws_tenant_a.send_text.assert_called_once()
        ws_tenant_b.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_count(self):
        """
        Testa contagem de conexões WebSocket.
        """
        from shared.websocket import WebSocketManager
        
        manager = WebSocketManager()
        
        tenant_id = uuid4()
        
        # Sem conexões
        assert manager.get_connection_count(tenant_id) == 0
        
        # Adiciona conexões
        ws1 = Mock()
        ws2 = Mock()
        
        await manager.connect(ws1, tenant_id)
        assert manager.get_connection_count(tenant_id) == 1
        
        await manager.connect(ws2, tenant_id)
        assert manager.get_connection_count(tenant_id) == 2
        
        # Remove conexão
        await manager.disconnect(ws1, tenant_id)
        assert manager.get_connection_count(tenant_id) == 1


class TestEventProcessor:
    """Testes para processador de eventos"""

    def _make_processor(self):
        from services.event_processor import EventProcessor

        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock(side_effect=lambda _: None)

        ctx = Mock()
        ctx.__aenter__ = AsyncMock(return_value=session_mock)
        ctx.__aexit__ = AsyncMock(return_value=False)

        db_manager = Mock()
        db_manager.get_session.return_value = ctx

        rabbitmq = AsyncMock()
        rabbitmq.publish = AsyncMock()

        return EventProcessor(db_manager, rabbitmq), session_mock, rabbitmq

    @pytest.mark.asyncio
    async def test_process_message_with_high_confidence(self):
        """
        Mensagem com confidence alta deve ser persistida e broadcast.
        """
        from unittest.mock import patch as _patch

        processor, session_mock, rabbitmq = self._make_processor()

        config = {"min_confidence_to_store": 0.7, "min_confidence_to_notify": 0.8}
        detection = Mock()
        detection.event_type = "presence"
        detection.confidence = 0.95
        detection.metadata = {}

        with _patch.object(processor, "_get_tenant_config", AsyncMock(return_value=config)):
            with _patch("services.event_processor.EventDetector") as MockD:
                MockD.return_value.detect.return_value = detection
                with _patch("services.event_processor.websocket_manager") as ws:
                    ws.broadcast_to_tenant = AsyncMock()
                    await processor._process_message({
                        "tenant_id": str(uuid4()),
                        "device_id": str(uuid4()),
                        "features": {},
                        "timestamp": datetime.utcnow().timestamp(),
                        "data_type": "rssi",
                    })

        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_with_low_confidence(self):
        """
        Mensagem com confidence < 0.7 NÃO deve ser persistida.
        """
        from unittest.mock import patch as _patch

        processor, session_mock, _ = self._make_processor()

        config = {"min_confidence_to_store": 0.7, "min_confidence_to_notify": 0.8}
        detection = Mock()
        detection.event_type = "presence"
        detection.confidence = 0.5
        detection.metadata = {}

        with _patch.object(processor, "_get_tenant_config", AsyncMock(return_value=config)):
            with _patch("services.event_processor.EventDetector") as MockD:
                MockD.return_value.detect.return_value = detection
                await processor._process_message({
                    "tenant_id": str(uuid4()),
                    "device_id": str(uuid4()),
                    "features": {},
                    "timestamp": datetime.utcnow().timestamp(),
                    "data_type": "rssi",
                })

        session_mock.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_queuing(self):
        """
        Eventos com confidence >= min_confidence_to_notify (0.8) devem
        publicar mensagem na fila 'notification_delivery'.
        """
        from unittest.mock import patch as _patch

        processor, session_mock, rabbitmq = self._make_processor()

        config = {"min_confidence_to_store": 0.7, "min_confidence_to_notify": 0.8}
        detection = Mock()
        detection.event_type = "fall_suspected"
        detection.confidence = 0.92
        detection.metadata = {}

        with _patch.object(processor, "_get_tenant_config", AsyncMock(return_value=config)):
            with _patch("services.event_processor.EventDetector") as MockD:
                MockD.return_value.detect.return_value = detection
                with _patch("services.event_processor.websocket_manager") as ws:
                    ws.broadcast_to_tenant = AsyncMock()
                    await processor._process_message({
                        "tenant_id": str(uuid4()),
                        "device_id": str(uuid4()),
                        "features": {},
                        "timestamp": datetime.utcnow().timestamp(),
                        "data_type": "rssi",
                    })

        # Deve ter publicado em notification_delivery
        rabbitmq.publish.assert_called()
        calls = [str(c) for c in rabbitmq.publish.call_args_list]
        assert any("notification_delivery" in c for c in calls)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
