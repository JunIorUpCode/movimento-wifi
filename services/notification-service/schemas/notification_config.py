# -*- coding: utf-8 -*-
"""
NotificationConfig Schemas - Schemas Pydantic para Configuração de Notificações
Define estruturas de validação para configuração de notificações
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class QuietHours(BaseModel):
    """
    Schema para horários de silêncio (quiet hours).
    
    Define período em que notificações não devem ser enviadas.
    
    Attributes:
        start: Horário de início (formato HH:MM)
        end: Horário de fim (formato HH:MM)
    """
    start: str = Field(..., description="Horário de início (HH:MM)", example="22:00")
    end: str = Field(..., description="Horário de fim (HH:MM)", example="07:00")
    
    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Valida formato de horário HH:MM"""
        try:
            hours, minutes = v.split(":")
            h, m = int(hours), int(minutes)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            return v
        except:
            raise ValueError("Formato de horário inválido. Use HH:MM (ex: 22:00)")


class NotificationConfigUpdate(BaseModel):
    """
    Schema para atualização de configuração de notificações.
    
    Permite atualizar preferências de notificação do tenant.
    
    Attributes:
        enabled: Habilitar/desabilitar notificações
        channels: Lista de canais habilitados
        min_confidence: Confiança mínima para notificar (0.0 a 1.0)
        cooldown_seconds: Período de cooldown em segundos
        quiet_hours: Horários de silêncio
        telegram_bot_token: Token do bot Telegram (será criptografado)
        telegram_chat_ids: Lista de chat IDs do Telegram
        email_recipients: Lista de emails
        sendgrid_api_key: API key do SendGrid (será criptografado)
        webhook_urls: Lista de URLs de webhook
        webhook_secret: Secret para webhooks (será criptografado)
    """
    enabled: Optional[bool] = Field(None, description="Habilitar notificações")
    channels: Optional[List[str]] = Field(None, description="Canais habilitados (telegram, email, webhook)")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confiança mínima (0.0 a 1.0)")
    cooldown_seconds: Optional[int] = Field(None, ge=0, description="Cooldown em segundos")
    quiet_hours: Optional[QuietHours] = Field(None, description="Horários de silêncio")
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(None, description="Token do bot Telegram")
    telegram_chat_ids: Optional[List[str]] = Field(None, description="Chat IDs do Telegram")
    
    # Email
    email_recipients: Optional[List[str]] = Field(None, description="Lista de emails")
    sendgrid_api_key: Optional[str] = Field(None, description="API key do SendGrid")
    
    # Webhook
    webhook_urls: Optional[List[str]] = Field(None, description="URLs de webhook")
    webhook_secret: Optional[str] = Field(None, description="Secret para webhooks")
    
    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Valida canais permitidos"""
        if v is None:
            return v
        
        allowed_channels = {"telegram", "email", "webhook"}
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(f"Canal inválido: {channel}. Permitidos: {allowed_channels}")
        
        return v
    
    @field_validator("webhook_urls")
    @classmethod
    def validate_webhook_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Valida URLs de webhook (devem ser HTTPS)"""
        if v is None:
            return v
        
        for url in v:
            if not url.startswith("https://"):
                raise ValueError(f"Webhook URL deve usar HTTPS: {url}")
        
        return v


class NotificationConfigResponse(BaseModel):
    """
    Schema de resposta para configuração de notificações.
    
    Retorna configuração atual do tenant (sem expor tokens sensíveis).
    
    Attributes:
        id: ID da configuração
        tenant_id: ID do tenant
        enabled: Notificações habilitadas
        channels: Canais habilitados
        min_confidence: Confiança mínima
        cooldown_seconds: Cooldown em segundos
        quiet_hours: Horários de silêncio
        telegram_configured: Indica se Telegram está configurado
        telegram_chat_ids: Chat IDs do Telegram
        email_configured: Indica se email está configurado
        email_recipients: Lista de emails
        webhook_configured: Indica se webhook está configurado
        webhook_urls: URLs de webhook
        updated_at: Data da última atualização
        created_at: Data de criação
    """
    id: UUID
    tenant_id: UUID
    enabled: bool
    channels: List[str]
    min_confidence: float
    cooldown_seconds: int
    quiet_hours: Optional[QuietHours]
    
    # Telegram (não expõe token)
    telegram_configured: bool
    telegram_chat_ids: List[str]
    
    # Email (não expõe API key)
    email_configured: bool
    email_recipients: List[str]
    
    # Webhook (não expõe secret)
    webhook_configured: bool
    webhook_urls: List[str]
    
    updated_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationTestRequest(BaseModel):
    """
    Schema para testar canal de notificação.
    
    Permite enviar notificação de teste para validar configuração.
    
    Attributes:
        channel: Canal a testar (telegram, email, webhook)
        recipient: Destinatário específico (opcional)
    """
    channel: str = Field(..., description="Canal a testar (telegram, email, webhook)")
    recipient: Optional[str] = Field(None, description="Destinatário específico (opcional)")
    
    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        """Valida canal permitido"""
        allowed_channels = {"telegram", "email", "webhook"}
        if v not in allowed_channels:
            raise ValueError(f"Canal inválido: {v}. Permitidos: {allowed_channels}")
        return v
