# -*- coding: utf-8 -*-
"""
Testes de Propriedade para Event Service

Properties:
  - 9.3: Property 17 — Unauthenticated Data Rejection (HTTP 401/403 sem token válido)
  - 9.6: Property 18 — High Confidence Event Persistence (confidence >= 0.7 → persiste)
  - 9.8: Property 19 — WebSocket Event Broadcast (eventos chegam ao canal do tenant)

Implementa Tarefas 9.3, 9.6, 9.8 | Requisitos: 9.3, 9.5, 9.7
"""

import sys
import os

# conftest.py do event-service já adiciona o root_dir, mas deixamos aqui também
# para execução direta (python test_event_properties.py)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
service_dir = os.path.abspath(os.path.dirname(__file__))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

import asyncio
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from hypothesis import given, strategies as st
from hypothesis import settings as h_settings


# ─── helpers ─────────────────────────────────────────────────────────────────

def _run(coro):
    """Executa coroutine em loop limpo para testes Hypothesis síncronos."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_valid_device_token(
    device_id: str | None = None,
    tenant_id: str | None = None,
    plan_type: str = "basic",
) -> str:
    """Gera JWT de dispositivo válido usando a chave default de settings."""
    import jwt as _jwt

    device_id = device_id or str(uuid4())
    tenant_id = tenant_id or str(uuid4())

    payload = {
        "sub": tenant_id,
        "role": "device",
        "device_id": device_id,
        "tenant_id": tenant_id,
        "plan_type": plan_type,
        "exp": 9_999_999_999,  # Nunca expira no contexto de testes
    }
    return _jwt.encode(payload, "change-me-in-production", algorithm="HS256")


def _make_processor():
    """
    Cria EventProcessor com db_manager e rabbitmq_client mockados.
    Retorna (processor, session_mock).
    """
    from services.event_processor import EventProcessor

    session_mock = AsyncMock()
    session_mock.add = MagicMock()
    session_mock.commit = AsyncMock()
    session_mock.refresh = AsyncMock(side_effect=lambda _: None)

    # Simula async context manager: `async with db_manager.get_session() as session`
    ctx_mock = MagicMock()
    ctx_mock.__aenter__ = AsyncMock(return_value=session_mock)
    ctx_mock.__aexit__ = AsyncMock(return_value=False)

    db_manager = MagicMock()
    db_manager.get_session.return_value = ctx_mock

    rabbitmq_client = AsyncMock()
    rabbitmq_client.publish = AsyncMock()

    processor = EventProcessor(db_manager=db_manager, rabbitmq_client=rabbitmq_client)
    return processor, session_mock


# ─── Property 17: Unauthenticated Data Rejection (9.3) ───────────────────────

class TestUnauthenticatedDataRejection:
    """
    Property 17: Dados sem token JWT válido são rejeitados com HTTP 401.
    Requisito 9.3.
    """

    def test_malformed_token_raises_401(self):
        """Token malformado deve resultar em HTTPException 401."""
        from middleware.auth_middleware import require_device_auth
        from fastapi.security import HTTPAuthorizationCredentials

        bad_tokens = [
            "not.a.jwt",
            "eyJhbGciOiJIUzI1NiJ9.bad.payload",
            "random-garbage-1234",
            "Bearer eyJhbGciOiJIUzI1NiJ9",
        ]

        for token in bad_tokens:
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=token
            )
            with pytest.raises(HTTPException) as exc:
                require_device_auth(credentials)
            assert exc.value.status_code == 401, (
                f"Token '{token[:30]}' deveria retornar 401, got {exc.value.status_code}"
            )

    @given(
        sub=st.uuids().map(str),
        wrong_role=st.sampled_from(["tenant", "admin", "superuser", "guest"]),
    )
    @h_settings(max_examples=30)
    def test_property_non_device_role_raises_403(self, sub: str, wrong_role: str):
        """
        Property 17a: Token JWT com role != 'device' deve ser rejeitado com 403.
        """
        import jwt as _jwt
        from middleware.auth_middleware import require_device_auth
        from fastapi.security import HTTPAuthorizationCredentials

        payload = {
            "sub": sub,
            "role": wrong_role,
            "device_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "exp": 9_999_999_999,
        }
        token = _jwt.encode(payload, "change-me-in-production", algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )
        with pytest.raises(HTTPException) as exc:
            require_device_auth(credentials)
        assert exc.value.status_code == 403

    @given(
        tenant_id=st.uuids().map(str),
        device_id=st.uuids().map(str),
        plan_type=st.sampled_from(["basic", "premium"]),
    )
    @h_settings(max_examples=30)
    def test_property_valid_device_token_is_accepted(
        self, tenant_id: str, device_id: str, plan_type: str
    ):
        """
        Property 17b: Token JWT com role='device' válido é aceito sem exceção.
        """
        from middleware.auth_middleware import require_device_auth
        from fastapi.security import HTTPAuthorizationCredentials

        token = _make_valid_device_token(
            device_id=device_id, tenant_id=tenant_id, plan_type=plan_type
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        result = require_device_auth(credentials)

        assert result["device_id"] == device_id
        assert result["tenant_id"] == tenant_id
        assert result["plan_type"] == plan_type

    def test_expired_token_raises_401(self):
        """Token expirado deve resultar em HTTPException 401."""
        import jwt as _jwt
        from middleware.auth_middleware import require_device_auth
        from fastapi.security import HTTPAuthorizationCredentials

        payload = {
            "sub": str(uuid4()),
            "role": "device",
            "device_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "exp": 1,  # Timestamp no passado (expirado)
        }
        token = _jwt.encode(payload, "change-me-in-production", algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )
        with pytest.raises(HTTPException) as exc:
            require_device_auth(credentials)
        assert exc.value.status_code == 401

    def test_wrong_secret_raises_401(self):
        """Token assinado com segredo diferente deve resultar em HTTPException 401."""
        import jwt as _jwt
        from middleware.auth_middleware import require_device_auth
        from fastapi.security import HTTPAuthorizationCredentials

        payload = {
            "sub": str(uuid4()),
            "role": "device",
            "device_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "exp": 9_999_999_999,
        }
        token = _jwt.encode(payload, "WRONG-SECRET-KEY", algorithm="HS256")

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )
        with pytest.raises(HTTPException) as exc:
            require_device_auth(credentials)
        assert exc.value.status_code == 401


# ─── Property 18: High Confidence Event Persistence (9.6) ────────────────────

class TestHighConfidenceEventPersistence:
    """
    Property 18: Eventos com confidence >= 0.7 são persistidos no banco.
    Eventos com confidence < 0.7 são descartados.
    Requisito 9.5.
    """

    @given(confidence=st.floats(min_value=0.7, max_value=1.0))
    @h_settings(max_examples=30)
    def test_property_high_confidence_is_persisted(self, confidence: float):
        """
        Property 18a: Para qualquer confidence >= 0.7, session.add() é chamado.
        """
        async def _inner():
            processor, session_mock = _make_processor()

            tenant_config = {
                "plan_type": "basic",
                "min_confidence_to_store": 0.7,
                "min_confidence_to_notify": 0.8,
            }

            detection_result = MagicMock()
            detection_result.event_type = "presence"
            detection_result.confidence = confidence
            detection_result.metadata = {}

            with patch.object(
                processor, "_get_tenant_config", new=AsyncMock(return_value=tenant_config)
            ):
                with patch(
                    "services.event_processor.EventDetector"
                ) as MockDetector:
                    MockDetector.return_value.detect.return_value = detection_result

                    with patch(
                        "services.event_processor.websocket_manager"
                    ) as mock_ws:
                        mock_ws.broadcast_to_tenant = AsyncMock()

                        await processor._process_message({
                            "tenant_id": str(uuid4()),
                            "device_id": str(uuid4()),
                            "features": {"rssi_normalized": 0.8},
                            "timestamp": datetime.utcnow().timestamp(),
                            "data_type": "rssi",
                        })

            session_mock.add.assert_called_once()
            session_mock.commit.assert_called_once()

        _run(_inner())

    @given(confidence=st.floats(min_value=0.0, max_value=0.6999))
    @h_settings(max_examples=30)
    def test_property_low_confidence_is_not_persisted(self, confidence: float):
        """
        Property 18b: Para qualquer confidence < 0.7, session.add() NÃO é chamado.
        """
        async def _inner():
            processor, session_mock = _make_processor()

            tenant_config = {
                "plan_type": "basic",
                "min_confidence_to_store": 0.7,
                "min_confidence_to_notify": 0.8,
            }

            detection_result = MagicMock()
            detection_result.event_type = "presence"
            detection_result.confidence = confidence
            detection_result.metadata = {}

            with patch.object(
                processor, "_get_tenant_config", new=AsyncMock(return_value=tenant_config)
            ):
                with patch(
                    "services.event_processor.EventDetector"
                ) as MockDetector:
                    MockDetector.return_value.detect.return_value = detection_result

                    await processor._process_message({
                        "tenant_id": str(uuid4()),
                        "device_id": str(uuid4()),
                        "features": {"rssi_normalized": 0.3},
                        "timestamp": datetime.utcnow().timestamp(),
                        "data_type": "rssi",
                    })

            session_mock.add.assert_not_called()
            session_mock.commit.assert_not_called()

        _run(_inner())

    @pytest.mark.asyncio
    async def test_threshold_boundary_exactly_0_7_is_persisted(self):
        """Confidence exatamente 0.7 (threshold) deve ser persistido."""
        processor, session_mock = _make_processor()

        tenant_config = {
            "plan_type": "basic",
            "min_confidence_to_store": 0.7,
            "min_confidence_to_notify": 0.8,
        }

        detection_result = MagicMock()
        detection_result.event_type = "presence"
        detection_result.confidence = 0.7
        detection_result.metadata = {}

        with patch.object(
            processor, "_get_tenant_config", new=AsyncMock(return_value=tenant_config)
        ):
            with patch("services.event_processor.EventDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = detection_result
                with patch(
                    "services.event_processor.websocket_manager"
                ) as mock_ws:
                    mock_ws.broadcast_to_tenant = AsyncMock()
                    await processor._process_message({
                        "tenant_id": str(uuid4()),
                        "device_id": str(uuid4()),
                        "features": {},
                        "timestamp": datetime.utcnow().timestamp(),
                        "data_type": "rssi",
                    })

        session_mock.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_event_detected_skips_persistence(self):
        """Se EventDetector retornar None, nada é persistido."""
        processor, session_mock = _make_processor()

        with patch.object(
            processor,
            "_get_tenant_config",
            new=AsyncMock(return_value={"min_confidence_to_store": 0.7, "min_confidence_to_notify": 0.8}),
        ):
            with patch("services.event_processor.EventDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = None

                await processor._process_message({
                    "tenant_id": str(uuid4()),
                    "device_id": str(uuid4()),
                    "features": {},
                    "timestamp": datetime.utcnow().timestamp(),
                    "data_type": "rssi",
                })

        session_mock.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_high_confidence_triggers_notification_queue(self):
        """
        Eventos com confidence >= min_confidence_to_notify (0.8) publicam
        mensagem na fila 'notification_delivery'.
        """
        processor, session_mock = _make_processor()

        tenant_config = {
            "plan_type": "basic",
            "min_confidence_to_store": 0.7,
            "min_confidence_to_notify": 0.8,
        }

        detection_result = MagicMock()
        detection_result.event_type = "fall_suspected"
        detection_result.confidence = 0.9
        detection_result.metadata = {}

        with patch.object(
            processor, "_get_tenant_config", new=AsyncMock(return_value=tenant_config)
        ):
            with patch("services.event_processor.EventDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = detection_result
                with patch(
                    "services.event_processor.websocket_manager"
                ) as mock_ws:
                    mock_ws.broadcast_to_tenant = AsyncMock()
                    await processor._process_message({
                        "tenant_id": str(uuid4()),
                        "device_id": str(uuid4()),
                        "features": {},
                        "timestamp": datetime.utcnow().timestamp(),
                        "data_type": "rssi",
                    })

        # Deve ter publicado na fila de notificações
        processor.rabbitmq_client.publish.assert_called()
        call_args = processor.rabbitmq_client.publish.call_args
        assert "notification_delivery" in str(call_args)


# ─── Property 19: WebSocket Event Broadcast (9.8) ────────────────────────────

class TestWebSocketEventBroadcast:
    """
    Property 19: Eventos de um tenant chegam apenas ao canal WebSocket desse tenant.
    Requisito 9.7.
    """

    @pytest.mark.asyncio
    async def test_property_broadcast_calls_websocket_manager(self):
        """
        Property 19a: _broadcast_event() sempre chama
        websocket_manager.broadcast_to_tenant() com o tenant_id correto.
        """
        from services.event_processor import EventProcessor

        processor = EventProcessor(MagicMock(), AsyncMock())

        tenant_id = uuid4()
        event_data = {
            "event_id": str(uuid4()),
            "device_id": str(uuid4()),
            "event_type": "presence",
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {},
        }

        with patch("services.event_processor.websocket_manager") as mock_ws:
            mock_ws.broadcast_to_tenant = AsyncMock()
            await processor._broadcast_event(tenant_id, event_data)

            mock_ws.broadcast_to_tenant.assert_called_once()
            call_kwargs = mock_ws.broadcast_to_tenant.call_args

            # Verifica que o tenant_id correto foi passado
            passed_tenant = (
                call_kwargs.kwargs.get("tenant_id")
                or (call_kwargs.args[0] if call_kwargs.args else None)
            )
            assert passed_tenant == tenant_id

    @given(
        event_type=st.sampled_from(
            ["presence", "movement", "fall_suspected", "no_presence", "prolonged_inactivity"]
        ),
        confidence=st.floats(min_value=0.7, max_value=1.0),
    )
    @h_settings(max_examples=30)
    def test_property_broadcast_message_has_correct_format(
        self, event_type: str, confidence: float
    ):
        """
        Property 19b: A mensagem de broadcast tem sempre o formato
        {"type": "event", "data": {...}}.
        """
        async def _inner():
            from services.event_processor import EventProcessor

            processor = EventProcessor(MagicMock(), AsyncMock())
            tenant_id = uuid4()
            event_data = {
                "event_id": str(uuid4()),
                "device_id": str(uuid4()),
                "event_type": event_type,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {},
            }

            captured: list[dict] = []

            async def capture(tenant_id, message):
                captured.append(message)

            with patch("services.event_processor.websocket_manager") as mock_ws:
                mock_ws.broadcast_to_tenant = AsyncMock(side_effect=capture)
                await processor._broadcast_event(tenant_id, event_data)

            assert len(captured) == 1
            msg = captured[0]
            assert msg["type"] == "event"
            assert "data" in msg
            assert msg["data"]["event_type"] == event_type

        _run(_inner())

    @pytest.mark.asyncio
    async def test_broadcast_failure_does_not_crash_processor(self):
        """
        Property 19c: Falha no broadcast WebSocket não propaga exceção.
        O loop de processamento deve continuar funcionando.
        """
        from services.event_processor import EventProcessor

        processor = EventProcessor(MagicMock(), AsyncMock())
        tenant_id = uuid4()

        with patch("services.event_processor.websocket_manager") as mock_ws:
            mock_ws.broadcast_to_tenant = AsyncMock(
                side_effect=ConnectionError("WebSocket disconnected")
            )
            # Não deve lançar exceção
            await processor._broadcast_event(
                tenant_id, {"event_type": "presence"}
            )

    @pytest.mark.asyncio
    async def test_websocket_manager_tenant_channel_isolation(self):
        """
        Property 19d: WebSocketManager envia mensagens apenas para o tenant correto.
        Isolamento multi-tenant no canal WebSocket.
        """
        from shared.websocket import WebSocketManager

        manager = WebSocketManager()

        ws_a = MagicMock()
        ws_a.send_text = AsyncMock()
        ws_b = MagicMock()
        ws_b.send_text = AsyncMock()

        tenant_a = uuid4()
        tenant_b = uuid4()

        await manager.connect(ws_a, tenant_a)
        await manager.connect(ws_b, tenant_b)

        message = {"event_type": "presence", "confidence": 0.9}
        await manager.broadcast_to_tenant(tenant_a, message)

        ws_a.send_text.assert_called_once()
        ws_b.send_text.assert_not_called()

        # Inverso: tenant_b recebe, tenant_a não
        ws_a.send_text.reset_mock()
        ws_b.send_text.reset_mock()

        await manager.broadcast_to_tenant(tenant_b, message)

        ws_a.send_text.assert_not_called()
        ws_b.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_processing_pipeline_broadcasts_event(self):
        """
        Teste de integração parcial: _process_message() para evento com
        confidence alta deve terminar com broadcast via WebSocket.
        """
        processor, session_mock = _make_processor()

        tenant_config = {
            "plan_type": "basic",
            "min_confidence_to_store": 0.7,
            "min_confidence_to_notify": 0.8,
        }

        detection_result = MagicMock()
        detection_result.event_type = "presence"
        detection_result.confidence = 0.9
        detection_result.metadata = {}

        with patch.object(
            processor, "_get_tenant_config", new=AsyncMock(return_value=tenant_config)
        ):
            with patch("services.event_processor.EventDetector") as MockDetector:
                MockDetector.return_value.detect.return_value = detection_result

                with patch(
                    "services.event_processor.websocket_manager"
                ) as mock_ws:
                    mock_ws.broadcast_to_tenant = AsyncMock()

                    await processor._process_message({
                        "tenant_id": str(uuid4()),
                        "device_id": str(uuid4()),
                        "features": {"rssi_normalized": 0.9},
                        "timestamp": datetime.utcnow().timestamp(),
                        "data_type": "rssi",
                    })

                    mock_ws.broadcast_to_tenant.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
