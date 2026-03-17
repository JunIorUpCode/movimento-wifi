# -*- coding: utf-8 -*-
"""
Device Data Routes - Endpoints para Recepção de Dados de Dispositivos
Implementa endpoint para agentes locais enviarem dados
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from schemas.event import DeviceDataSubmit
from middleware.auth_middleware import require_device_auth, get_current_device
from shared.rabbitmq import get_rabbitmq_client, RabbitMQClient
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/devices", tags=["device-data"])


@router.post("/{device_id}/data", status_code=status.HTTP_202_ACCEPTED)
async def submit_device_data(
    device_id: UUID,
    data: DeviceDataSubmit,
    device_info: dict = Depends(get_current_device),
    rabbitmq: RabbitMQClient = Depends(get_rabbitmq_client)
):
    """
    Recebe dados de sinais Wi-Fi do agente local.
    
    Este endpoint é chamado pelo agente local para enviar dados processados
    de sinais Wi-Fi. Os dados são validados e publicados na fila RabbitMQ
    para processamento assíncrono.
    
    **Autenticação**: Requer JWT token do dispositivo
    
    **Validações**:
    - JWT token válido
    - device_id no path corresponde ao token
    - tenant_id do dispositivo corresponde ao token
    - Plano BÁSICO não pode enviar dados CSI
    
    **Fluxo**:
    1. Valida autenticação e autorização
    2. Valida tipo de dados vs plano
    3. Publica dados na fila RabbitMQ
    4. Retorna HTTP 202 Accepted
    
    Args:
        device_id: ID do dispositivo (deve corresponder ao token)
        data: Dados de sinais Wi-Fi processados
        device_info: Informações do dispositivo autenticado (injetado)
        rabbitmq: Cliente RabbitMQ (injetado)
    
    Returns:
        Dict com status de aceitação
    
    Raises:
        HTTPException 401: Token inválido ou expirado
        HTTPException 403: device_id não corresponde ao token ou plano não permite CSI
        HTTPException 422: Dados inválidos
    """
    # Valida que device_id corresponde ao token
    if str(device_id) != device_info["device_id"]:
        logger.warning(
            "Tentativa de enviar dados para outro dispositivo",
            token_device_id=device_info["device_id"],
            path_device_id=str(device_id)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="device_id não corresponde ao token de autenticação"
        )
    
    # Valida plano vs tipo de dados
    plan_type = device_info.get("plan_type", "basic")
    if data.data_type == "csi" and plan_type == "basic":
        logger.warning(
            "Plano BÁSICO tentou enviar dados CSI",
            tenant_id=device_info["tenant_id"],
            device_id=str(device_id)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Plano BÁSICO não suporta dados CSI. Faça upgrade para PREMIUM."
        )
    
    logger.info(
        "Dados recebidos do dispositivo",
        tenant_id=device_info["tenant_id"],
        device_id=str(device_id),
        data_type=data.data_type
    )
    
    # Prepara mensagem para fila
    message = {
        "tenant_id": device_info["tenant_id"],
        "device_id": str(device_id),
        "features": data.features,
        "timestamp": data.timestamp,
        "data_type": data.data_type
    }
    
    # Publica na fila para processamento assíncrono
    await rabbitmq.publish(
        queue_name="event_processing",
        message=message
    )
    
    logger.info(
        "Dados publicados na fila",
        tenant_id=device_info["tenant_id"],
        device_id=str(device_id)
    )
    
    return {
        "status": "accepted",
        "message": "Dados recebidos e enfileirados para processamento"
    }
