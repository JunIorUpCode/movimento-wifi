# -*- coding: utf-8 -*-
"""
Notification Config Routes - Endpoints para Configuração de Notificações
Implementa CRUD de configurações de notificação
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.notification_config import (
    NotificationConfigResponse,
    NotificationConfigUpdate,
    NotificationTestRequest
)
from services.notification_service import NotificationService
from middleware.auth_middleware import get_current_tenant
from shared.database import DatabaseManager
from shared.logging import get_logger
from channels.telegram_channel import TelegramChannel
from channels.email_channel import EmailChannel
from channels.webhook_channel import WebhookChannel
from utils.encryption import decrypt_token

logger = get_logger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Database manager
db_manager = DatabaseManager("notification_schema")


async def get_db_session():
    """Dependency para obter sessão do banco de dados"""
    async with db_manager.get_session() as session:
        yield session


@router.get("/config", response_model=NotificationConfigResponse)
async def get_notification_config(
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Obtém configuração de notificações do tenant.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Isolamento Multi-Tenant**: Retorna apenas configuração do tenant autenticado
    
    **Segurança**: Não expõe tokens sensíveis (bot_token, API keys, secrets)
    
    Returns:
        NotificationConfigResponse com configuração atual
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Buscando configuração de notificações",
        tenant_id=str(tenant_id)
    )
    
    # Busca configuração
    config = await NotificationService.get_config(session, tenant_id)
    
    # Se não existe, cria configuração padrão
    if not config:
        update_data = NotificationConfigUpdate(
            enabled=True,
            channels=[],
            min_confidence=0.7,
            cooldown_seconds=300
        )
        config = await NotificationService.create_or_update_config(
            session, tenant_id, update_data
        )
    
    # Monta resposta (sem expor tokens)
    response = NotificationConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        enabled=config.enabled,
        channels=config.channels or [],
        min_confidence=config.min_confidence,
        cooldown_seconds=config.cooldown_seconds,
        quiet_hours=config.quiet_hours,
        telegram_configured=bool(config.telegram_bot_token_encrypted),
        telegram_chat_ids=config.telegram_chat_ids or [],
        email_configured=bool(config.sendgrid_api_key_encrypted),
        email_recipients=config.email_recipients or [],
        webhook_configured=bool(config.webhook_secret_encrypted),
        webhook_urls=config.webhook_urls or [],
        updated_at=config.updated_at,
        created_at=config.created_at
    )
    
    return response


@router.put("/config", response_model=NotificationConfigResponse)
async def update_notification_config(
    update_data: NotificationConfigUpdate,
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Atualiza configuração de notificações do tenant.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Isolamento Multi-Tenant**: Atualiza apenas configuração do tenant autenticado
    
    **Criptografia**: Tokens sensíveis são criptografados antes de salvar
    
    **Validações**:
    - Canais devem ser: telegram, email, webhook
    - min_confidence entre 0.0 e 1.0
    - cooldown_seconds >= 0
    - quiet_hours no formato HH:MM
    - webhook_urls devem usar HTTPS
    
    Args:
        update_data: Dados de atualização
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        NotificationConfigResponse com configuração atualizada
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Atualizando configuração de notificações",
        tenant_id=str(tenant_id)
    )
    
    # Atualiza configuração
    config = await NotificationService.create_or_update_config(
        session, tenant_id, update_data
    )
    
    # Monta resposta
    response = NotificationConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        enabled=config.enabled,
        channels=config.channels or [],
        min_confidence=config.min_confidence,
        cooldown_seconds=config.cooldown_seconds,
        quiet_hours=config.quiet_hours,
        telegram_configured=bool(config.telegram_bot_token_encrypted),
        telegram_chat_ids=config.telegram_chat_ids or [],
        email_configured=bool(config.sendgrid_api_key_encrypted),
        email_recipients=config.email_recipients or [],
        webhook_configured=bool(config.webhook_secret_encrypted),
        webhook_urls=config.webhook_urls or [],
        updated_at=config.updated_at,
        created_at=config.created_at
    )
    
    return response


@router.post("/test")
async def test_notification_channel(
    test_request: NotificationTestRequest,
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Testa canal de notificação enviando mensagem de teste.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Canais Suportados**: telegram, email, webhook
    
    **Uso**: Validar configuração antes de ativar notificações
    
    Args:
        test_request: Requisição de teste com canal
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        Dict com resultado do teste:
        {
            "success": bool,
            "message": str,
            "details": dict
        }
    
    Raises:
        HTTPException 400: Canal não configurado
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    channel = test_request.channel
    
    logger.info(
        "Testando canal de notificação",
        tenant_id=str(tenant_id),
        channel=channel
    )
    
    # Busca configuração com tokens descriptografados
    config = await NotificationService.get_decrypted_config(session, tenant_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuração de notificações não encontrada"
        )
    
    # Testa canal específico
    try:
        if channel == "telegram":
            if not config["telegram_bot_token"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telegram não configurado. Configure bot_token e chat_ids primeiro."
                )
            
            telegram_channel = TelegramChannel(
                config["telegram_bot_token"],
                config["telegram_chat_ids"]
            )
            result = await telegram_channel.test_connection()
        
        elif channel == "email":
            if not config["sendgrid_api_key"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email não configurado. Configure sendgrid_api_key e email_recipients primeiro."
                )
            
            email_channel = EmailChannel(
                config["sendgrid_api_key"],
                config["email_recipients"]
            )
            result = await email_channel.test_connection()
        
        elif channel == "webhook":
            if not config["webhook_urls"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Webhook não configurado. Configure webhook_urls primeiro."
                )
            
            webhook_channel = WebhookChannel(
                config["webhook_urls"],
                config["webhook_secret"]
            )
            result = await webhook_channel.test_connection()
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Canal inválido: {channel}"
            )
        
        return {
            "success": result["success"],
            "message": result["message"],
            "details": result
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            f"Erro ao testar canal {channel}",
            tenant_id=str(tenant_id),
            error=str(e),
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao testar canal: {str(e)}"
        )
