# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de autenticação e autorização
Valida tokens JWT e extrai informações do tenant
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

from services.jwt_service import jwt_service
from services.auth_service import auth_service
from shared.logging import get_logger

logger = get_logger(__name__)

# Security scheme para Swagger UI
security = HTTPBearer()


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Middleware que valida JWT e extrai tenant_id
    
    - Valida token JWT
    - Verifica se token está na blacklist
    - Extrai tenant_id, role e plan
    - Adiciona informações ao request.state
    
    Args:
        request: Requisição HTTP
        credentials: Credenciais do header Authorization
    
    Returns:
        Payload do token JWT
    
    Raises:
        HTTPException 401: Se token inválido ou expirado
    
    Requisitos: 1.2, 19.2
    """
    try:
        token = credentials.credentials
        
        # Garante que auth_service está inicializado
        if auth_service.redis_client is None:
            await auth_service.initialize()
        
        # Verifica se token está na blacklist (logout)
        if await auth_service.is_token_blacklisted(token):
            logger.warning("Tentativa de uso de token invalidado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidado. Faça login novamente."
            )
        
        # Valida e decodifica token
        payload = jwt_service.validate_jwt_token(token)
        
        # Adiciona informações ao request state para uso posterior
        request.state.tenant_id = payload["sub"]
        request.state.email = payload["email"]
        request.state.role = payload["role"]
        request.state.plan = payload["plan"]
        
        logger.debug(
            "Autenticação bem-sucedida",
            tenant_id=payload["sub"],
            email=payload["email"],
            role=payload["role"]
        )
        
        return payload
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na autenticação: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falha na autenticação"
        )


async def require_admin(
    request: Request,
    payload: Dict[str, Any] = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Middleware que requer papel de administrador
    
    - Valida autenticação (via require_auth)
    - Verifica se role é "admin"
    
    Args:
        request: Requisição HTTP
        payload: Payload do token (de require_auth)
    
    Returns:
        Payload do token JWT
    
    Raises:
        HTTPException 403: Se não for admin
    
    Requisitos: 1.2
    """
    if payload.get("role") != "admin":
        logger.warning(
            f"Acesso negado: tenant {payload.get('sub')} tentou acessar endpoint admin",
            tenant_id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role")
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    
    return payload
