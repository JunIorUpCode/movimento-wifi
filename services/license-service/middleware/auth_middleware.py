# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de autenticação e autorização
Valida JWT tokens e verifica permissões
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

# Security scheme para Bearer token
security = HTTPBearer()


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Middleware que requer autenticação JWT
    Valida token e extrai informações do tenant
    
    Args:
        request: Request HTTP
        credentials: Credenciais Bearer token
    
    Returns:
        Payload do JWT decodificado
    
    Raises:
        HTTPException: Se token inválido ou expirado
    
    Requisitos: 1.2, 19.2
    """
    token = credentials.credentials
    
    try:
        # Decodifica e valida token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Adiciona informações ao request state
        request.state.tenant_id = payload.get("sub")
        request.state.email = payload.get("email")
        request.state.role = payload.get("role")
        request.state.plan = payload.get("plan")
        
        logger.debug(
            "Token JWT validado",
            tenant_id=request.state.tenant_id,
            role=request.state.role
        )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token JWT inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def require_admin(
    payload: dict = Depends(require_auth)
) -> dict:
    """
    Middleware que requer role de admin
    Deve ser usado após require_auth
    
    Args:
        payload: Payload do JWT (injetado por require_auth)
    
    Returns:
        Payload do JWT
    
    Raises:
        HTTPException: Se usuário não for admin
    
    Requisitos: 1.2
    """
    role = payload.get("role")
    
    if role != "admin":
        logger.warning(
            "Acesso negado: role admin requerida",
            tenant_id=payload.get("sub"),
            role=role
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Permissão de administrador requerida."
        )
    
    logger.debug(
        "Acesso admin autorizado",
        tenant_id=payload.get("sub")
    )
    
    return payload
