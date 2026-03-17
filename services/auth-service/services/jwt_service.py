# -*- coding: utf-8 -*-
"""
JWT Service - Serviço de geração e validação de tokens JWT
Implementa autenticação baseada em JWT com tenant_id, role e plan no payload
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class JWTService:
    """
    Serviço para gerenciar tokens JWT
    Gera e valida tokens com informações do tenant
    """
    
    def __init__(self):
        """Inicializa o serviço JWT com configurações"""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS
    
    def generate_jwt_token(
        self,
        tenant_id: str,
        email: str,
        role: str,
        plan: str
    ) -> str:
        """
        Gera um token JWT com informações do tenant
        
        Args:
            tenant_id: ID único do tenant
            email: Email do tenant
            role: Papel do usuário (tenant ou admin)
            plan: Tipo de plano (basic ou premium)
        
        Returns:
            Token JWT assinado como string
        
        Requisitos: 1.2, 19.2
        """
        # Calcula timestamp de expiração (24 horas)
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.expiration_hours)
        
        # Monta payload do token
        payload = {
            "sub": tenant_id,  # Subject: ID do tenant
            "email": email,
            "role": role,
            "plan": plan,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expires_at.timestamp())  # Expiration
        }
        
        # Gera token assinado
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(
            "Token JWT gerado com sucesso",
            tenant_id=tenant_id,
            email=email,
            role=role,
            plan=plan,
            expires_at=expires_at.isoformat()
        )
        
        return token
    
    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Valida e decodifica um token JWT
        
        Args:
            token: Token JWT a ser validado
        
        Returns:
            Payload decodificado do token
        
        Raises:
            HTTPException: Se token for inválido ou expirado
        
        Requisitos: 1.2, 19.2
        """
        try:
            # Decodifica e valida o token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            logger.debug(
                "Token JWT validado com sucesso",
                tenant_id=payload.get("sub"),
                email=payload.get("email")
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expirado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Faça login novamente."
            )
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT inválido: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido. Faça login novamente."
            )
    
    def refresh_token(self, old_token: str) -> str:
        """
        Gera um novo token a partir de um token válido
        
        Args:
            old_token: Token JWT atual
        
        Returns:
            Novo token JWT com expiração renovada
        
        Raises:
            HTTPException: Se token for inválido
        """
        # Valida token atual
        payload = self.validate_jwt_token(old_token)
        
        # Gera novo token com mesmas informações
        new_token = self.generate_jwt_token(
            tenant_id=payload["sub"],
            email=payload["email"],
            role=payload["role"],
            plan=payload["plan"]
        )
        
        logger.info(
            "Token JWT renovado com sucesso",
            tenant_id=payload["sub"],
            email=payload["email"]
        )
        
        return new_token


# Instância global do serviço JWT
jwt_service = JWTService()
