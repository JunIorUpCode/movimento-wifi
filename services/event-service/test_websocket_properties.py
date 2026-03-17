# -*- coding: utf-8 -*-
"""
Testes de Propriedade para WebSocket
Task 17.3: Escrever teste de propriedade para WebSocket Channel Isolation
Property 4: WebSocket Channel Isolation
Requisitos: 1.5
"""

import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4, UUID

import jwt
import pytest
from hypothesis import given, settings, strategies as st
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from main import app
from shared.config import settings as app_settings
from shared.websocket import websocket_manager


# ============================================================================
# Helpers
# ============================================================================

def generate_jwt_token(tenant_id: UUID, role: str = "tenant") -> str:
    """
    Gera um token JWT para testes.
    
    Args:
        tenant_id: ID do tenant
        role: Role do usuário (tenant ou admin)
    
    Returns:
        Token JWT válido
    """
    payload = {
        "sub": str(tenant_id),
        "email": f"tenant-{tenant_id}@example.com",
        "role": role,
        "plan": "premium",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        app_settings.JWT_SECRET_KEY,
        algorithm=app_settings.JWT_ALGORITHM
    )
    
    return token


# ============================================================================
# Property 4: WebSocket Channel Isolation
# ============================================================================

@pytest.mark.asyncio
@given(
    tenant_a_id=st.uuids(),
    tenant_b_id=st.uuids()
)
@settings(max_examples=50, deadline=10000)
async def test_property_websocket_channel_isolation(tenant_a_id: UUID, tenant_b_id: UUID):
    """
    Property 4: WebSocket Channel Isolation
    
    **Propriedade**: Para quaisquer dois tenants diferentes A e B,
    quando um evento é enviado para o canal do tenant A, apenas
    clientes conectados ao canal de A devem receber o evento.
    Clientes do tenant B não devem receber o evento.
    
    **Valida**: Requisitos 1.5 (Isolamento multi-tenant)
    
    **Cenário**:
    1. Conectar cliente do tenant A
    2. Conectar cliente do tenant B
    3. Enviar evento para canal do tenant A
    4. Verificar que apenas cliente A recebe o evento
    5. Verificar que cliente B não recebe o evento
    
    **Importância**: Garante que dados de um tenant não vazam
    para outros tenants, fundamental para segurança e privacidade.
    
    Args:
        tenant_a_id: ID do tenant A (gerado por Hypothesis)
        tenant_b_id: ID do tenant B (gerado por Hypothesis)
    """
    # Garante que os tenants são diferentes
    if tenant_a_id == tenant_b_id:
        tenant_b_id = uuid4()
    
    # Gera tokens JWT para ambos os tenants
    token_a = generate_jwt_token(tenant_a_id)
    token_b = generate_jwt_token(tenant_b_id)
    
    # Cria cliente de teste
    client = TestClient(app)
    
    # Flags para rastrear mensagens recebidas
    tenant_a_received = []
    tenant_b_received = []
    
    # Conecta cliente do tenant A
    with client.websocket_connect(f"/ws?token={token_a}") as websocket_a:
        # Recebe mensagem de boas-vindas
        welcome_a = websocket_a.receive_json()
        assert welcome_a["type"] == "connected"
        assert welcome_a["tenant_id"] == str(tenant_a_id)
        assert welcome_a["channel"] == f"tenant:{tenant_a_id}"
        
        # Conecta cliente do tenant B
        with client.websocket_connect(f"/ws?token={token_b}") as websocket_b:
            # Recebe mensagem de boas-vindas
            welcome_b = websocket_b.receive_json()
            assert welcome_b["type"] == "connected"
            assert welcome_b["tenant_id"] == str(tenant_b_id)
            assert welcome_b["channel"] == f"tenant:{tenant_b_id}"
            
            # Cria evento para tenant A
            event_data = {
                "event_id": str(uuid4()),
                "device_id": str(uuid4()),
                "event_type": "presence",
                "confidence": 0.85,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {"test": "property_4"}
            }
            
            # Envia evento para canal do tenant A
            await websocket_manager.broadcast_to_tenant(
                tenant_id=tenant_a_id,
                message={
                    "type": "event",
                    "data": event_data
                }
            )
            
            # Aguarda um pouco para mensagens chegarem
            await asyncio.sleep(0.5)
            
            # Tenta receber mensagem no cliente A (deve receber)
            try:
                message_a = websocket_a.receive_json(timeout=1.0)
                tenant_a_received.append(message_a)
            except:
                pass
            
            # Tenta receber mensagem no cliente B (não deve receber)
            try:
                message_b = websocket_b.receive_json(timeout=1.0)
                tenant_b_received.append(message_b)
            except:
                pass
    
    # ========================================================================
    # Verificações da Propriedade
    # ========================================================================
    
    # 1. Cliente A deve ter recebido exatamente 1 mensagem (o evento)
    assert len(tenant_a_received) == 1, \
        f"Tenant A deveria receber 1 evento, mas recebeu {len(tenant_a_received)}"
    
    # 2. A mensagem recebida por A deve ser do tipo "event"
    assert tenant_a_received[0]["type"] == "event", \
        f"Mensagem recebida por A deveria ser 'event', mas foi '{tenant_a_received[0]['type']}'"
    
    # 3. O evento recebido por A deve ter os dados corretos
    assert tenant_a_received[0]["data"]["event_id"] == event_data["event_id"], \
        "Event ID não corresponde"
    
    # 4. Cliente B NÃO deve ter recebido nenhuma mensagem
    assert len(tenant_b_received) == 0, \
        f"Tenant B NÃO deveria receber eventos de A, mas recebeu {len(tenant_b_received)}"
    
    # ========================================================================
    # Propriedade Validada ✓
    # ========================================================================
    # Isolamento multi-tenant garantido: tenant A recebe seus eventos,
    # tenant B não recebe eventos de A


# ============================================================================
# Teste Adicional: Broadcast para Múltiplos Clientes do Mesmo Tenant
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_broadcast_multiple_clients_same_tenant():
    """
    Testa que múltiplos clientes do mesmo tenant recebem o mesmo evento.
    
    **Cenário**:
    1. Conectar 3 clientes do mesmo tenant
    2. Enviar evento para o canal do tenant
    3. Verificar que todos os 3 clientes recebem o evento
    """
    tenant_id = uuid4()
    token = generate_jwt_token(tenant_id)
    
    client = TestClient(app)
    
    # Conecta 3 clientes do mesmo tenant
    with client.websocket_connect(f"/ws?token={token}") as ws1, \
         client.websocket_connect(f"/ws?token={token}") as ws2, \
         client.websocket_connect(f"/ws?token={token}") as ws3:
        
        # Recebe mensagens de boas-vindas
        ws1.receive_json()
        ws2.receive_json()
        ws3.receive_json()
        
        # Cria evento
        event_data = {
            "event_id": str(uuid4()),
            "device_id": str(uuid4()),
            "event_type": "movement",
            "confidence": 0.92,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {}
        }
        
        # Envia evento para canal do tenant
        await websocket_manager.broadcast_to_tenant(
            tenant_id=tenant_id,
            message={
                "type": "event",
                "data": event_data
            }
        )
        
        # Aguarda mensagens
        await asyncio.sleep(0.5)
        
        # Todos os 3 clientes devem receber o evento
        msg1 = ws1.receive_json(timeout=1.0)
        msg2 = ws2.receive_json(timeout=1.0)
        msg3 = ws3.receive_json(timeout=1.0)
        
        # Verifica que todos receberam o mesmo evento
        assert msg1["type"] == "event"
        assert msg2["type"] == "event"
        assert msg3["type"] == "event"
        
        assert msg1["data"]["event_id"] == event_data["event_id"]
        assert msg2["data"]["event_id"] == event_data["event_id"]
        assert msg3["data"]["event_id"] == event_data["event_id"]


# ============================================================================
# Teste: Isolamento com Múltiplos Tenants e Múltiplos Clientes
# ============================================================================

@pytest.mark.asyncio
async def test_websocket_isolation_multiple_tenants_multiple_clients():
    """
    Testa isolamento com cenário complexo:
    - Tenant A com 2 clientes
    - Tenant B com 2 clientes
    - Enviar evento para A
    - Verificar que apenas clientes de A recebem
    """
    tenant_a_id = uuid4()
    tenant_b_id = uuid4()
    
    token_a = generate_jwt_token(tenant_a_id)
    token_b = generate_jwt_token(tenant_b_id)
    
    client = TestClient(app)
    
    # Conecta 2 clientes de cada tenant
    with client.websocket_connect(f"/ws?token={token_a}") as ws_a1, \
         client.websocket_connect(f"/ws?token={token_a}") as ws_a2, \
         client.websocket_connect(f"/ws?token={token_b}") as ws_b1, \
         client.websocket_connect(f"/ws?token={token_b}") as ws_b2:
        
        # Recebe mensagens de boas-vindas
        ws_a1.receive_json()
        ws_a2.receive_json()
        ws_b1.receive_json()
        ws_b2.receive_json()
        
        # Cria evento para tenant A
        event_data = {
            "event_id": str(uuid4()),
            "device_id": str(uuid4()),
            "event_type": "fall_suspected",
            "confidence": 0.88,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"severity": "high"}
        }
        
        # Envia evento para canal do tenant A
        await websocket_manager.broadcast_to_tenant(
            tenant_id=tenant_a_id,
            message={
                "type": "event",
                "data": event_data
            }
        )
        
        # Aguarda mensagens
        await asyncio.sleep(0.5)
        
        # Clientes de A devem receber
        msg_a1 = ws_a1.receive_json(timeout=1.0)
        msg_a2 = ws_a2.receive_json(timeout=1.0)
        
        assert msg_a1["type"] == "event"
        assert msg_a2["type"] == "event"
        assert msg_a1["data"]["event_id"] == event_data["event_id"]
        assert msg_a2["data"]["event_id"] == event_data["event_id"]
        
        # Clientes de B NÃO devem receber
        received_b1 = []
        received_b2 = []
        
        try:
            msg_b1 = ws_b1.receive_json(timeout=1.0)
            received_b1.append(msg_b1)
        except:
            pass
        
        try:
            msg_b2 = ws_b2.receive_json(timeout=1.0)
            received_b2.append(msg_b2)
        except:
            pass
        
        assert len(received_b1) == 0, "Cliente B1 não deveria receber eventos de A"
        assert len(received_b2) == 0, "Cliente B2 não deveria receber eventos de A"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
