"""
Rotas REST da API FastAPI.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import MLModel, NotificationLog
from app.schemas.schemas import (
    ConfigIn,
    ConfigOut,
    EventOut,
    HealthOut,
    ModelInfoResponse,
    NotificationConfigRequest,
    NotificationConfigResponse,
    NotificationLogResponse,
    NotificationTestRequest,
    SimulationModeIn,
    StatusOut,
)
from app.services.config_service import config_service
from app.services.history_service import HistoryService
from app.services.monitor_service import monitor_service
from app.services.notification_service import NotificationService
from app.services.notification_types import Alert, NotificationConfig

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health_check():
    """Verifica status de saúde do sistema."""
    return HealthOut(
        status="ok",
        version="1.0.0",
        uptime_seconds=round(monitor_service.uptime, 1),
    )


@router.get("/status", response_model=StatusOut)
async def get_status(db: AsyncSession = Depends(get_db)):
    """Retorna estado atual do monitoramento."""
    result = monitor_service.current_result
    features = monitor_service.current_features
    total = await HistoryService.get_event_count(db)

    return StatusOut(
        is_monitoring=monitor_service.is_running,
        current_event=result.event_type.value if result else "no_presence",
        confidence=round(result.confidence, 3) if result else 0.0,
        simulation_mode=monitor_service.simulation_mode,
        provider=config_service.config.active_provider,
        uptime_seconds=round(monitor_service.uptime, 1),
        total_events=total,
        signal_data=monitor_service.current_signal or None,
        features={
            "rssi_normalized": round(features.rssi_normalized, 3),
            "rssi_smoothed": round(features.rssi_smoothed, 2),
            "signal_energy": round(features.signal_energy, 2),
            "signal_variance": round(features.signal_variance, 3),
            "rate_of_change": round(features.rate_of_change, 3),
            "instability_score": round(features.instability_score, 3),
        } if features else None,
    )


@router.get("/events", response_model=list[EventOut])
async def get_events(
    limit: int = 100,
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retorna histórico de eventos."""
    return await HistoryService.get_events(db, limit=limit, event_type=event_type)


@router.get("/config", response_model=ConfigOut)
async def get_config():
    """Retorna configuração atual."""
    return config_service.config


@router.post("/config", response_model=ConfigOut)
async def update_config(data: ConfigIn):
    """Atualiza configuração do sistema."""
    return config_service.update(data)


@router.post("/simulation/mode")
async def set_simulation_mode(data: SimulationModeIn):
    """Altera modo de simulação."""
    monitor_service.set_simulation_mode(data.mode)
    return {"status": "ok", "mode": data.mode}


@router.post("/monitor/start")
async def start_monitor():
    """Inicia o monitoramento."""
    await monitor_service.start()
    return {"status": "monitoring_started"}


@router.post("/monitor/stop")
async def stop_monitor():
    """Para o monitoramento."""
    await monitor_service.stop()
    return {"status": "monitoring_stopped"}


# --- ML Models ---

@router.get("/ml/models", response_model=List[ModelInfoResponse])
async def list_ml_models(db: AsyncSession = Depends(get_db)):
    """
    Lista todos os modelos ML disponíveis.
    
    Retorna informações sobre modelos treinados incluindo:
    - Nome e tipo do modelo
    - Accuracy e número de amostras de treinamento
    - Status de ativação
    - Metadados adicionais
    
    Implementa Requisitos 8.1, 8.2
    """
    result = await db.execute(
        select(MLModel).order_by(MLModel.created_at.desc())
    )
    models = result.scalars().all()
    return models


@router.post("/ml/models/{name}/activate")
async def activate_ml_model(name: str, db: AsyncSession = Depends(get_db)):
    """
    Ativa um modelo ML específico.
    
    Desativa todos os outros modelos do mesmo tipo e ativa o modelo especificado.
    O MonitorService será notificado para recarregar o detector com o novo modelo.
    
    Args:
        name: Nome do modelo a ser ativado
    
    Returns:
        Status da ativação e informações do modelo
    
    Raises:
        HTTPException 404: Se o modelo não for encontrado
    
    Implementa Requisitos 8.1, 8.2
    """
    # Busca o modelo
    result = await db.execute(
        select(MLModel).where(MLModel.name == name)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    
    # Desativa todos os modelos do mesmo tipo
    await db.execute(
        update(MLModel)
        .where(MLModel.model_type == model.model_type)
        .values(is_active=False)
    )
    
    # Ativa o modelo selecionado
    model.is_active = True
    await db.commit()
    await db.refresh(model)
    
    # TODO: Notificar MonitorService para recarregar detector
    # Isso será implementado quando integrarmos com MLDetector
    
    return {
        "status": "activated",
        "model": ModelInfoResponse.model_validate(model)
    }



# --- Notification Logs ---

@router.get("/notifications/logs", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    channel: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista logs de notificações enviadas.
    
    Permite filtrar por canal e paginar resultados.
    Retorna logs ordenados por timestamp decrescente (mais recentes primeiro).
    
    Args:
        channel: Filtro opcional por canal (telegram, whatsapp, webhook)
        limit: Número máximo de registros a retornar (padrão: 100)
        offset: Número de registros a pular para paginação (padrão: 0)
    
    Returns:
        Lista de logs de notificações
    
    Implementa Requisito 12.7
    """
    query = select(NotificationLog).order_by(NotificationLog.timestamp.desc())
    
    # Aplica filtro por canal se especificado
    if channel:
        query = query.where(NotificationLog.channel == channel)
    
    # Aplica paginação
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs


# --- Notification Configuration ---

@router.get("/notifications/config", response_model=NotificationConfigResponse)
async def get_notification_config():
    """
    Retorna configuração atual de notificações.
    
    Não expõe credenciais sensíveis (tokens, secrets).
    Retorna apenas informações sobre quais canais estão configurados.
    
    Returns:
        Configuração de notificações (sem credenciais)
    
    Implementa Requisitos 10.1, 10.2
    """
    # Obtém instância do NotificationService
    notification_service = monitor_service._notification_service
    config = notification_service._config
    
    return NotificationConfigResponse(
        enabled=config.enabled,
        channels=config.channels,
        min_confidence=config.min_confidence,
        cooldown_seconds=config.cooldown_seconds,
        quiet_hours=config.quiet_hours,
        telegram_configured=bool(config.telegram_bot_token and config.telegram_chat_ids),
        telegram_chat_count=len(config.telegram_chat_ids),
        whatsapp_configured=bool(
            config.twilio_account_sid and 
            config.twilio_auth_token and 
            config.twilio_whatsapp_from and 
            config.whatsapp_recipients
        ),
        whatsapp_recipient_count=len(config.whatsapp_recipients),
        webhook_configured=bool(config.webhook_urls),
        webhook_url_count=len(config.webhook_urls)
    )


@router.put("/notifications/config", response_model=NotificationConfigResponse)
async def update_notification_config(config_request: NotificationConfigRequest):
    """
    Atualiza configuração de notificações.
    
    Permite configurar:
    - Canais ativos (telegram, whatsapp, webhook)
    - Confiança mínima para alertas
    - Cooldown entre alertas
    - Horários de silêncio
    - Credenciais de cada canal
    
    Args:
        config_request: Nova configuração de notificações
    
    Returns:
        Configuração atualizada (sem credenciais)
    
    Implementa Requisitos 10.1, 10.2, 10.6
    """
    # Cria nova configuração
    new_config = NotificationConfig(
        enabled=config_request.enabled,
        channels=config_request.channels,
        min_confidence=config_request.min_confidence,
        cooldown_seconds=config_request.cooldown_seconds,
        quiet_hours=config_request.quiet_hours,
        telegram_bot_token=config_request.telegram_bot_token,
        telegram_chat_ids=config_request.telegram_chat_ids,
        twilio_account_sid=config_request.twilio_account_sid,
        twilio_auth_token=config_request.twilio_auth_token,
        twilio_whatsapp_from=config_request.twilio_whatsapp_from,
        whatsapp_recipients=config_request.whatsapp_recipients,
        webhook_urls=config_request.webhook_urls,
        webhook_secret=config_request.webhook_secret
    )
    
    # Atualiza NotificationService
    notification_service = monitor_service._notification_service
    notification_service.update_config(new_config)
    
    # Retorna configuração atualizada (sem credenciais)
    return NotificationConfigResponse(
        enabled=new_config.enabled,
        channels=new_config.channels,
        min_confidence=new_config.min_confidence,
        cooldown_seconds=new_config.cooldown_seconds,
        quiet_hours=new_config.quiet_hours,
        telegram_configured=bool(new_config.telegram_bot_token and new_config.telegram_chat_ids),
        telegram_chat_count=len(new_config.telegram_chat_ids),
        whatsapp_configured=bool(
            new_config.twilio_account_sid and 
            new_config.twilio_auth_token and 
            new_config.twilio_whatsapp_from and 
            new_config.whatsapp_recipients
        ),
        whatsapp_recipient_count=len(new_config.whatsapp_recipients),
        webhook_configured=bool(new_config.webhook_urls),
        webhook_url_count=len(new_config.webhook_urls)
    )


@router.post("/notifications/test")
async def test_notification(test_request: NotificationTestRequest):
    """
    Envia notificação de teste para um canal específico.
    
    Útil para validar configuração de canais antes de ativar alertas.
    Envia um alerta de teste com confiança 100% para o canal especificado.
    
    Args:
        test_request: Canal e mensagem de teste
    
    Returns:
        Status do envio de teste
    
    Raises:
        HTTPException 400: Se o canal não estiver configurado
        HTTPException 500: Se o envio falhar
    
    Implementa Requisito 10.6
    """
    notification_service = monitor_service._notification_service
    
    # Verifica se o canal está configurado
    if test_request.channel not in notification_service._channels:
        raise HTTPException(
            status_code=400,
            detail=f"Canal '{test_request.channel}' não está configurado. "
                   f"Canais disponíveis: {list(notification_service._channels.keys())}"
        )
    
    # Cria alerta de teste
    test_alert = Alert(
        event_type="test_notification",
        confidence=1.0,
        timestamp=datetime.now().timestamp(),
        message=test_request.message,
        details={"test": True, "channel": test_request.channel}
    )
    
    # Envia para o canal específico
    channel = notification_service._channels[test_request.channel]
    try:
        success = await channel.send(test_alert)
        
        if success:
            return {
                "status": "success",
                "channel": test_request.channel,
                "message": "Notificação de teste enviada com sucesso"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Falha ao enviar notificação de teste para '{test_request.channel}'"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar notificação de teste: {str(e)}"
        )
