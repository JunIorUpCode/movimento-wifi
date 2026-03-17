# -*- coding: utf-8 -*-
"""
Event Service - Serviço de Consulta de Eventos
Implementa lógica de negócio para consulta e gerenciamento de eventos
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.event import Event
from schemas.event import EventResponse, EventListResponse, EventStatsResponse
from shared.logging import get_logger

logger = get_logger(__name__)


class EventService:
    """
    Serviço de consulta e gerenciamento de eventos.
    
    Implementa operações de leitura e atualização de eventos,
    com isolamento multi-tenant.
    """
    
    @staticmethod
    async def list_events(
        session: AsyncSession,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        event_type: Optional[str] = None,
        device_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EventListResponse:
        """
        Lista eventos do tenant com paginação e filtros.
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant (isolamento multi-tenant)
            page: Número da página (começa em 1)
            page_size: Tamanho da página
            event_type: Filtro por tipo de evento (opcional)
            device_id: Filtro por dispositivo (opcional)
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
        
        Returns:
            EventListResponse com eventos paginados
        """
        logger.info(
            "Listando eventos",
            tenant_id=str(tenant_id),
            page=page,
            page_size=page_size,
            event_type=event_type
        )
        
        # Constrói query base com isolamento multi-tenant
        query = select(Event).where(Event.tenant_id == tenant_id)
        
        # Aplica filtros opcionais
        if event_type:
            query = query.where(Event.event_type == event_type)
        
        if device_id:
            query = query.where(Event.device_id == device_id)
        
        if start_date:
            query = query.where(Event.timestamp >= start_date)
        
        if end_date:
            query = query.where(Event.timestamp <= end_date)
        
        # Ordena por timestamp decrescente (mais recentes primeiro)
        query = query.order_by(Event.timestamp.desc())
        
        # Conta total de registros
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Aplica paginação
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Executa query
        result = await session.execute(query)
        events = result.scalars().all()
        
        logger.info(
            "Eventos listados",
            tenant_id=str(tenant_id),
            total=total,
            returned=len(events)
        )
        
        return EventListResponse(
            events=[EventResponse.from_orm(event) for event in events],
            total=total,
            page=page,
            page_size=page_size
        )
    
    @staticmethod
    async def get_event(
        session: AsyncSession,
        tenant_id: UUID,
        event_id: UUID
    ) -> Optional[EventResponse]:
        """
        Busca um evento específico.
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant (isolamento multi-tenant)
            event_id: ID do evento
        
        Returns:
            EventResponse se encontrado, None caso contrário
        """
        logger.info(
            "Buscando evento",
            tenant_id=str(tenant_id),
            event_id=str(event_id)
        )
        
        # Query com isolamento multi-tenant
        query = select(Event).where(
            and_(
                Event.id == event_id,
                Event.tenant_id == tenant_id
            )
        )
        
        result = await session.execute(query)
        event = result.scalar_one_or_none()
        
        if event:
            logger.info("Evento encontrado", event_id=str(event_id))
            return EventResponse.from_orm(event)
        else:
            logger.warning("Evento não encontrado", event_id=str(event_id))
            return None
    
    @staticmethod
    async def get_event_stats(
        session: AsyncSession,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EventStatsResponse:
        """
        Calcula estatísticas de eventos do tenant.
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant (isolamento multi-tenant)
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
        
        Returns:
            EventStatsResponse com estatísticas
        """
        logger.info(
            "Calculando estatísticas de eventos",
            tenant_id=str(tenant_id)
        )
        
        # Query base com isolamento multi-tenant
        base_query = select(Event).where(Event.tenant_id == tenant_id)
        
        if start_date:
            base_query = base_query.where(Event.timestamp >= start_date)
        
        if end_date:
            base_query = base_query.where(Event.timestamp <= end_date)
        
        # Total de eventos
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await session.execute(count_query)
        total_events = total_result.scalar()
        
        # Eventos por tipo
        type_query = select(
            Event.event_type,
            func.count(Event.id)
        ).where(Event.tenant_id == tenant_id).group_by(Event.event_type)
        
        if start_date:
            type_query = type_query.where(Event.timestamp >= start_date)
        if end_date:
            type_query = type_query.where(Event.timestamp <= end_date)
        
        type_result = await session.execute(type_query)
        events_by_type = {row[0]: row[1] for row in type_result}
        
        # Eventos por dispositivo
        device_query = select(
            Event.device_id,
            func.count(Event.id)
        ).where(Event.tenant_id == tenant_id).group_by(Event.device_id)
        
        if start_date:
            device_query = device_query.where(Event.timestamp >= start_date)
        if end_date:
            device_query = device_query.where(Event.timestamp <= end_date)
        
        device_result = await session.execute(device_query)
        events_by_device = {str(row[0]): row[1] for row in device_result}
        
        # Confiança média
        avg_query = select(func.avg(Event.confidence)).select_from(base_query.subquery())
        avg_result = await session.execute(avg_query)
        avg_confidence = avg_result.scalar() or 0.0
        
        # Falsos positivos
        fp_query = select(func.count()).where(
            and_(
                Event.tenant_id == tenant_id,
                Event.is_false_positive == True
            )
        )
        
        if start_date:
            fp_query = fp_query.where(Event.timestamp >= start_date)
        if end_date:
            fp_query = fp_query.where(Event.timestamp <= end_date)
        
        fp_result = await session.execute(fp_query)
        false_positives = fp_result.scalar()
        
        logger.info(
            "Estatísticas calculadas",
            tenant_id=str(tenant_id),
            total_events=total_events
        )
        
        return EventStatsResponse(
            total_events=total_events,
            events_by_type=events_by_type,
            events_by_device=events_by_device,
            avg_confidence=round(avg_confidence, 2),
            false_positives=false_positives
        )
    
    @staticmethod
    async def update_event_feedback(
        session: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        is_false_positive: bool,
        user_notes: Optional[str] = None
    ) -> Optional[EventResponse]:
        """
        Atualiza feedback do usuário sobre um evento.
        
        Args:
            session: Sessão do banco de dados
            tenant_id: ID do tenant (isolamento multi-tenant)
            event_id: ID do evento
            is_false_positive: Se o evento é um falso positivo
            user_notes: Notas do usuário
        
        Returns:
            EventResponse atualizado se encontrado, None caso contrário
        """
        logger.info(
            "Atualizando feedback do evento",
            tenant_id=str(tenant_id),
            event_id=str(event_id),
            is_false_positive=is_false_positive
        )
        
        # Busca evento com isolamento multi-tenant
        query = select(Event).where(
            and_(
                Event.id == event_id,
                Event.tenant_id == tenant_id
            )
        )
        
        result = await session.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            logger.warning("Evento não encontrado", event_id=str(event_id))
            return None
        
        # Atualiza feedback
        event.is_false_positive = is_false_positive
        event.user_notes = user_notes
        
        await session.commit()
        await session.refresh(event)
        
        logger.info(
            "Feedback atualizado",
            event_id=str(event_id),
            is_false_positive=is_false_positive
        )
        
        return EventResponse.from_orm(event)
