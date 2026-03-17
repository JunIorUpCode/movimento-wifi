# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de Autenticação JWT
Valida tokens JWT e extrai tenant_id
"""

from fastapi import Request, HTTPException, status
from typing import Dict
import jwt

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


async def require_auth(request: Request) -> Dict:
    """
    Middleware de autenticação JWT
    
    Valida o token JWT no header Authorization e extrai o tenant_id.
    
    Args:
        request: Request do FastAPI
    
    Returns:
        Dict com payload do JWT (tenant_id, email, role, plan)
    
    Raises:
        HTTPException: Se token inválido ou ausente
    
    Requisito: 1.2, 19.2
    """
    # Extrai token do header Authorization
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        logger.warning("Token JWT ausente ou formato inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente ou inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        # Decodifica e valida token JWT
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Valida campos obrigatórios
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: tenant_id ausente"
            )
        
        # Armazena tenant_id no request state
        request.state.tenant_id = payload["sub"]
        request.state.email = payload.get("email")
        request.state.role = payload.get("role", "tenant")
        request.state.plan = payload.get("plan", "basic")
        
        logger.info(
            f"Autenticação bem-sucedida para tenant {payload['sub']}",
            tenant_id=payload["sub"],
            role=payload.get("role")
        )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token JWT inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
