# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de Autenticação e Autorização
Valida JWT tokens de tenants e dispositivos
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Dict

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)

# Security scheme para Bearer token
security = HTTPBearer()


def require_tenant_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Valida JWT token de tenant.
    
    Extrai e valida o token JWT do header Authorization.
    Verifica que o token é válido e contém role='tenant' ou 'admin'.
    
    Args:
        credentials: Credenciais HTTP Bearer (injetado)
    
    Returns:
        Dict com payload do token (tenant_id, email, role, plan)
    
    Raises:
        HTTPException 401: Token inválido, expirado ou ausente
        HTTPException 403: Token não é de tenant/admin
    """
    token = credentials.credentials
    
    try:
        # Decodifica e valida token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verifica role
        role = payload.get("role")
        if role not in ["tenant", "admin"]:
            logger.warning(
                "Token com role inválida",
                role=role,
                tenant_id=payload.get("sub")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: role inválida"
            )
        
        logger.debug(
            "Token de tenant validado",
            tenant_id=payload.get("sub"),
            role=role
        )
        
        return {
            "tenant_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": role,
            "plan": payload.get("plan")
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Token inválido", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


def require_device_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    Valida JWT token de dispositivo.
    
    Extrai e valida o token JWT do header Authorization.
    Verifica que o token é válido e contém role='device'.
    
    Args:
        credentials: Credenciais HTTP Bearer (injetado)
    
    Returns:
        Dict com payload do token (device_id, tenant_id, plan_type)
    
    Raises:
        HTTPException 401: Token inválido, expirado ou ausente
        HTTPException 403: Token não é de dispositivo
    """
    token = credentials.credentials
    
    try:
        # Decodifica e valida token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verifica role
        role = payload.get("role")
        if role != "device":
            logger.warning(
                "Token com role inválida para dispositivo",
                role=role,
                device_id=payload.get("device_id")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: token não é de dispositivo"
            )
        
        logger.debug(
            "Token de dispositivo validado",
            device_id=payload.get("device_id"),
            tenant_id=payload.get("tenant_id")
        )
        
        return {
            "device_id": payload.get("device_id"),
            "tenant_id": payload.get("tenant_id"),
            "plan_type": payload.get("plan_type")
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token de dispositivo expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Token de dispositivo inválido", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


# Aliases para facilitar uso
get_current_tenant = require_tenant_auth
get_current_device = require_device_auth
