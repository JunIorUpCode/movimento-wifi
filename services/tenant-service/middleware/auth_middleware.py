# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de autenticação e autorização
Valida tokens JWT e verifica permissões de admin
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
import jwt

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

# Security scheme para Swagger UI
security = HTTPBearer()


def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Valida e decodifica token JWT
    
    Args:
        token: Token JWT
    
    Returns:
        Payload do token
    
    Raises:
        HTTPException: Se token inválido ou expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Middleware que requer papel de administrador
    
    - Valida token JWT
    - Verifica se role é "admin"
    - Adiciona informações ao request.state
    
    Args:
        request: Requisição HTTP
        credentials: Credenciais do header Authorization
    
    Returns:
        Payload do token JWT
    
    Raises:
        HTTPException 401: Se token inválido
        HTTPException 403: Se não for admin
    
    Requisitos: 1.2, 2.2
    """
    try:
        token = credentials.credentials
        
        # Valida e decodifica token
        payload = validate_jwt_token(token)
        
        # Verifica se é admin
        if payload.get("role") != "admin":
            logger.warning(
                f"Acesso negado: usuário {payload.get('sub')} tentou acessar endpoint admin",
                user_id=payload.get("sub"),
                email=payload.get("email"),
                role=payload.get("role")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso restrito a administradores"
            )
        
        # Adiciona informações ao request state
        request.state.admin_id = payload["sub"]
        request.state.email = payload["email"]
        request.state.role = payload["role"]
        
        logger.debug(
            "Autenticação admin bem-sucedida",
            admin_id=payload["sub"],
            email=payload["email"]
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
