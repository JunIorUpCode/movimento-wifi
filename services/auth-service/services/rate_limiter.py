# -*- coding: utf-8 -*-
"""
Rate Limiter - Middleware de limitação de taxa de requisições
Implementa rate limiting usando Redis com 100 req/min por tenant
"""

from typing import Optional
from datetime import datetime
import redis.asyncio as redis
from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Serviço de rate limiting baseado em Redis
    Limita requisições por tenant para prevenir abuso
    """
    
    def __init__(self):
        """Inicializa conexão com Redis"""
        self.redis_client: Optional[redis.Redis] = None
        self.requests_per_minute = 100  # Requisito 19.4
        self.window_seconds = 60
    
    async def initialize(self):
        """Conecta ao Redis"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("RateLimiter conectado ao Redis")
    
    async def close(self):
        """Fecha conexão com Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("RateLimiter desconectado do Redis")
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        endpoint: str
    ) -> tuple[bool, int, int]:
        """
        Verifica se tenant excedeu limite de requisições
        
        Args:
            tenant_id: ID do tenant
            endpoint: Endpoint sendo acessado
        
        Returns:
            Tupla (permitido, limite, restante)
        
        Requisitos: 19.4, 34.1-34.4
        """
        if not self.redis_client:
            await self.initialize()
        
        # Chave Redis: rate_limit:{tenant_id}:{endpoint}
        key = f"rate_limit:{tenant_id}:{endpoint}"
        
        # Incrementa contador
        current_count = await self.redis_client.incr(key)
        
        # Define TTL na primeira requisição
        if current_count == 1:
            await self.redis_client.expire(key, self.window_seconds)
        
        # Calcula requisições restantes
        remaining = max(0, self.requests_per_minute - current_count)
        
        # Verifica se excedeu limite
        allowed = current_count <= self.requests_per_minute
        
        if not allowed:
            logger.warning(
                f"Rate limit excedido para tenant {tenant_id}",
                tenant_id=tenant_id,
                endpoint=endpoint,
                current_count=current_count,
                limit=self.requests_per_minute
            )
        
        return allowed, self.requests_per_minute, remaining
    
    async def middleware(self, request: Request, call_next):
        """
        Middleware FastAPI para aplicar rate limiting
        
        Args:
            request: Requisição HTTP
            call_next: Próximo handler na cadeia
        
        Returns:
            Response com headers de rate limit
        
        Raises:
            HTTPException 429: Se limite excedido
        
        Requisitos: 19.4, 34.3, 34.4
        """
        # Extrai tenant_id do request state (definido pelo middleware de auth)
        tenant_id = getattr(request.state, "tenant_id", "anonymous")
        endpoint = request.url.path
        
        # Verifica rate limit
        allowed, limit, remaining = await self.check_rate_limit(tenant_id, endpoint)
        
        # Se excedeu limite, retorna HTTP 429
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Limite de requisições excedido. Tente novamente em 1 minuto."
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )
        
        # Processa requisição
        response = await call_next(request)
        
        # Adiciona headers de rate limit na resposta
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


# Instância global do rate limiter
rate_limiter = RateLimiter()
