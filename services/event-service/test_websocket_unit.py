# -*- coding: utf-8 -*-
"""
Testes Unitários para WebSocket
Task 17.4: Escrever testes unitários para WebSocket
- Testar autenticação na conexão
- Testar broadcast de eventos
- Testar isolamento de canais
- Testar heartbeat e timeout
"""

import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4, UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from main import app
from shared.config import settings as app_settings
from shared.websocket import websocket_manager


# ============================================================================
# Helpers
# ============================================================================

def generate_jwt_token(
    tenant_id: UUID,
    role: str = "tenant",
    expires_in_hours: int = 1
) -> str:
    """
    Gera um token JWT para testes.
    
    Args:
        tenant_id: ID do tenant
        role: Role do usuário
        expires_in_hours: Horas até expiração
    
    Returns:
        Token JWT
    """
    payload = {
        "sub": str(tenant_id),
        "email": f"tenant-{tenant_id}@example.com",
        "role": role,
        "plan": "premium",
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(
        payload,
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM
    )


# ============================================================================
# Testes de Autenticação
# ============================================================================

def test_websocket_authentication_valid_token():
    """
    Testa autenticação com token JWT válido.
    
    **Cenário**:
    1. Gerar token JWT válido
    2. Conectar ao WebSocket com o token
    3. Verificar que conexão é aceita
    4. Verificar mensagem de boas-vindas
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Deve receber mensagem de boas-vindas
        message = websocket.receive_json()
        
        assert message["type"] == "connected"
        assert message["tenant_id"] == str(tenant_id)
        assert message["channel"] == f"tenant:{tenant_id}"
        assert "heartbeat_interval" in message
        assert message["heartbeat_interval"] == 30
        assert "idle_timeout" in message
        assert message["idle_timeout"] == 300


def test_websocket_authentication_expired_token():
    """
    Testa autenticação com token JWT expirado.
    
    **Cenário**:
    1. Gerar token JWT expirado
    2. Tentar conectar ao WebSocket
    3. Verificar que conexão é rejeitada
    """
    tenant_id = uuid4()
    
    # Gera token expirado (expirou há 1 hora)
    payload = {
        "sub": str(tenant_id),
        "email": f"tenant-{tenant_id}@example.com",
        "role": "tenant",
        "plan": "premium",
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expirado
        "iat": datetime.utcnow() - timedelta(hours=2)
    }
    
    token = jwt.encode(
        payload,
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM
    )
    
    client = TestClient(app)
    
    # Deve rejeitar conexão
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            pass


def test_websocket_authentication_invalid_token():
    """
    Testa autenticação com token JWT inválido.
    
    **Cenário**:
    1. Usar token JWT inválido (assinatura incorreta)
    2. Tentar conectar ao WebSocket
    3. Verificar que conexão é rejeitada
    """
    client = TestClient(app)
    
    # Token inválido
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
    
    # Deve rejeitar conexão
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws?token={invalid_token}") as websocket:
            pass


def test_websocket_authentication_missing_token():
    """
    Testa autenticação sem fornecer token.
    
    **Cenário**:
    1. Tentar conectar ao WebSocket sem token
    2. Verificar que conexão é rejeitada
    """
    client = TestClient(app)
    
    # Deve rejeitar conexão (token é obrigatório)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws") as websocket:
            pass


def test_websocket_authentication_invalid_role():
    """
    Testa autenticação com role inválida.
    
    **Cenário**:
    1. Gerar token com role inválida (não é 'tenant' nem 'admin')
    2. Tentar conectar ao WebSocket
    3. Verificar que conexão é rejeitada
    """
    tenant_id = uuid4()
    
    payload = {
        "sub": str(tenant_id),
        "email": f"tenant-{tenant_id}@example.com",
        "role": "invalid_role",  # Role inválida
        "plan": "premium",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM
    )
    
    client = TestClient(app)
    
    # Deve rejeitar conexão
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            pass


# ============================================================================
# Testes de Broadcast
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_broadcast_single_client():
    """
    Testa broadcast de evento para um único cliente.
    
    **Cenário**:
    1. Conectar cliente
    2. Enviar evento via broadcast
    3. Verificar que cliente recebe o evento
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Recebe mensagem de boas-vindas
        welcome = websocket.receive_json()
        assert welcome["type"] == "connected"
        
        # Cria evento
        event_data = {
            "event_id": str(uuid4()),
            "device_id": str(uuid4()),
            "event_type": "presence",
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {}
        }
        
        # Envia evento via broadcast
        await websocket_manager.broadcast_to_tenant(
            tenant_id=tenant_id,
            message={
                "type": "event",
                "data": event_data
            }
        )
        
        # Aguarda mensagem
        await asyncio.sleep(0.5)
        
        # Deve receber o evento
        message = websocket.receive_json(timeout=2.0)
        
        assert message["type"] == "event"
        assert message["data"]["event_id"] == event_data["event_id"]
        assert message["data"]["event_type"] == "presence"
        assert message["data"]["confidence"] == 0.85


@pytest.mark.asyncio
async def test_websocket_broadcast_multiple_events():
    """
    Testa broadcast de múltiplos eventos sequenciais.
    
    **Cenário**:
    1. Conectar cliente
    2. Enviar 3 eventos diferentes
    3. Verificar que cliente recebe todos os 3 eventos na ordem
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Recebe mensagem de boas-vindas
        websocket.receive_json()
        
        # Envia 3 eventos
        event_types = ["presence", "movement", "fall_suspected"]
        event_ids = []
        
        for event_type in event_types:
            event_id = str(uuid4())
            event_ids.append(event_id)
            
            await websocket_manager.broadcast_to_tenant(
                tenant_id=tenant_id,
                message={
                    "type": "event",
                    "data": {
                        "event_id": event_id,
                        "device_id": str(uuid4()),
                        "event_type": event_type,
                        "confidence": 0.85,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {}
                    }
                }
            )
            
            await asyncio.sleep(0.2)
        
        # Deve receber os 3 eventos
        received_events = []
        for _ in range(3):
            message = websocket.receive_json(timeout=2.0)
            assert message["type"] == "event"
            received_events.append(message["data"])
        
        # Verifica que recebeu todos os eventos
        received_ids = [e["event_id"] for e in received_events]
        assert received_ids == event_ids


# ============================================================================
# Testes de Isolamento
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_isolation_different_tenants():
    """
    Testa isolamento entre diferentes tenants.
    
    **Cenário**:
    1. Conectar cliente do tenant A
    2. Conectar cliente do tenant B
    3. Enviar evento para tenant A
    4. Verificar que apenas A recebe, B não recebe
    """
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()
    
    token_a = generate_jwt_token(tenant_a_id)
    token_b = generate_jwt_token(tenant_b_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token_a}") as ws_a, \
         client.websocket_connect(f"/ws?token={token_b}") as ws_b:
        
        # Recebe mensagens de boas-vindas
        ws_a.receive_json()
        ws_b.receive_json()
        
        # Envia evento para tenant A
        event_data = {
            "event_id": str(uuid4()),
            "device_id": str(uuid4()),
            "event_type": "movement",
            "confidence": 0.92,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {}
        }
        
        await websocket_manager.broadcast_to_tenant(
            tenant_id=tenant_a_id,
            message={
                "type": "event",
                "data": event_data
            }
        )
        
        await asyncio.sleep(0.5)
        
        # Tenant A deve receber
        msg_a = ws_a.receive_json(timeout=2.0)
        assert msg_a["type"] == "event"
        assert msg_a["data"]["event_id"] == event_data["event_id"]
        
        # Tenant B NÃO deve receber
        received_b = []
        try:
            msg_b = ws_b.receive_json(timeout=1.0)
            received_b.append(msg_b)
        except:
            pass
        
        assert len(received_b) == 0, "Tenant B não deveria receber eventos de A"


# ============================================================================
# Testes de Heartbeat e Timeout
# ============================================================================

def test_websocket_heartbeat_ping_pong():
    """
    Testa mecanismo de heartbeat (ping/pong).
    
    **Cenário**:
    1. Conectar cliente
    2. Enviar ping
    3. Verificar que recebe pong
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Recebe mensagem de boas-vindas
        websocket.receive_json()
        
        # Envia ping
        websocket.send_text("ping")
        
        # Deve receber pong
        response = websocket.receive_json(timeout=2.0)
        
        assert response["type"] == "pong"
        assert "timestamp" in response


def test_websocket_multiple_heartbeats():
    """
    Testa múltiplos heartbeats sequenciais.
    
    **Cenário**:
    1. Conectar cliente
    2. Enviar 5 pings
    3. Verificar que recebe 5 pongs
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Recebe mensagem de boas-vindas
        websocket.receive_json()
        
        # Envia 5 pings
        for i in range(5):
            websocket.send_text("ping")
            
            # Deve receber pong
            response = websocket.receive_json(timeout=2.0)
            assert response["type"] == "pong"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_websocket_idle_timeout():
    """
    Testa que conexão idle é fechada após 5 minutos.
    
    **Cenário**:
    1. Conectar cliente
    2. Não enviar heartbeat por 5 minutos
    3. Verificar que conexão é fechada
    
    **Nota**: Este teste é marcado como 'slow' pois leva 5 minutos.
    Para testes rápidos, pode ser pulado.
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Recebe mensagem de boas-vindas
        websocket.receive_json()
        
        # Aguarda 5 minutos sem enviar heartbeat
        # (em produção, seria 300 segundos)
        # Para testes, podemos simular com timeout menor
        
        # Aguarda timeout (5 minutos = 300 segundos)
        await asyncio.sleep(301)
        
        # Conexão deve estar fechada
        with pytest.raises(Exception):
            websocket.send_text("ping")


# ============================================================================
# Testes de Conexão e Desconexão
# ============================================================================

def test_websocket_connection_count():
    """
    Testa contagem de conexões ativas.
    
    **Cenário**:
    1. Verificar contagem inicial
    2. Conectar 3 clientes
    3. Verificar que contagem aumentou
    4. Desconectar clientes
    5. Verificar que contagem voltou ao normal
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    # Contagem inicial
    initial_count = websocket_manager.get_connection_count(tenant_id)
    
    # Conecta 3 clientes
    with client.websocket_connect(f"/ws?token={token}") as ws1, \
         client.websocket_connect(f"/ws?token={token}") as ws2, \
         client.websocket_connect(f"/ws?token={token}") as ws3:
        
        # Recebe mensagens de boas-vindas
        ws1.receive_json()
        ws2.receive_json()
        ws3.receive_json()
        
        # Contagem deve ter aumentado em 3
        current_count = websocket_manager.get_connection_count(tenant_id)
        assert current_count == initial_count + 3
    
    # Após desconectar, contagem deve voltar ao normal
    final_count = websocket_manager.get_connection_count(tenant_id)
    assert final_count == initial_count


def test_websocket_disconnect_cleanup():
    """
    Testa que desconexão limpa recursos corretamente.
    
    **Cenário**:
    1. Conectar cliente
    2. Desconectar cliente
    3. Verificar que não há mais conexões para o tenant
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    # Conecta e desconecta
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.receive_json()
    
    # Não deve haver conexões ativas para este tenant
    count = websocket_manager.get_connection_count(tenant_id)
    assert count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
