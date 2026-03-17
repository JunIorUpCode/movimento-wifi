# -*- coding: utf-8 -*-
"""
Auth Middleware - Middleware de autenticação JWT
Valida tokens de tenants e dispositivos
"""

from fastapi import Header, HTTPException, status
import jwt

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


async def require_auth(authorization: str = Header(...)) -> dict:
    """
    Middleware que valida JWT token de tenant
    
    Args:
        authorization: Header Authorization com Bearer token
    
    Returns:
        Payload do token decodificado
    
    Raises:
        HTTPException: Se token inválido ou expirado
    
    Requisitos: 1.2, 13.8
    """
    if not authorization.startswith("Bearer "):
        logger.warning("Token sem prefixo Bearer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Valida que é token de tenant (não de dispositivo)
        if payload.get("type") == "device":
            logger.warning(
                "Tentativa de usar token de dispositivo em endpoint de tenant",
                device_id=payload.get("sub")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de dispositivo não permitido neste endpoint"
            )
        
        logger.debug(
            f"Token validado para tenant: {payload.get('tenant_id')}",
            tenant_id=payload.get("tenant_id")
        )
        
        return payload
    
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


async def require_device_auth(authorization: str = Header(...)) -> dict:
    """
    Middleware que valida JWT token de dispositivo
    
    Args:
        authorization: Header Authorization com Bearer token
    
    Returns:
        Payload do token decodificado
    
    Raises:
        HTTPException: Se token inválido ou expirado
    
    Requisitos: 8.8
    """
    if not authorization.startswith("Bearer "):
        logger.warning("Token sem prefixo Bearer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Valida que é token de dispositivo
        if payload.get("type") != "device":
            logger.warning(
                "Tentativa de usar token de tenant em endpoint de dispositivo",
                tenant_id=payload.get("tenant_id")
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de tenant não permitido neste endpoint"
            )
        
        # Adiciona device_id ao payload para facilitar acesso
        payload["device_id"] = payload.get("sub")
        
        logger.debug(
            f"Token de dispositivo validado: {payload.get('device_id')}",
            device_id=payload.get("device_id"),
            tenant_id=payload.get("tenant_id")
        )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token de dispositivo expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token de dispositivo inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
