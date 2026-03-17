# -*- coding: utf-8 -*-
"""
Tenant Routes - Endpoints de gerenciamento de tenants
Implementa CRUD, suspensão, ativação e listagem
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID

from models.tenant import PlanType, TenantStatus
from services.tenant_service import tenant_service
from middleware.auth_middleware import require_admin
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin/tenants", tags=["Tenant Management"])

# Database manager para tenant_schema
db_manager = DatabaseManager("tenant_schema")


# Schemas Pydantic para request/response
class CreateTenantRequest(BaseModel):
    """Schema para criação de tenant"""
    email: EmailStr = Field(..., description="Email do tenant")
    name: str = Field(..., min_length=3, description="Nome do tenant")
    plan_type: PlanType = Field(default=PlanType.BASIC, description="Tipo de plano")


class UpdateTenantRequest(BaseModel):
    """Schema para atualização de tenant"""
    name: Optional[str] = Field(None, min_length=3, description="Nome do tenant")
    plan_type: Optional[PlanType] = Field(None, description="Tipo de plano")
    language: Optional[str] = Field(None, description="Idioma preferido")
    metadata: Optional[dict] = Field(None, description="Metadados adicionais")


class TenantResponse(BaseModel):
    """Schema para resposta de tenant"""
    id: str
    email: str
    name: str
    plan_type: str
    status: str
    trial_ends_at: Optional[str]
    created_at: str
    updated_at: str
    language: str
    metadata: Optional[dict]


class TenantListResponse(BaseModel):
    """Schema para listagem de tenants"""
    tenants: List[TenantResponse]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Schema para resposta de mensagem simples"""
    message: str


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    _: dict = Depends(require_admin)
):
    """
    Cria um novo tenant (admin only)
    
    - Cria conta com período de trial de 7 dias
    - Email deve ser único
    - Retorna dados do tenant criado
    
    Requisitos: 2.2, 18.1
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        # Cria tenant
        async with db_manager.get_session() as session:
            tenant = await tenant_service.create_tenant(
                email=request.email,
                name=request.name,
                plan_type=request.plan_type,
                session=session
            )
            
            return TenantResponse(**tenant.to_dict())
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao criar tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar tenant"
        )


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    status_filter: Optional[TenantStatus] = Query(None, alias="status", description="Filtrar por status"),
    plan_filter: Optional[PlanType] = Query(None, alias="plan", description="Filtrar por plano"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    _: dict = Depends(require_admin)
):
    """
    Lista todos os tenants com filtros opcionais (admin only)
    
    - Suporta filtros por status e plano
    - Paginação com limit e offset
    - Retorna total de registros
    
    Requisitos: 2.3
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Busca tenants
            tenants = await tenant_service.list_tenants(
                session=session,
                status=status_filter,
                plan_type=plan_filter,
                limit=limit,
                offset=offset
            )
            
            # Conta total
            total = await tenant_service.count_tenants(
                session=session,
                status=status_filter,
                plan_type=plan_filter
            )
            
            return TenantListResponse(
                tenants=[TenantResponse(**t.to_dict()) for t in tenants],
                total=total,
                limit=limit,
                offset=offset
            )
    
    except Exception as e:
        logger.error(f"Erro ao listar tenants: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar tenants"
        )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    _: dict = Depends(require_admin)
):
    """
    Obtém detalhes de um tenant específico (admin only)
    
    Requisitos: 2.3
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            tenant = await tenant_service.get_tenant_by_id(tenant_id, session)
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant {tenant_id} não encontrado"
                )
            
            return TenantResponse(**tenant.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar tenant"
        )


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    request: UpdateTenantRequest,
    _: dict = Depends(require_admin)
):
    """
    Atualiza informações de um tenant (admin only)
    
    - Permite atualizar nome, plano, idioma e metadados
    - Campos não fornecidos não são alterados
    
    Requisitos: 2.3
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            tenant = await tenant_service.update_tenant(
                tenant_id=tenant_id,
                session=session,
                name=request.name,
                plan_type=request.plan_type,
                language=request.language,
                metadata=request.metadata
            )
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant {tenant_id} não encontrado"
                )
            
            return TenantResponse(**tenant.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar tenant"
        )


@router.delete("/{tenant_id}", response_model=MessageResponse)
async def delete_tenant(
    tenant_id: UUID,
    _: dict = Depends(require_admin)
):
    """
    Deleta um tenant permanentemente (admin only)
    
    ATENÇÃO: Esta operação é irreversível e deleta todos os dados
    relacionados (dispositivos, eventos, licenças, etc.)
    
    Requisitos: 2.6
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            deleted = await tenant_service.delete_tenant(tenant_id, session)
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant {tenant_id} não encontrado"
                )
            
            return MessageResponse(message=f"Tenant {tenant_id} deletado com sucesso")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao deletar tenant"
        )


@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
async def suspend_tenant(
    tenant_id: UUID,
    _: dict = Depends(require_admin)
):
    """
    Suspende um tenant (admin only)
    
    - Altera status para SUSPENDED
    - Bloqueia acesso a todas as APIs
    - Dispositivos param de enviar dados
    
    Requisitos: 2.4, 2.5
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            tenant = await tenant_service.suspend_tenant(tenant_id, session)
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant {tenant_id} não encontrado"
                )
            
            return TenantResponse(**tenant.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao suspender tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao suspender tenant"
        )


@router.post("/{tenant_id}/activate", response_model=TenantResponse)
async def activate_tenant(
    tenant_id: UUID,
    _: dict = Depends(require_admin)
):
    """
    Ativa um tenant suspenso (admin only)
    
    - Altera status para ACTIVE
    - Restaura acesso a todas as APIs
    - Dispositivos voltam a funcionar normalmente
    
    Requisitos: 2.4
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            tenant = await tenant_service.activate_tenant(tenant_id, session)
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant {tenant_id} não encontrado"
                )
            
            return TenantResponse(**tenant.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ativar tenant: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao ativar tenant"
        )
