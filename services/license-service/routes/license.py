# -*- coding: utf-8 -*-
"""
License Routes - Endpoints de gerenciamento de licenças
Implementa geração, validação, revogação e extensão de licenças
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from models.license import PlanType, LicenseStatus
from services.license_service import license_service
from services.license_generator import license_generator
from middleware.auth_middleware import require_admin, require_auth
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)

# Routers separados para admin e dispositivos
admin_router = APIRouter(prefix="/api/admin/licenses", tags=["License Management (Admin)"])
device_router = APIRouter(prefix="/api/licenses", tags=["License Validation (Device)"])

# Database manager para license_schema
db_manager = DatabaseManager("license_schema")


# Schemas Pydantic para request/response
class CreateLicenseRequest(BaseModel):
    """Schema para criação de licença"""
    tenant_id: str = Field(..., description="ID do tenant")
    plan_type: PlanType = Field(..., description="Tipo de plano")
    device_limit: int = Field(default=1, ge=1, le=100, description="Limite de dispositivos")
    expires_in_days: int = Field(default=365, ge=1, le=3650, description="Dias até expiração")


class ExtendLicenseRequest(BaseModel):
    """Schema para extensão de licença"""
    additional_days: int = Field(..., ge=1, le=3650, description="Dias adicionais")


class ValidateLicenseRequest(BaseModel):
    """Schema para validação de licença"""
    activation_key: str = Field(..., min_length=16, max_length=19, description="Chave de ativação")
    device_id: str = Field(..., description="ID do dispositivo")
    hardware_info: dict = Field(default={}, description="Informações do hardware")


class LicenseResponse(BaseModel):
    """Schema para resposta de licença"""
    id: str
    tenant_id: str
    plan_type: str
    device_limit: int
    expires_at: str
    activated_at: Optional[str]
    device_id: Optional[str]
    status: str
    created_at: str
    updated_at: str
    activation_key: Optional[str] = None  # Apenas para admin


class LicenseListResponse(BaseModel):
    """Schema para listagem de licenças"""
    licenses: List[LicenseResponse]
    total: int
    limit: int
    offset: int


class ValidateLicenseResponse(BaseModel):
    """Schema para resposta de validação"""
    valid: bool
    license_id: Optional[str] = None
    tenant_id: Optional[str] = None
    plan_type: Optional[str] = None
    device_limit: Optional[int] = None
    expires_at: Optional[str] = None
    message: str


class MessageResponse(BaseModel):
    """Schema para resposta de mensagem simples"""
    message: str


# ============================================================================
# ENDPOINTS ADMINISTRATIVOS (Admin Only)
# ============================================================================

@admin_router.post("", response_model=LicenseResponse, status_code=status.HTTP_201_CREATED)
async def create_license(
    request: CreateLicenseRequest,
    _: dict = Depends(require_admin)
):
    """
    Gera uma nova licença (admin only)
    
    - Gera chave de ativação criptograficamente segura
    - Define limite de dispositivos e data de expiração
    - Retorna licença com activation_key (mostrar apenas uma vez!)
    
    Requisitos: 4.1, 4.2
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        # Converte tenant_id para UUID
        try:
            tenant_uuid = UUID(request.tenant_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tenant_id inválido"
            )
        
        # Cria licença
        async with db_manager.get_session() as session:
            license = await license_service.create_license(
                tenant_id=tenant_uuid,
                plan_type=request.plan_type,
                device_limit=request.device_limit,
                expires_in_days=request.expires_in_days,
                session=session
            )
            
            # Retorna com activation_key (apenas para admin)
            return LicenseResponse(**license.to_dict(include_key=True))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar licença: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar licença"
        )


@admin_router.get("", response_model=LicenseListResponse)
async def list_licenses(
    tenant_id: Optional[str] = Query(None, description="Filtrar por tenant"),
    status_filter: Optional[LicenseStatus] = Query(None, alias="status", description="Filtrar por status"),
    plan_filter: Optional[PlanType] = Query(None, alias="plan", description="Filtrar por plano"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    _: dict = Depends(require_admin)
):
    """
    Lista todas as licenças com filtros opcionais (admin only)
    
    - Suporta filtros por tenant, status e plano
    - Paginação com limit e offset
    - Retorna total de registros
    
    Requisitos: 4.1
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        # Converte tenant_id para UUID se fornecido
        tenant_uuid = None
        if tenant_id:
            try:
                tenant_uuid = UUID(tenant_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="tenant_id inválido"
                )
        
        async with db_manager.get_session() as session:
            # Busca licenças
            licenses = await license_service.list_licenses(
                session=session,
                tenant_id=tenant_uuid,
                status=status_filter,
                plan_type=plan_filter,
                limit=limit,
                offset=offset
            )
            
            # Conta total
            total = await license_service.count_licenses(
                session=session,
                tenant_id=tenant_uuid,
                status=status_filter,
                plan_type=plan_filter
            )
            
            return LicenseListResponse(
                licenses=[LicenseResponse(**lic.to_dict(include_key=True)) for lic in licenses],
                total=total,
                limit=limit,
                offset=offset
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar licenças: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar licenças"
        )


@admin_router.get("/{license_id}", response_model=LicenseResponse)
async def get_license(
    license_id: UUID,
    _: dict = Depends(require_admin)
):
    """
    Obtém detalhes de uma licença específica (admin only)
    
    Requisitos: 4.1
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            license = await license_service.get_license_by_id(license_id, session)
            
            if not license:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Licença {license_id} não encontrada"
                )
            
            return LicenseResponse(**license.to_dict(include_key=True))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar licença: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar licença"
        )


@admin_router.put("/{license_id}/revoke", response_model=LicenseResponse)
async def revoke_license(
    license_id: UUID,
    _: dict = Depends(require_admin)
):
    """
    Revoga uma licença (admin only)
    
    - Altera status para REVOKED
    - Dispositivos associados serão desativados na próxima validação
    
    Requisitos: 4.7
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            license = await license_service.revoke_license(license_id, session)
            
            if not license:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Licença {license_id} não encontrada"
                )
            
            return LicenseResponse(**license.to_dict(include_key=True))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao revogar licença: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao revogar licença"
        )


@admin_router.put("/{license_id}/extend", response_model=LicenseResponse)
async def extend_license(
    license_id: UUID,
    request: ExtendLicenseRequest,
    _: dict = Depends(require_admin)
):
    """
    Estende a expiração de uma licença (admin only)
    
    - Adiciona dias à data de expiração
    - Se licença estava expirada, reativa
    
    Requisitos: 4.7
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            license = await license_service.extend_license(
                license_id,
                request.additional_days,
                session
            )
            
            if not license:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Licença {license_id} não encontrada"
                )
            
            return LicenseResponse(**license.to_dict(include_key=True))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao estender licença: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao estender licença"
        )


# ============================================================================
# ENDPOINTS DE DISPOSITIVOS (Device Authentication)
# ============================================================================

@device_router.post("/validate", response_model=ValidateLicenseResponse)
async def validate_license(
    request: ValidateLicenseRequest
):
    """
    Valida uma chave de ativação (dispositivo)
    
    - Verifica se chave é válida e não expirada
    - Retorna informações da licença se válida
    - Usado durante registro de dispositivo
    
    Requisitos: 4.1
    """
    try:
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        # Valida formato da chave
        if not license_generator.validate_key_format(request.activation_key):
            return ValidateLicenseResponse(
                valid=False,
                message="Formato de chave inválido"
            )
        
        async with db_manager.get_session() as session:
            # Busca licença
            license = await license_service.get_license_by_key(
                request.activation_key,
                session
            )
            
            if not license:
                return ValidateLicenseResponse(
                    valid=False,
                    message="Chave de ativação não encontrada"
                )
            
            # Verifica status
            if license.status == LicenseStatus.REVOKED:
                return ValidateLicenseResponse(
                    valid=False,
                    message="Licença revogada"
                )
            
            if license.status == LicenseStatus.EXPIRED:
                return ValidateLicenseResponse(
                    valid=False,
                    message="Licença expirada"
                )
            
            if license.status == LicenseStatus.ACTIVATED:
                return ValidateLicenseResponse(
                    valid=False,
                    message="Licença já ativada por outro dispositivo"
                )
            
            # Verifica expiração
            if license.expires_at < datetime.utcnow():
                license.status = LicenseStatus.EXPIRED
                await session.flush()
                return ValidateLicenseResponse(
                    valid=False,
                    message="Licença expirada"
                )
            
            # Licença válida
            return ValidateLicenseResponse(
                valid=True,
                license_id=str(license.id),
                tenant_id=str(license.tenant_id),
                plan_type=license.plan_type.value,
                device_limit=license.device_limit,
                expires_at=license.expires_at.isoformat(),
                message="Licença válida"
            )
    
    except Exception as e:
        logger.error(f"Erro ao validar licença: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao validar licença"
        )


# Combina routers
router = APIRouter()
router.include_router(admin_router)
router.include_router(device_router)


@device_router.post("/activate", response_model=MessageResponse)
async def activate_license(
    request: dict
):
    """
    Marca uma licença como ativada após registro de dispositivo
    
    - Atualiza status para ACTIVATED
    - Associa device_id à licença
    - Registra data de ativação
    
    Requisitos: 4.4
    """
    try:
        activation_key = request.get("activation_key")
        device_id_str = request.get("device_id")
        
        if not activation_key or not device_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="activation_key e device_id são obrigatórios"
            )
        
        # Converte device_id para UUID
        try:
            device_uuid = UUID(device_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="device_id inválido"
            )
        
        # Garante que database manager está inicializado
        if db_manager.engine is None:
            await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Busca licença
            license = await license_service.get_license_by_key(
                activation_key,
                session
            )
            
            if not license:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Licença não encontrada"
                )
            
            # Atualiza licença
            license.status = LicenseStatus.ACTIVATED
            license.device_id = device_uuid
            license.activated_at = datetime.utcnow()
            license.updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(
                f"Licença ativada com sucesso: {license.id}",
                license_id=str(license.id),
                device_id=str(device_uuid)
            )
            
            return MessageResponse(message="Licença ativada com sucesso")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ativar licença: {str(e)}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao ativar licença"
        )
