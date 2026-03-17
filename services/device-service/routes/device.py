# -*- coding: utf-8 -*-
"""
Device Routes - Endpoints da API de dispositivos
Implementa registro, gerenciamento e heartbeat de dispositivos
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

from services.device_service import DeviceService
from services.device_registration import DeviceRegistration
from services.device_heartbeat import DeviceHeartbeat
from middleware.auth_middleware import require_auth, require_device_auth
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/devices", tags=["devices"])

# Database manager
db_manager = DatabaseManager("device_schema")


# Schemas Pydantic
class DeviceRegisterRequest(BaseModel):
    """Request para registro de dispositivo"""
    activation_key: str = Field(..., description="Chave de ativação da licença")
    hardware_info: dict = Field(..., description="Informações do hardware")
    device_name: Optional[str] = Field(None, description="Nome do dispositivo")


class DeviceRegisterResponse(BaseModel):
    """Response do registro de dispositivo"""
    device_id: str
    jwt_token: str
    config: dict
    hardware_validation: dict


class DeviceUpdateRequest(BaseModel):
    """Request para atualização de dispositivo"""
    name: Optional[str] = Field(None, description="Novo nome do dispositivo")
    config: Optional[dict] = Field(None, description="Nova configuração")


class DeviceHeartbeatRequest(BaseModel):
    """Request para heartbeat de dispositivo"""
    health_metrics: Optional[dict] = Field(None, description="Métricas de saúde (CPU, memória, disco)")


class DeviceDataRequest(BaseModel):
    """Request para envio de dados de sinal do dispositivo"""
    features: dict = Field(..., description="Features processadas (RSSI ou CSI)")
    timestamp: float = Field(..., description="Timestamp da captura")
    data_type: str = Field(..., description="Tipo de dados: 'rssi' ou 'csi'")


class DeviceResponse(BaseModel):
    """Response com dados do dispositivo"""
    id: str
    tenant_id: str
    name: str
    hardware_type: str
    status: str
    last_seen: str
    registered_at: str
    hardware_info: dict
    config: dict
    created_at: str
    updated_at: str


class DeviceStatusResponse(BaseModel):
    """Response com status do dispositivo"""
    device_id: str
    name: str
    status: str
    last_seen: str
    seconds_since_last_seen: int
    hardware_type: str
    hardware_info: dict


# Endpoints

@router.post("/register", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_device(request: DeviceRegisterRequest):
    """
    Registra um novo dispositivo com activation_key
    
    Requisitos: 3.2, 3.3, 4.4
    """
    logger.info(
        f"Recebida requisição de registro de dispositivo",
        activation_key_prefix=request.activation_key[:4],
        hardware_type=request.hardware_info.get("type")
    )
    
    try:
        async with db_manager.get_session() as session:
            registration_service = DeviceRegistration(session)
            result = await registration_service.register_device(
                activation_key=request.activation_key,
                hardware_info=request.hardware_info,
                device_name=request.device_name
            )
            
            logger.info(
                f"Dispositivo registrado com sucesso: {result['device_id']}",
                device_id=result['device_id']
            )
            
            return DeviceRegisterResponse(**result)
    
    except ValueError as e:
        logger.warning(
            f"Erro ao registrar dispositivo: {str(e)}",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Erro inesperado ao registrar dispositivo: {str(e)}",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar dispositivo"
        )


@router.get("", response_model=List[DeviceResponse])
async def list_devices(auth_data: dict = Depends(require_auth)):
    """
    Lista todos os dispositivos do tenant autenticado
    
    Requisitos: 13.2
    """
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    
    logger.info(
        f"Listando dispositivos para tenant: {tenant_id}",
        tenant_id=str(tenant_id)
    )
    
    try:
        async with db_manager.get_session() as session:
            device_service = DeviceService(session)
            devices = await device_service.list_devices(tenant_id)
            
            return [DeviceResponse(**device.to_dict()) for device in devices]
    
    except Exception as e:
        logger.error(
            f"Erro ao listar dispositivos: {str(e)}",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar dispositivos"
        )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, auth_data: dict = Depends(require_auth)):
    """
    Obtém detalhes de um dispositivo específico
    
    Requisitos: 13.3
    """
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    device_uuid = uuid.UUID(device_id)
    
    logger.info(
        f"Buscando dispositivo: {device_id}",
        device_id=device_id,
        tenant_id=str(tenant_id)
    )
    
    try:
        async with db_manager.get_session() as session:
            device_service = DeviceService(session)
            device = await device_service.get_device(device_uuid, tenant_id)
            
            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dispositivo não encontrado"
                )
            
            return DeviceResponse(**device.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao buscar dispositivo: {str(e)}",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar dispositivo"
        )


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    request: DeviceUpdateRequest,
    auth_data: dict = Depends(require_auth)
):
    """
    Atualiza configuração de um dispositivo
    
    Requisitos: 13.4, 24.4-24.7
    """
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    device_uuid = uuid.UUID(device_id)
    
    logger.info(
        f"Atualizando dispositivo: {device_id}",
        device_id=device_id,
        tenant_id=str(tenant_id)
    )
    
    try:
        async with db_manager.get_session() as session:
            device_service = DeviceService(session)
            device = await device_service.update_device(
                device_uuid,
                tenant_id,
                name=request.name,
                config=request.config
            )
            
            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dispositivo não encontrado"
                )
            
            return DeviceResponse(**device.to_dict())
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Erro ao atualizar dispositivo: {str(e)}",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar dispositivo"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_device(device_id: str, auth_data: dict = Depends(require_auth)):
    """
    Desativa um dispositivo (soft delete)
    
    Requisitos: 3.7, 13.5
    """
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    device_uuid = uuid.UUID(device_id)
    
    logger.info(
        f"Desativando dispositivo: {device_id}",
        device_id=device_id,
        tenant_id=str(tenant_id)
    )
    
    try:
        async with db_manager.get_session() as session:
            device_service = DeviceService(session)
            success = await device_service.deactivate_device(device_uuid, tenant_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dispositivo não encontrado"
                )
            
            return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao desativar dispositivo: {str(e)}",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao desativar dispositivo"
        )


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(device_id: str, auth_data: dict = Depends(require_auth)):
    """
    Obtém status em tempo real de um dispositivo
    
    Requisitos: 13.6
    """
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    device_uuid = uuid.UUID(device_id)
    
    logger.info(
        f"Buscando status do dispositivo: {device_id}",
        device_id=device_id,
        tenant_id=str(tenant_id)
    )
    
    try:
        async with db_manager.get_session() as session:
            device_service = DeviceService(session)
            status_data = await device_service.get_device_status(device_uuid, tenant_id)
            
            if not status_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dispositivo não encontrado"
                )
            
            return DeviceStatusResponse(**status_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erro ao buscar status do dispositivo: {str(e)}",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar status"
        )


@router.post("/{device_id}/heartbeat", status_code=status.HTTP_200_OK)
async def device_heartbeat(
    device_id: str,
    request: DeviceHeartbeatRequest,
    auth_data: dict = Depends(require_device_auth)
):
    """
    Recebe heartbeat de um dispositivo
    
    Requisitos: 39.1, 39.6
    """
    # Valida que o device_id do token corresponde ao da URL
    token_device_id = auth_data.get("device_id")
    if token_device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID não corresponde ao token"
        )
    
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    device_uuid = uuid.UUID(device_id)
    
    logger.debug(
        f"Recebido heartbeat do dispositivo: {device_id}",
        device_id=device_id,
        tenant_id=str(tenant_id)
    )
    
    try:
        async with db_manager.get_session() as session:
            heartbeat_service = DeviceHeartbeat(session)
            result = await heartbeat_service.process_heartbeat(
                device_uuid,
                tenant_id,
                health_metrics=request.health_metrics
            )
            
            return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Erro ao processar heartbeat: {str(e)}",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar heartbeat"
        )


@router.post("/{device_id}/data", status_code=status.HTTP_200_OK)
async def submit_device_data(
    device_id: str,
    request: DeviceDataRequest,
    auth_data: dict = Depends(require_device_auth)
):
    """
    Recebe dados de sinal do dispositivo (RSSI ou CSI)
    Valida que plano BÁSICO não pode enviar dados CSI
    
    Requisitos: 5.2, 8.5, 8.8
    """
    # Valida que o device_id do token corresponde ao da URL
    token_device_id = auth_data.get("device_id")
    if token_device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device ID não corresponde ao token"
        )
    
    tenant_id = uuid.UUID(auth_data["tenant_id"])
    device_uuid = uuid.UUID(device_id)
    plan_type = auth_data.get("plan_type", "basic")
    
    logger.debug(
        f"Recebidos dados do dispositivo: {device_id}",
        device_id=device_id,
        tenant_id=str(tenant_id),
        data_type=request.data_type,
        plan_type=plan_type
    )
    
    # Validação: Plano BÁSICO não pode enviar dados CSI
    if plan_type == "basic" and request.data_type == "csi":
        logger.warning(
            f"Dispositivo BÁSICO tentou enviar dados CSI: {device_id}",
            device_id=device_id,
            tenant_id=str(tenant_id),
            plan_type=plan_type
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plano BÁSICO não suporta dados CSI. Faça upgrade para PREMIUM."
        )
    
    try:
        # TODO: Implementar processamento de dados (event-service)
        # Por enquanto, apenas aceita os dados
        
        logger.info(
            f"Dados aceitos do dispositivo: {device_id}",
            device_id=device_id,
            data_type=request.data_type
        )
        
        return {
            "status": "accepted",
            "device_id": device_id,
            "timestamp": request.timestamp
        }
    
    except Exception as e:
        logger.error(
            f"Erro ao processar dados do dispositivo: {str(e)}",
            device_id=device_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar dados"
        )
