# -*- coding: utf-8 -*-
"""
Auth Routes - Endpoints de autenticação
Implementa registro, login, refresh e logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from models.user import PlanType
from services.auth_service import auth_service
from services.jwt_service import jwt_service
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Inicializa database manager para auth_schema
db_manager = DatabaseManager("auth_schema")


# Schemas Pydantic para request/response
class RegisterRequest(BaseModel):
    """Schema para requisição de registro"""
    email: EmailStr = Field(..., description="Email do tenant")
    password: str = Field(..., min_length=8, description="Senha (mínimo 8 caracteres)")
    name: str = Field(..., min_length=3, description="Nome do tenant")
    plan_type: PlanType = Field(default=PlanType.BASIC, description="Tipo de plano")


class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    email: EmailStr = Field(..., description="Email do tenant")
    password: str = Field(..., description="Senha")


class AuthResponse(BaseModel):
    """Schema para resposta de autenticação"""
    access_token: str = Field(..., description="Token JWT de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token")
    tenant_id: str = Field(..., description="ID do tenant")
    email: str = Field(..., description="Email do tenant")
    plan: str = Field(..., description="Tipo de plano")


class MessageResponse(BaseModel):
    """Schema para resposta de mensagem simples"""
    message: str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Registra um novo tenant no sistema
    
    - Cria conta com período de trial de 7 dias
    - Hash de senha com bcrypt (12 rounds)
    - Retorna token JWT para acesso imediato
    
    Requisitos: 19.3
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        # Garante que auth_service está inicializado
        if auth_service.redis_client is None:
            await auth_service.initialize()
        
        # Registra tenant
        async with db_manager.get_session() as session:
            user = await auth_service.register_tenant(
                email=request.email,
                password=request.password,
                name=request.name,
                plan_type=request.plan_type,
                session=session
            )
        
        # Gera token JWT
        token = jwt_service.generate_jwt_token(
            tenant_id=str(user.id),
            email=user.email,
            role="tenant",
            plan=user.plan_type.value
        )
        
        return AuthResponse(
            access_token=token,
            tenant_id=str(user.id),
            email=user.email,
            plan=user.plan_type.value
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao registrar tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar registro"
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Autentica tenant e retorna token JWT
    
    - Valida credenciais (email/senha)
    - Verifica bloqueio de conta (5 falhas em 15 min = bloqueio de 30 min)
    - Retorna token JWT válido por 24 horas
    
    Requisitos: 19.3, 19.6, 19.7
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        # Garante que auth_service está inicializado
        if auth_service.redis_client is None:
            await auth_service.initialize()
        
        # Autentica usuário
        async with db_manager.get_session() as session:
            user, token = await auth_service.login(
                email=request.email,
                password=request.password,
                session=session
            )
        
        return AuthResponse(
            access_token=token,
            tenant_id=str(user.id),
            email=user.email,
            plan=user.plan_type.value
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao fazer login: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar login"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(authorization: Optional[str] = Header(None)):
    """
    Renova token JWT
    
    - Valida token atual
    - Gera novo token com expiração renovada (24 horas)
    
    Requisitos: 19.2
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    try:
        # Extrai token do header
        old_token = authorization.replace("Bearer ", "")
        
        # Garante que auth_service está inicializado
        if auth_service.redis_client is None:
            await auth_service.initialize()
        
        # Verifica se token está na blacklist
        if await auth_service.is_token_blacklisted(old_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidado. Faça login novamente."
            )
        
        # Gera novo token
        new_token = jwt_service.refresh_token(old_token)
        
        # Decodifica para obter informações
        payload = jwt_service.validate_jwt_token(new_token)
        
        return AuthResponse(
            access_token=new_token,
            tenant_id=payload["sub"],
            email=payload["email"],
            plan=payload["plan"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao renovar token: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao renovar token"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(authorization: Optional[str] = Header(None)):
    """
    Invalida token JWT (logout)
    
    - Adiciona token à blacklist no Redis
    - Token permanece inválido até expiração natural
    
    Requisitos: 19.2
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    try:
        # Extrai token do header
        token = authorization.replace("Bearer ", "")
        
        # Garante que auth_service está inicializado
        if auth_service.redis_client is None:
            await auth_service.initialize()
        
        # Invalida token
        await auth_service.logout(token)
        
        return MessageResponse(message="Logout realizado com sucesso")
    
    except Exception as e:
        logger.error(f"Erro ao fazer logout: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar logout"
        )
