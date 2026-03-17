# -*- coding: utf-8 -*-
"""
test_saas_pipeline.py — Testes End-to-End do pipeline SaaS WiFiSense.

Valida o fluxo completo: registro de tenant → licença → dispositivo →
autenticação → envio de dados → evento detectado → notificação.

Requisitos:
    - Todos os microserviços rodando (docker-compose up -d)
    - Variável E2E_BASE_URL apontando para o gateway (default: http://localhost)
    - pip install pytest httpx pytest-asyncio

Uso:
    pytest tests/e2e/ -v --tb=short
    E2E_BASE_URL=https://staging.wifisense.com pytest tests/e2e/ -v
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost").rstrip("/")
TIMEOUT = httpx.Timeout(30.0)

# IDs gerados para este run (isolamento entre execuções)
RUN_ID = uuid.uuid4().hex[:8]
TENANT_EMAIL = f"e2e-{RUN_ID}@test.wifisense.com"
TENANT_NAME  = f"E2E Tenant {RUN_ID}"
ADMIN_EMAIL  = f"admin-{RUN_ID}@wifisense.com"
ADMIN_PASSWORD = "E2eTestPwd!2026"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def tenant_data(client):
    """Cria tenant e retorna dados para os testes."""
    resp = client.post("/api/tenant/tenants", json={
        "name": TENANT_NAME,
        "email": TENANT_EMAIL,
        "plan": "trial",
    })
    assert resp.status_code in (200, 201), f"Criar tenant falhou: {resp.text}"
    return resp.json()


@pytest.fixture(scope="module")
def auth_token(client, tenant_data):
    """Registra usuário e retorna JWT."""
    tenant_id = tenant_data["id"]
    # Registra
    client.post("/api/auth/register", json={
        "tenant_id": tenant_id,
        "email": ADMIN_EMAIL,
        "name": "Admin E2E",
        "password": ADMIN_PASSWORD,
    })
    # Login
    resp = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    })
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def license_key(client, tenant_data, auth_token):
    """Gera licença para o tenant."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/license/licenses", json={
        "tenant_id": tenant_data["id"],
        "plan": "basic",
        "max_devices": 3,
    }, headers=headers)
    assert resp.status_code in (200, 201), f"Criar licença falhou: {resp.text}"
    return resp.json()["key"]


@pytest.fixture(scope="module")
def device_token(client, license_key):
    """Registra dispositivo e retorna JWT do dispositivo."""
    resp = client.post("/api/device/devices/register", json={
        "activation_key": license_key,
        "device_name": f"E2E-Device-{RUN_ID}",
        "hardware_type": "raspberry_pi_4",
    })
    assert resp.status_code in (200, 201), f"Registrar dispositivo falhou: {resp.text}"
    return resp.json()["device_token"]


# ── Testes ────────────────────────────────────────────────────────────────────

class TestHealthChecks:
    """Valida que todos os serviços estão respondendo."""

    @pytest.mark.parametrize("path", [
        "/health",
        "/api/auth/health",
        "/api/tenant/health",
        "/api/device/health",
        "/api/license/health",
        "/api/event/health",
        "/api/notification/health",
        "/api/billing/health",
    ])
    def test_service_health(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} retornou {resp.status_code}"


class TestAuthFlow:
    """Testa o fluxo de autenticação."""

    def test_register_and_login(self, client, tenant_data):
        email = f"flow-{RUN_ID}@test.com"
        client.post("/api/auth/register", json={
            "tenant_id": tenant_data["id"],
            "email": email,
            "name": "Flow Test User",
            "password": "FlowTest@2026",
        })
        resp = client.post("/api/auth/login", json={"email": email, "password": "FlowTest@2026"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_wrong_password_rejected(self, client):
        resp = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
        assert resp.status_code in (400, 401, 422)

    def test_token_contains_tenant_id(self, client, auth_token, tenant_data):
        import base64, json as _json
        payload_b64 = auth_token.split(".")[1] + "=="
        payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
        assert payload.get("tenant_id") == tenant_data["id"]


class TestTenantFlow:
    """Testa isolamento e gerenciamento de tenants."""

    def test_tenant_created(self, tenant_data):
        assert tenant_data["id"]
        assert tenant_data["email"] == TENANT_EMAIL

    def test_tenant_uniqueness(self, client):
        resp1 = client.post("/api/tenant/tenants", json={"name": "T1", "email": f"unique1-{RUN_ID}@t.com"})
        resp2 = client.post("/api/tenant/tenants", json={"name": "T1", "email": f"unique1-{RUN_ID}@t.com"})
        assert resp1.status_code in (200, 201)
        assert resp2.status_code in (400, 409)

    def test_suspended_tenant_blocked(self, client, tenant_data, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Cria tenant extra para suspender
        resp = client.post("/api/tenant/tenants", json={"name": "ToSuspend", "email": f"suspend-{RUN_ID}@t.com"})
        if resp.status_code not in (200, 201):
            pytest.skip("Não foi possível criar tenant para teste de suspensão")
        tid = resp.json()["id"]
        client.post(f"/api/tenant/tenants/{tid}/suspend", headers=headers)
        # Tenta operação com tenant suspenso
        resp2 = client.get(f"/api/tenant/tenants/{tid}", headers=headers)
        # Suspenso deve retornar 403 ou conter status suspenso
        if resp2.status_code == 200:
            assert resp2.json().get("status") == "suspended"
        else:
            assert resp2.status_code in (403, 404)


class TestDeviceAndEventPipeline:
    """Testa o pipeline completo: dispositivo → dados → evento."""

    def test_device_registered(self, device_token):
        assert device_token
        assert len(device_token) > 20

    def test_send_signal_data(self, client, device_token, tenant_data):
        headers = {"Authorization": f"Bearer {device_token}"}
        payload = {
            "tenant_id": tenant_data["id"],
            "rssi": -65.5,
            "timestamp": time.time(),
            "features": {
                "signal_energy": 12.3,
                "variance": 1.5,
                "rate_of_change": 2.1,
                "instability_score": 0.3,
            },
        }
        resp = client.post("/api/event/data", json=payload, headers=headers)
        assert resp.status_code in (200, 201, 202), f"Envio de dados falhou: {resp.text}"

    def test_unauthenticated_data_rejected(self, client, tenant_data):
        resp = client.post("/api/event/data", json={"tenant_id": tenant_data["id"], "rssi": -70})
        assert resp.status_code in (401, 403, 422)

    def test_events_list(self, client, auth_token, tenant_data):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get(f"/api/event/events?tenant_id={tenant_data['id']}", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), (list, dict))

    def test_device_heartbeat(self, client, device_token):
        headers = {"Authorization": f"Bearer {device_token}"}
        resp = client.post("/api/device/heartbeat", json={
            "cpu_usage": 12.5,
            "memory_usage": 35.0,
            "disk_usage": 18.0,
        }, headers=headers)
        assert resp.status_code in (200, 204)


class TestAnalyticsEndpoints:
    """Valida os endpoints de analytics."""

    def test_events_summary(self, client, auth_token, tenant_data):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get(
            f"/api/event/analytics/events/summary?tenant_id={tenant_data['id']}&days=7",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_events" in data

    def test_daily_events(self, client, auth_token, tenant_data):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get(
            f"/api/event/analytics/events/daily?tenant_id={tenant_data['id']}&days=7",
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 7


class TestBillingFlow:
    """Testa fluxo básico de faturamento."""

    def test_list_invoices(self, client, auth_token, tenant_data):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get(f"/api/billing/invoices?tenant_id={tenant_data['id']}", headers=headers)
        assert resp.status_code == 200
