# -*- coding: utf-8 -*-
"""
Notification Logs Routes - Endpoints para Logs de Notificações
Implementa consulta de logs de entrega de notificações
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.notification_log import NotificationLogListResponse
from services.notification_service import NotificationService
from middleware.auth_middleware import get_current_tenant
from shared.database import DatabaseManager
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Database manager
db_manager = DatabaseManager("notification_schema")


async def get_db_session():
    """Dependency para obter sessão do banco de dados"""
    async with db_manager.get_session() as session:
        yield session


@router.get("/logs", response_model=NotificationLogListResponse)
async def get_notification_logs(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    channel: Optional[str] = Query(None, description="Filtro por canal (telegram, email, webhook)"),
    success: Optional[bool] = Query(None, description="Filtro por sucesso (true/false)"),
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Lista logs de notificações do tenant com paginação e filtros.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Isolamento Multi-Tenant**: Retorna apenas logs do tenant autenticado
    
    **Filtros Disponíveis**:
    - channel: Canal utilizado (telegram, email, webhook)
    - success: Sucesso do envio (true/false)
    
    **Paginação**:
    - page: Número da página (começa em 1)
    - page_size: Tamanho da página (1-100)
    
    **Ordenação**: Logs mais recentes primeiro (timestamp DESC)
    
    Args:
        page: Número da página
        page_size: Tamanho da página
        channel: Filtro por canal (opcional)
        success: Filtro por sucesso (opcional)
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        NotificationLogListResponse com logs paginados
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Listando logs de notificações",
        tenant_id=str(tenant_id),
        page=page,
        page_size=page_size,
        channel=channel,
        success=success
    )
    
    # Lista logs
    result = await NotificationService.get_logs(
        session=session,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        channel=channel,
        success=success
    )
    
    return result
