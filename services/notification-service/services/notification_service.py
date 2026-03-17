# -*- coding: utf-8 -*-
"""
Notification Service - Serviço de Gerenciamento de Notificações
Implementa lógica de negócio para configuração e logs de notificações
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from models.notification_config import NotificationConfig
from models.notification_log import NotificationLog
from schemas.notification_config import NotificationConfigUpdate, QuietHours
from schemas.notification_log import NotificationLogResponse, NotificationLogListResponse
from utils.encryption import encrypt_token, decrypt_token
from shared.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Serviço de gerenciamento de notificações.
    
    **Responsabilidades**:
    - CRUD de configurações de notificação
    - Consulta de logs de notificação
    - Criptografia de tokens sensíveis
    """
    
    @staticmethod
    async def get_config(
        session: AsyncSession,
        tenant_id: UUID
    ) -> Optional[NotificationConfig]:
        """
        Busca configuração de notificações do tenant.
        
        **Isolamento Multi-Tenant**: Filtra por tenant_id
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant
        
        Returns:
            NotificationConfig ou None se não existir
        """
        result = await session.execute(
            select(NotificationConfig).where(
                NotificationConfig.tenant_id == tenant_id
            )
        )
        
        config = result.scalar_one_or_none()
        
        logger.debug(
            "Configuração de notificação buscada",
            tenant_id=str(tenant_id),
            found=config is not None
        )
        
        return config
    
    @staticmethod
    async def create_or_update_config(
        session: AsyncSession,
        tenant_id: UUID,
        update_data: NotificationConfigUpdate
    ) -> NotificationConfig:
        """
        Cria ou atualiza configuração de notificações do tenant.
        
        **Criptografia**: Tokens sensíveis são criptografados antes de salvar
        
        **Isolamento Multi-Tenant**: Configuração isolada por tenant_id
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant
            update_data: Dados de atualização
        
        Returns:
            NotificationConfig atualizada
        """
        # Busca configuração existente
        config = await NotificationService.get_config(session, tenant_id)
        
        # Se não existe, cria nova
        if not config:
            config = NotificationConfig(tenant_id=tenant_id)
            session.add(config)
            logger.info(
                "Nova configuração de notificação criada",
                tenant_id=str(tenant_id)
            )
        
        # Atualiza campos
        if update_data.enabled is not None:
            config.enabled = update_data.enabled
        
        if update_data.channels is not None:
            config.channels = update_data.channels
        
        if update_data.min_confidence is not None:
            config.min_confidence = update_data.min_confidence
        
        if update_data.cooldown_seconds is not None:
            config.cooldown_seconds = update_data.cooldown_seconds
        
        if update_data.quiet_hours is not None:
            config.quiet_hours = update_data.quiet_hours.model_dump()
        
        # Telegram (criptografa token)
        if update_data.telegram_bot_token is not None:
            config.telegram_bot_token_encrypted = encrypt_token(update_data.telegram_bot_token)
        
        if update_data.telegram_chat_ids is not None:
            config.telegram_chat_ids = update_data.telegram_chat_ids
        
        # Email (criptografa API key)
        if update_data.sendgrid_api_key is not None:
            config.sendgrid_api_key_encrypted = encrypt_token(update_data.sendgrid_api_key)
        
        if update_data.email_recipients is not None:
            config.email_recipients = update_data.email_recipients
        
        # Webhook (criptografa secret)
        if update_data.webhook_secret is not None:
            config.webhook_secret_encrypted = encrypt_token(update_data.webhook_secret)
        
        if update_data.webhook_urls is not None:
            config.webhook_urls = update_data.webhook_urls
        
        # Atualiza timestamp
        config.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(config)
        
        logger.info(
            "Configuração de notificação atualizada",
            tenant_id=str(tenant_id),
            channels=config.channels
        )
        
        return config
    
    @staticmethod
    async def get_decrypted_config(
        session: AsyncSession,
        tenant_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Busca configuração com tokens descriptografados.
        
        **Uso Interno**: Usado pelo worker para enviar notificações
        
        **Segurança**: Tokens são descriptografados em memória
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant
        
        Returns:
            Dict com configuração e tokens descriptografados
        """
        config = await NotificationService.get_config(session, tenant_id)
        
        if not config:
            return None
        
        # Descriptografa tokens
        decrypted = {
            "tenant_id": config.tenant_id,
            "enabled": config.enabled,
            "channels": config.channels,
            "min_confidence": config.min_confidence,
            "cooldown_seconds": config.cooldown_seconds,
            "quiet_hours": config.quiet_hours,
            "telegram_bot_token": None,
            "telegram_chat_ids": config.telegram_chat_ids or [],
            "sendgrid_api_key": None,
            "email_recipients": config.email_recipients or [],
            "webhook_secret": None,
            "webhook_urls": config.webhook_urls or []
        }
        
        # Descriptografa Telegram token
        if config.telegram_bot_token_encrypted:
            try:
                decrypted["telegram_bot_token"] = decrypt_token(config.telegram_bot_token_encrypted)
            except Exception as e:
                logger.error(
                    "Erro ao descriptografar Telegram token",
                    tenant_id=str(tenant_id),
                    error=str(e)
                )
        
        # Descriptografa SendGrid API key
        if config.sendgrid_api_key_encrypted:
            try:
                decrypted["sendgrid_api_key"] = decrypt_token(config.sendgrid_api_key_encrypted)
            except Exception as e:
                logger.error(
                    "Erro ao descriptografar SendGrid API key",
                    tenant_id=str(tenant_id),
                    error=str(e)
                )
        
        # Descriptografa webhook secret
        if config.webhook_secret_encrypted:
            try:
                decrypted["webhook_secret"] = decrypt_token(config.webhook_secret_encrypted)
            except Exception as e:
                logger.error(
                    "Erro ao descriptografar webhook secret",
                    tenant_id=str(tenant_id),
                    error=str(e)
                )
        
        return decrypted
    
    @staticmethod
    async def create_log(
        session: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        channel: str,
        recipient: str,
        success: bool,
        error_message: Optional[str] = None,
        alert_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> NotificationLog:
        """
        Cria log de tentativa de notificação.
        
        **Auditoria**: Registra todas as tentativas de envio
        
        **Isolamento Multi-Tenant**: Logs isolados por tenant_id
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant
            event_id: ID do evento
            channel: Canal utilizado
            recipient: Destinatário
            success: Sucesso do envio
            error_message: Mensagem de erro (opcional)
            alert_data: Dados do alerta (opcional)
            response_data: Resposta do canal (opcional)
            retry_count: Número de tentativas
        
        Returns:
            NotificationLog criado
        """
        log = NotificationLog(
            tenant_id=tenant_id,
            event_id=event_id,
            channel=channel,
            recipient=recipient,
            success=success,
            error_message=error_message,
            alert_data=alert_data,
            response_data=response_data,
            retry_count=retry_count
        )
        
        session.add(log)
        await session.commit()
        await session.refresh(log)
        
        logger.info(
            "Log de notificação criado",
            tenant_id=str(tenant_id),
            event_id=str(event_id),
            channel=channel,
            success=success
        )
        
        return log
    
    @staticmethod
    async def get_logs(
        session: AsyncSession,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        channel: Optional[str] = None,
        success: Optional[bool] = None
    ) -> NotificationLogListResponse:
        """
        Lista logs de notificações do tenant com paginação.
        
        **Isolamento Multi-Tenant**: Retorna apenas logs do tenant
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant
            page: Número da página
            page_size: Tamanho da página
            channel: Filtro por canal (opcional)
            success: Filtro por sucesso (opcional)
        
        Returns:
            NotificationLogListResponse com logs paginados
        """
        # Constrói query base
        query = select(NotificationLog).where(
            NotificationLog.tenant_id == tenant_id
        )
        
        # Aplica filtros
        if channel:
            query = query.where(NotificationLog.channel == channel)
        
        if success is not None:
            query = query.where(NotificationLog.success == success)
        
        # Ordena por timestamp decrescente
        query = query.order_by(NotificationLog.timestamp.desc())
        
        # Conta total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Aplica paginação
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Executa query
        result = await session.execute(query)
        logs = result.scalars().all()
        
        # Calcula total de páginas
        total_pages = (total + page_size - 1) // page_size
        
        logger.debug(
            "Logs de notificação listados",
            tenant_id=str(tenant_id),
            page=page,
            total=total
        )
        
        return NotificationLogListResponse(
            logs=[NotificationLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
