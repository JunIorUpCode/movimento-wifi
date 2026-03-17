# -*- coding: utf-8 -*-
"""
Event Routes - Endpoints para Consulta de Eventos
Implementa endpoints para listar, buscar e gerenciar eventos
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID
from datetime import datetime

from schemas.event import EventResponse, EventListResponse, EventStatsResponse, EventFeedback
from services.event_service import EventService
from middleware.auth_middleware import require_tenant_auth, get_current_tenant
from shared.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    event_type: Optional[str] = Query(None, description="Filtro por tipo de evento"),
    device_id: Optional[UUID] = Query(None, description="Filtro por dispositivo"),
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Lista eventos do tenant com paginação e filtros.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Isolamento Multi-Tenant**: Retorna apenas eventos do tenant autenticado
    
    **Filtros Disponíveis**:
    - event_type: Tipo do evento (presence, movement, fall_suspected, prolonged_inactivity)
    - device_id: ID do dispositivo
    - start_date: Data inicial (ISO 8601)
    - end_date: Data final (ISO 8601)
    
    **Paginação**:
    - page: Número da página (começa em 1)
    - page_size: Tamanho da página (1-100)
    
    Args:
        page: Número da página
        page_size: Tamanho da página
        event_type: Filtro por tipo (opcional)
        device_id: Filtro por dispositivo (opcional)
        start_date: Data inicial (opcional)
        end_date: Data final (opcional)
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        EventListResponse com eventos paginados
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Listando eventos",
        tenant_id=str(tenant_id),
        page=page,
        page_size=page_size
    )
    
    result = await EventService.list_events(
        session=session,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        event_type=event_type,
        device_id=device_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return result


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Busca detalhes de um evento específico.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Isolamento Multi-Tenant**: Retorna apenas se o evento pertence ao tenant
    
    Args:
        event_id: ID do evento
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        EventResponse com detalhes do evento
    
    Raises:
        HTTPException 404: Evento não encontrado ou não pertence ao tenant
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Buscando evento",
        tenant_id=str(tenant_id),
        event_id=str(event_id)
    )
    
    event = await EventService.get_event(
        session=session,
        tenant_id=tenant_id,
        event_id=event_id
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    return event


@router.get("/timeline", response_model=EventListResponse)
async def get_event_timeline(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    device_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna timeline de eventos com filtros.
    
    Alias para list_events, mantido para compatibilidade com design.
    
    **Autenticação**: Requer JWT token do tenant
    
    Args:
        page: Número da página
        page_size: Tamanho da página
        event_type: Filtro por tipo (opcional)
        device_id: Filtro por dispositivo (opcional)
        start_date: Data inicial (opcional)
        end_date: Data final (opcional)
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        EventListResponse com eventos paginados
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    return await EventService.list_events(
        session=session,
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        event_type=event_type,
        device_id=device_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/stats", response_model=EventStatsResponse)
async def get_event_stats(
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retorna estatísticas de eventos do tenant.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Estatísticas Incluídas**:
    - Total de eventos
    - Eventos por tipo
    - Eventos por dispositivo
    - Confiança média
    - Total de falsos positivos
    
    Args:
        start_date: Data inicial (opcional)
        end_date: Data final (opcional)
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        EventStatsResponse com estatísticas
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Calculando estatísticas de eventos",
        tenant_id=str(tenant_id)
    )
    
    stats = await EventService.get_event_stats(
        session=session,
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return stats


@router.post("/{event_id}/feedback", response_model=EventResponse)
async def submit_event_feedback(
    event_id: UUID,
    feedback: EventFeedback,
    tenant_info: dict = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Submete feedback do usuário sobre um evento.
    
    Permite marcar eventos como falsos positivos e adicionar notas.
    
    **Autenticação**: Requer JWT token do tenant
    
    **Isolamento Multi-Tenant**: Atualiza apenas se o evento pertence ao tenant
    
    Args:
        event_id: ID do evento
        feedback: Feedback do usuário
        tenant_info: Informações do tenant autenticado (injetado)
        session: Sessão do banco de dados (injetado)
    
    Returns:
        EventResponse com evento atualizado
    
    Raises:
        HTTPException 404: Evento não encontrado ou não pertence ao tenant
    """
    tenant_id = UUID(tenant_info["tenant_id"])
    
    logger.info(
        "Submetendo feedback do evento",
        tenant_id=str(tenant_id),
        event_id=str(event_id),
        is_false_positive=feedback.is_false_positive
    )
    
    event = await EventService.update_event_feedback(
        session=session,
        tenant_id=tenant_id,
        event_id=event_id,
        is_false_positive=feedback.is_false_positive,
        user_notes=feedback.user_notes
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado"
        )
    
    return event
