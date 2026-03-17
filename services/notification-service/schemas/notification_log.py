# -*- coding: utf-8 -*-
"""
NotificationLog Schemas - Schemas Pydantic para Logs de Notificações
Define estruturas de validação para logs de notificações
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class NotificationLogResponse(BaseModel):
    """
    Schema de resposta para log de notificação.
    
    Retorna informações sobre uma tentativa de envio de notificação.
    
    Attributes:
        id: ID do log
        tenant_id: ID do tenant
        event_id: ID do evento
        channel: Canal utilizado
        recipient: Destinatário
        success: Sucesso do envio
        error_message: Mensagem de erro (se houver)
        alert_data: Dados do alerta
        response_data: Resposta do canal
        retry_count: Número de tentativas
        timestamp: Momento do envio
    """
    id: UUID
    tenant_id: UUID
    event_id: UUID
    channel: str
    recipient: str
    success: bool
    error_message: Optional[str]
    alert_data: Optional[Dict[str, Any]]
    response_data: Optional[Dict[str, Any]]
    retry_count: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class NotificationLogListResponse(BaseModel):
    """
    Schema de resposta para lista de logs de notificações.
    
    Retorna lista paginada de logs.
    
    Attributes:
        logs: Lista de logs
        total: Total de logs
        page: Página atual
        page_size: Tamanho da página
        total_pages: Total de páginas
    """
    logs: List[NotificationLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
