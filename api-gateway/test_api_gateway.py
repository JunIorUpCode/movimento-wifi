#!/usr/bin/env python3
"""
============================================================================
WiFiSense SaaS - API Gateway Integration Tests
============================================================================
Testes de integração para o API Gateway (Nginx).

Testa:
- Roteamento para microserviços
- Rate limiting
- CORS
- Health checks
- Headers de segurança

Requisitos: 1.1, 19.8, 22.1, 34.1-34.4, 36.1-36.3
============================================================================
"""

import asyncio
import time
from typing import Dict, List

import aiohttp
import pytest

# ============================================================================
# Configuração
# ============================================================================

# URL base do API Gateway
GATEWAY_URL = "http://localhost"  # Ajustar conforme necessário

# Timeout para requisições
REQUEST_TIMEOUT = 10

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def http_session():
    """Cria uma sessão HTTP para os testes."""
    async with aiohttp.ClientSession() as session:
        yield session

# ============================================================================
# Testes de Health Check (Requisitos 36.1-36.3)
# ============================================================================

@pytest.mark.asyncio
async def test_health_check_simple(http_session):
    """
    Testa health check simples do gateway.
    
    Requisito: 36.1
    """
    async with http_session.get(f"{GATEWAY_URL}/health") as response:
        assert response.status == 200
        
        data = await response.json()
        assert "status" in data
        assert data["status"] in ["operational", "degraded", "outage"]
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_health_check_detailed(http_session):
    """
    Testa health check detalhado com status de todos os serviços.
    
    Requisitos: 36.2, 36.3
    """
    async with http_session.get(f"{GATEWAY_URL}/health/detailed") as response:
        # Status pode ser 200 (operational/degraded) ou 503 (outage)
        assert response.status in [200, 503]
        
        data = await response.json()
        assert "status" in data
        assert data["status"] in ["operational", "degraded", "outage"]
        assert "timestamp" in data
        assert "services" in data
        
        # Verificar que todos os serviços estão presentes
        services = {s["service_id"] for s in data["services"]}
        expected_services = {
            "auth", "tenant", "device", "license",
            "event", "notification", "billing"
        }
        assert services == expected_services
        
        # Verificar estrutura de cada serviço
        for service in data["services"]:
            assert "service_id" in service
            assert "name" in service
            assert "status" in service
            assert service["status"] in ["operational", "degraded", "outage"]
            assert "critical" in service
            assert isinstance(service["critical"], bool)

# ============================================================================
# Testes de Roteamento
# ============================================================================

@pytest.mark.asyncio
async def test_route_to_auth_service(http_session):
    """
    Testa roteamento para o auth-service.
    """
    # Tentar acessar endpoint de login (deve retornar 422 sem body)
    async with http_session.post(
        f"{GATEWAY_URL}/api/auth/login",
        json={}
    ) as response:
        # 422 = validação falhou (esperado sem credenciais)
        # 404 = rota não encontrada (problema no gateway)
        assert response.status != 404, "Rota não encontrada - problema no gateway"

@pytest.mark.asyncio
async def test_route_to_device_service(http_session):
    """
    Testa roteamento para o device-service.
    """
    # Tentar acessar endpoint de dispositivos (deve retornar 401 sem auth)
    async with http_session.get(f"{GATEWAY_URL}/api/devices") as response:
        # 401 = não autenticado (esperado)
        # 404 = rota não encontrada (problema no gateway)
        assert response.status != 404, "Rota não encontrada - problema no gateway"

@pytest.mark.asyncio
async def test_route_not_found(http_session):
    """
    Testa que rotas inexistentes retornam 404.
    """
    async with http_session.get(f"{GATEWAY_URL}/api/nonexistent") as response:
        assert response.status == 404
        
        data = await response.json()
        assert "error" in data

# ============================================================================
# Testes de Rate Limiting (Requisitos 34.1-34.4)
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiting_per_minute(http_session):
    """
    Testa rate limiting de 100 requisições por minuto.
    
    Requisitos: 34.1, 34.2
    """
    tenant_id = f"test-tenant-{int(time.time())}"
    
    # Enviar 101 requisições rapidamente
    tasks = []
    for i in range(101):
        task = http_session.get(
            f"{GATEWAY_URL}/health",
            headers={"X-Tenant-ID": tenant_id}
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Contar quantas requisições foram bloqueadas (429)
    status_codes = []
    for response in responses:
        if isinstance(response, Exception):
            continue
        status_codes.append(response.status)
        response.close()
    
    # Deve haver pelo menos uma requisição com status 429
    assert 429 in status_codes, "Rate limiting não está funcionando"
    
    # A maioria das requisições deve ter passado
    successful = status_codes.count(200)
    assert successful >= 90, f"Muitas requisições bloqueadas: {successful}/101"

@pytest.mark.asyncio
async def test_rate_limiting_headers(http_session):
    """
    Testa que headers X-RateLimit-* estão presentes.
    
    Requisitos: 34.3, 34.4
    """
    tenant_id = f"test-tenant-{int(time.time())}"
    
    async with http_session.get(
        f"{GATEWAY_URL}/health",
        headers={"X-Tenant-ID": tenant_id}
    ) as response:
        # Verificar headers de rate limit
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        
        # Verificar valores
        limit = int(response.headers["X-RateLimit-Limit"])
        assert limit > 0

@pytest.mark.asyncio
async def test_rate_limiting_isolation(http_session):
    """
    Testa que rate limiting é isolado por tenant.
    
    Requisito: 1.1
    """
    tenant_a = f"test-tenant-a-{int(time.time())}"
    tenant_b = f"test-tenant-b-{int(time.time())}"
    
    # Enviar 50 requisições para tenant A
    tasks_a = []
    for i in range(50):
        task = http_session.get(
            f"{GATEWAY_URL}/health",
            headers={"X-Tenant-ID": tenant_a}
        )
        tasks_a.append(task)
    
    responses_a = await asyncio.gather(*tasks_a)
    for response in responses_a:
        response.close()
    
    # Tenant B deve conseguir fazer requisições normalmente
    async with http_session.get(
        f"{GATEWAY_URL}/health",
        headers={"X-Tenant-ID": tenant_b}
    ) as response:
        assert response.status == 200, "Rate limiting não está isolado por tenant"

# ============================================================================
# Testes de CORS (Requisito 19.8)
# ============================================================================

@pytest.mark.asyncio
async def test_cors_preflight(http_session):
    """
    Testa que requisições OPTIONS (preflight) são respondidas corretamente.
    
    Requisito: 19.8
    """
    async with http_session.options(
        f"{GATEWAY_URL}/api/devices",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    ) as response:
        assert response.status == 204
        
        # Verificar headers CORS
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

@pytest.mark.asyncio
async def test_cors_headers_present(http_session):
    """
    Testa que headers CORS estão presentes em requisições normais.
    
    Requisito: 19.8
    """
    async with http_session.get(
        f"{GATEWAY_URL}/health",
        headers={"Origin": "http://localhost:3000"}
    ) as response:
        # Verificar headers CORS
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Credentials" in response.headers

# ============================================================================
# Testes de Segurança (Requisito 19.8)
# ============================================================================

@pytest.mark.asyncio
async def test_security_headers_present(http_session):
    """
    Testa que headers de segurança estão presentes.
    
    Requisito: 19.8
    """
    async with http_session.get(f"{GATEWAY_URL}/health") as response:
        headers = response.headers
        
        # Verificar headers de segurança obrigatórios
        assert "X-Frame-Options" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers
        assert "Content-Security-Policy" in headers
        
        # Verificar valores
        assert headers["X-Frame-Options"] == "SAMEORIGIN"
        assert headers["X-Content-Type-Options"] == "nosniff"

@pytest.mark.asyncio
async def test_server_version_hidden(http_session):
    """
    Testa que a versão do servidor está oculta.
    
    Requisito: 19.8
    """
    async with http_session.get(f"{GATEWAY_URL}/health") as response:
        # Server header não deve conter versão do Nginx
        server_header = response.headers.get("Server", "")
        assert "nginx/" not in server_header.lower()

# ============================================================================
# Testes de Timeout (Requisito 19.8)
# ============================================================================

@pytest.mark.asyncio
async def test_request_timeout(http_session):
    """
    Testa que requisições têm timeout de 30 segundos.
    
    Requisito: 19.8
    
    Nota: Este teste é difícil de executar sem um endpoint que demore 30s.
    Aqui apenas verificamos que a configuração está correta.
    """
    # Este teste seria executado com um endpoint mock que demora 30s+
    # Por enquanto, apenas verificamos que requisições normais funcionam
    start_time = time.time()
    
    async with http_session.get(f"{GATEWAY_URL}/health") as response:
        elapsed = time.time() - start_time
        
        # Requisição normal deve ser rápida (< 5s)
        assert elapsed < 5, "Requisição muito lenta"
        assert response.status == 200

# ============================================================================
# Testes de Load Balancing
# ============================================================================

@pytest.mark.asyncio
async def test_load_balancing_distribution(http_session):
    """
    Testa que requisições são distribuídas entre instâncias.
    
    Requisito: 22.1
    
    Nota: Este teste só funciona se houver múltiplas instâncias.
    """
    # Fazer múltiplas requisições e verificar upstream_addr nos logs
    # Por enquanto, apenas verificamos que o roteamento funciona
    
    responses = []
    for i in range(10):
        async with http_session.get(f"{GATEWAY_URL}/health") as response:
            assert response.status == 200
            responses.append(response.status)
    
    # Todas as requisições devem ter sucesso
    assert all(status == 200 for status in responses)

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
