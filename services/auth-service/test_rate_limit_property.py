# -*- coding: utf-8 -*-
"""
Testes de Propriedade para Rate Limiter — Property 29: Rate Limit Enforcement

Valida que o rate limiter bloqueia após 100 requisições por minuto por tenant.

Implementa Tarefa 2.7 | Requisitos: 19.4, 34.1-34.4
"""

import sys
import os

# Adiciona diretório raiz ao PYTHONPATH (shared/, services/)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
service_dir = os.path.abspath(os.path.dirname(__file__))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

import asyncio
import pytest
from unittest.mock import AsyncMock
from hypothesis import given, strategies as st
from hypothesis import settings as h_settings


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_limiter(counter_start: int = 0):
    """Cria RateLimiter com Redis mockado. Retorna (limiter, counter_dict)."""
    from services.rate_limiter import RateLimiter

    limiter = RateLimiter()
    counter = {"v": counter_start}

    async def _incr(key: str) -> int:
        counter["v"] += 1
        return counter["v"]

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(side_effect=_incr)
    mock_redis.expire = AsyncMock()
    limiter.redis_client = mock_redis
    return limiter, counter


def _run(coro):
    """Executa coroutine em loop limpo — compatível com Hypothesis sync tests."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── testes de propriedade (Hypothesis) ──────────────────────────────────────

class TestRateLimitProperties:
    """Property 29 — Testes de propriedade para RateLimiter."""

    # --- Property 29a: primeiras N requisições (N <= 100) são sempre permitidas ---

    @given(n=st.integers(min_value=1, max_value=100))
    @h_settings(max_examples=50)
    def test_property_first_n_requests_always_allowed(self, n: int):
        """
        Property 29a: As primeiras N requisições (1 ≤ N ≤ 100) são sempre permitidas.

        Valida Requisito 19.4.
        """
        async def _inner():
            limiter, _ = _make_limiter()
            for i in range(n):
                allowed, limit, remaining = await limiter.check_rate_limit(
                    "tenant-prop-a", "/api/endpoint"
                )
                assert allowed is True, f"Requisição {i + 1} deveria ser permitida"
                assert limit == 100
                assert remaining == max(0, 100 - (i + 1))

        _run(_inner())

    # --- Property 29b: qualquer requisição após a 100ª é bloqueada ---

    @given(extra=st.integers(min_value=1, max_value=20))
    @h_settings(max_examples=30)
    def test_property_requests_after_limit_are_blocked(self, extra: int):
        """
        Property 29b: Qualquer requisição após a 100ª é bloqueada (allowed=False).

        Valida Requisito 19.4.
        """
        async def _inner():
            limiter, _ = _make_limiter()

            # Consome as 100 requisições permitidas
            for _ in range(100):
                await limiter.check_rate_limit("tenant-prop-b", "/api")

            # As próximas devem ser bloqueadas
            for _ in range(extra):
                allowed, limit, remaining = await limiter.check_rate_limit(
                    "tenant-prop-b", "/api"
                )
                assert allowed is False, "Requisição após limite deveria ser bloqueada"
                assert remaining == 0
                assert limit == 100

        _run(_inner())

    # --- Property 29c: limites de tenants distintos são independentes ---

    @given(
        tenant_a=st.uuids().map(str),
        tenant_b=st.uuids().map(str),
    )
    @h_settings(max_examples=20)
    def test_property_different_tenants_are_independent(
        self, tenant_a: str, tenant_b: str
    ):
        """
        Property 29c: Rate limits de tenant_A e tenant_B são completamente
        independentes — esgotar A não afeta B.
        """
        if tenant_a == tenant_b:
            return  # ignora caso degenerado

        async def _inner():
            from services.rate_limiter import RateLimiter

            limiter = RateLimiter()
            counters: dict = {}

            async def _incr(key: str) -> int:
                counters[key] = counters.get(key, 0) + 1
                return counters[key]

            mock_redis = AsyncMock()
            mock_redis.incr = AsyncMock(side_effect=_incr)
            mock_redis.expire = AsyncMock()
            limiter.redis_client = mock_redis

            endpoint = "/api/events"

            # Esgota limite de tenant_a
            for _ in range(100):
                await limiter.check_rate_limit(tenant_a, endpoint)

            # tenant_a deve estar bloqueado
            allowed_a, _, _ = await limiter.check_rate_limit(tenant_a, endpoint)
            assert allowed_a is False, "Tenant A deveria estar bloqueado"

            # tenant_b ainda tem contadores próprios — deve estar permitido
            allowed_b, _, remaining_b = await limiter.check_rate_limit(
                tenant_b, endpoint
            )
            assert allowed_b is True, "Tenant B deve ter limite independente"
            assert remaining_b == 99

        _run(_inner())


# ─── testes unitários diretos ─────────────────────────────────────────────────

class TestRateLimitUnit:
    """Testes unitários do RateLimiter sem Hypothesis."""

    def test_window_is_60_seconds(self):
        """Janela de tempo é sempre 60 segundos (Requisito 34.3)."""
        from services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert limiter.window_seconds == 60

    def test_limit_is_100_requests_per_minute(self):
        """Limite é sempre 100 requisições por minuto (Requisito 19.4)."""
        from services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert limiter.requests_per_minute == 100

    @pytest.mark.asyncio
    async def test_101st_request_is_blocked(self):
        """Exatamente a 101ª requisição é bloqueada — teste de fronteira."""
        limiter, _ = _make_limiter()

        for _ in range(100):
            allowed, _, _ = await limiter.check_rate_limit("tenant-boundary", "/api")
            assert allowed is True

        allowed, _, remaining = await limiter.check_rate_limit(
            "tenant-boundary", "/api"
        )
        assert allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_returns_correct_tuple_types(self):
        """check_rate_limit retorna tupla (bool, int, int)."""
        limiter, _ = _make_limiter()

        result = await limiter.check_rate_limit("tenant-types", "/api/test")
        allowed, limit, remaining = result

        assert isinstance(allowed, bool)
        assert isinstance(limit, int)
        assert isinstance(remaining, int)
        assert limit == 100
        assert 0 <= remaining <= 100

    @pytest.mark.asyncio
    async def test_redis_key_contains_tenant_and_endpoint(self):
        """A chave Redis contém tanto o tenant_id quanto o endpoint."""
        from services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        keys_used: list[str] = []

        async def _incr(key: str) -> int:
            keys_used.append(key)
            return 1

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(side_effect=_incr)
        mock_redis.expire = AsyncMock()
        limiter.redis_client = mock_redis

        tenant_id = "tenant-redis-key-test"
        endpoint = "/api/health"

        await limiter.check_rate_limit(tenant_id, endpoint)

        assert len(keys_used) == 1
        key = keys_used[0]
        assert tenant_id in key
        assert endpoint in key

    @pytest.mark.asyncio
    async def test_remaining_decrements_with_each_request(self):
        """O campo 'remaining' diminui em 1 a cada requisição."""
        limiter, _ = _make_limiter()

        prev_remaining = 100
        for i in range(10):
            _, _, remaining = await limiter.check_rate_limit(
                "tenant-decrement", "/api"
            )
            assert remaining == prev_remaining - 1
            prev_remaining = remaining

    @pytest.mark.asyncio
    async def test_first_request_sets_redis_ttl(self):
        """Na primeira requisição, deve chamar redis.expire com 60 segundos."""
        from services.rate_limiter import RateLimiter

        limiter = RateLimiter()
        expire_calls: list = []

        async def _incr(key: str) -> int:
            return 1  # primeira requisição

        async def _expire(key: str, ttl: int):
            expire_calls.append((key, ttl))

        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(side_effect=_incr)
        mock_redis.expire = AsyncMock(side_effect=_expire)
        limiter.redis_client = mock_redis

        await limiter.check_rate_limit("tenant-ttl", "/api")

        assert len(expire_calls) == 1
        _, ttl = expire_calls[0]
        assert ttl == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
