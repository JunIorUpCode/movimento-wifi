# -*- coding: utf-8 -*-
"""
NotificationLog Model - Modelo de Log de Notificações
Define a estrutura de logs de tentativas de notificação
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from shared.database import Base


class NotificationLog(Base):
    """
    Modelo de Log de Notificações.
    
    Registra todas as tentativas de envio de notificações, incluindo
    sucesso/falha, canal utilizado, destinatário e dados do alerta.
    
    **Isolamento Multi-Tenant**: Logs são isolados por tenant_id
    
    **Auditoria**: Mantém histórico completo de notificações enviadas
    
    Attributes:
        id: ID único do log (UUID)
        tenant_id: ID do tenant proprietário (isolamento multi-tenant)
        event_id: ID do evento que gerou a notificação
        channel: Canal utilizado (telegram, email, webhook)
        recipient: Destinatário da notificação (chat_id, email, url)
        success: Flag indicando se o envio foi bem-sucedido
        error_message: Mensagem de erro em caso de falha
        timestamp: Momento do envio
        alert_data: Dados completos do alerta enviado (JSON)
        response_data: Resposta do canal (JSON)
        retry_count: Número de tentativas de reenvio
    """
    
    __tablename__ = "notification_logs"
    __table_args__ = (
        # Índices para queries eficientes
        Index("idx_notification_logs_tenant_id", "tenant_id"),
        Index("idx_notification_logs_event_id", "event_id"),
        Index("idx_notification_logs_timestamp", "timestamp"),
        Index("idx_notification_logs_tenant_channel", "tenant_id", "channel", "timestamp"),
        {"schema": "notification_schema"}
    )
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Informações do envio
    channel = Column(String(50), nullable=False)  # telegram, email, webhook
    recipient = Column(String(500), nullable=False)  # chat_id, email, url
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Dados do alerta
    alert_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    # Retry
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, channel={self.channel}, success={self.success})>"
