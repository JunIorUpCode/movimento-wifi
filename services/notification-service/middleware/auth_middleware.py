# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de Autenticação
Valida JWT tokens e extrai informações do tenant
"""

from fastapi import Header, HTTPException, status
import jwt
from typing import Dict

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


async def require_tenant_auth(authorization: str = Header(...)) -> Dict[str, str]:
    """
    Middleware para validar JWT token e extrair tenant_id.
    
    **Autenticação**: Valida JWT token no header Authorization
    
    **Isolamento Multi-Tenant**: Extrai tenant_id do token
    
    Args:
        authorization: Header Authorization com formato "Bearer <token>"
    
    Returns:
        Dict com informações do tenant:
        {
            "tenant_id": str,
            "email": str,
            "role": str,
            "plan": str
        }
    
    Raises:
        HTTPException 401: Token inválido, expirado ou ausente
    """
    # Verifica formato do header
    if not authorization.startswith("Bearer "):
        logger.warning("Token sem prefixo Bearer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Use: Bearer <token>"
        )
    
    # Extrai token
    token = authorization.replace("Bearer ", "")
    
    try:
        # Decodifica e valida token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extrai informações
        tenant_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        plan = payload.get("plan")
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: tenant_id ausente"
            )
        
        logger.debug(
            "Token validado",
            tenant_id=tenant_id,
            role=role
        )
        
        return {
            "tenant_id": tenant_id,
            "email": email,
            "role": role,
            "plan": plan
        }
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def get_current_tenant(tenant_info: Dict[str, str] = require_tenant_auth) -> Dict[str, str]:
    """
    Dependency para obter informações do tenant autenticado.
    
    Alias para require_tenant_auth, usado em rotas que precisam do tenant.
    
    Args:
        tenant_info: Informações do tenant (injetado por require_tenant_auth)
    
    Returns:
        Dict com informações do tenant
    """
    return tenant_info
