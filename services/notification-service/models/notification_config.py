# -*- coding: utf-8 -*-
"""
NotificationConfig Model - Modelo de Configuração de Notificações
Define a estrutura de configuração de notificações por tenant
"""

from sqlalchemy import Column, String, Boolean, Float, Integer, JSON, DateTime, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from shared.database import Base


class NotificationConfig(Base):
    """
    Modelo de Configuração de Notificações por Tenant.
    
    Armazena as preferências de notificação de cada tenant, incluindo
    canais habilitados, thresholds, cooldown e quiet hours.
    
    **Isolamento Multi-Tenant**: Cada tenant tem sua própria configuração
    
    **Segurança**: Tokens sensíveis (bot_token, webhook_secret) são criptografados
    
    Attributes:
        id: ID único da configuração (UUID)
        tenant_id: ID do tenant proprietário (isolamento multi-tenant)
        enabled: Flag indicando se notificações estão habilitadas
        channels: Lista de canais habilitados (telegram, email, webhook)
        min_confidence: Confiança mínima para enviar notificação (0.0 a 1.0)
        cooldown_seconds: Período de cooldown entre notificações do mesmo tipo
        quiet_hours: Horários em que notificações são suprimidas (JSON)
        telegram_bot_token_encrypted: Token do bot Telegram (criptografado)
        telegram_chat_ids: Lista de chat IDs do Telegram
        email_recipients: Lista de emails para notificações
        webhook_urls: Lista de URLs de webhook
        webhook_secret_encrypted: Secret para assinatura de webhooks (criptografado)
        sendgrid_api_key_encrypted: API key do SendGrid (criptografado)
        updated_at: Timestamp da última atualização
        created_at: Timestamp de criação
    """
    
    __tablename__ = "notification_configs"
    __table_args__ = (
        # Índice para lookup rápido por tenant
        Index("idx_notification_configs_tenant_id", "tenant_id"),
        {"schema": "notification_schema"}
    )
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Configurações gerais
    enabled = Column(Boolean, default=True, nullable=False)
    channels = Column(ARRAY(String), default=[], nullable=False)  # ['telegram', 'email', 'webhook']
    min_confidence = Column(Float, default=0.7, nullable=False)  # 0.0 a 1.0
    cooldown_seconds = Column(Integer, default=300, nullable=False)  # 5 minutos padrão
    quiet_hours = Column(JSON, nullable=True)  # {"start": "22:00", "end": "07:00"}
    
    # Configurações Telegram (multi-tenant)
    telegram_bot_token_encrypted = Column(String(500), nullable=True)
    telegram_chat_ids = Column(ARRAY(String), default=[], nullable=True)
    
    # Configurações Email
    email_recipients = Column(ARRAY(String), default=[], nullable=True)
    sendgrid_api_key_encrypted = Column(String(500), nullable=True)
    
    # Configurações Webhook
    webhook_urls = Column(ARRAY(String), default=[], nullable=True)
    webhook_secret_encrypted = Column(String(500), nullable=True)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NotificationConfig(tenant_id={self.tenant_id}, enabled={self.enabled}, channels={self.channels})>"
