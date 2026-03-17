"""
Rotas REST — Estatísticas agregadas.

Implementa Tarefa 24 | Requisitos: Fase 4
Endpoints:
  GET /api/stats               — eventos agregados por período
  GET /api/stats/patterns      — padrões comportamentais (BehaviorPattern)
  GET /api/stats/anomalies     — eventos classificados como anomalia
  GET /api/stats/performance   — métricas de performance do sistema
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import BehaviorPattern, Event, PerformanceMetric
from app.schemas.schemas import BehaviorPatternOut, EventStatsOut, PerformanceStatsOut

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=EventStatsOut)
async def get_event_stats(
    period_hours: int = Query(default=24, ge=1, le=720, description="Período em horas (1-720)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna estatísticas agregadas de eventos para o período especificado.

    - ``total_events``: total de eventos no período
    - ``by_type``: contagem por tipo de evento
    - ``avg_confidence``: confiança média dos eventos
    - ``period_hours``: período consultado
    """
    since = datetime.utcnow() - timedelta(hours=period_hours)

    # Total de eventos no período
    total_result = await db.execute(
        select(func.count(Event.id)).where(Event.timestamp >= since)
    )
    total = total_result.scalar_one() or 0

    # Contagem por tipo
    type_result = await db.execute(
        select(Event.event_type, func.count(Event.id))
        .where(Event.timestamp >= since)
        .group_by(Event.event_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    # Confiança média
    avg_result = await db.execute(
        select(func.avg(Event.confidence)).where(Event.timestamp >= since)
    )
    avg_confidence = float(avg_result.scalar_one() or 0.0)

    return EventStatsOut(
        total_events=total,
        by_type=by_type,
        avg_confidence=round(avg_confidence, 4),
        period_hours=period_hours,
    )


@router.get("/patterns", response_model=List[BehaviorPatternOut])
async def get_behavior_patterns(
    hour_of_day: int | None = Query(default=None, ge=0, le=23, description="Filtrar por hora do dia"),
    day_of_week: int | None = Query(default=None, ge=0, le=6, description="Filtrar por dia da semana (0=seg, 6=dom)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna padrões comportamentais aprendidos.

    Os padrões são indexados por hora do dia (0-23) e dia da semana (0-6),
    com probabilidade de presença e nível médio de movimento.
    """
    query = select(BehaviorPattern)

    if hour_of_day is not None:
        query = query.where(BehaviorPattern.hour_of_day == hour_of_day)
    if day_of_week is not None:
        query = query.where(BehaviorPattern.day_of_week == day_of_week)

    query = query.order_by(BehaviorPattern.day_of_week, BehaviorPattern.hour_of_day)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/anomalies")
async def get_anomalies(
    period_hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna eventos classificados como anomalia no período.

    Anomalias são eventos com ``confidence >= 0.9`` do tipo
    ``fall_suspected`` ou ``prolonged_inactivity``.
    """
    since = datetime.utcnow() - timedelta(hours=period_hours)

    result = await db.execute(
        select(Event)
        .where(
            Event.timestamp >= since,
            Event.event_type.in_(["fall_suspected", "prolonged_inactivity"]),
            Event.confidence >= 0.9,
        )
        .order_by(Event.timestamp.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return {
        "period_hours": period_hours,
        "total": len(events),
        "anomalies": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "confidence": e.confidence,
                "provider": e.provider,
            }
            for e in events
        ],
    }


@router.get("/performance", response_model=PerformanceStatsOut)
async def get_performance_stats(
    period_hours: int = Query(default=1, ge=1, le=168, description="Período em horas (1-168)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna estatísticas de performance do sistema para o período.

    Inclui latências médias (captura, processamento, detecção, total),
    uso de memória e CPU.
    """
    since = datetime.utcnow() - timedelta(hours=period_hours)

    result = await db.execute(
        select(
            func.avg(PerformanceMetric.total_latency_ms),
            func.avg(PerformanceMetric.capture_time_ms),
            func.avg(PerformanceMetric.processing_time_ms),
            func.avg(PerformanceMetric.detection_time_ms),
            func.avg(PerformanceMetric.memory_usage_mb),
            func.avg(PerformanceMetric.cpu_usage_percent),
            func.count(PerformanceMetric.id),
        ).where(PerformanceMetric.timestamp >= since)
    )
    row = result.one()

    def _f(v) -> float:
        return round(float(v), 3) if v is not None else 0.0

    return PerformanceStatsOut(
        avg_total_latency_ms=_f(row[0]),
        avg_capture_time_ms=_f(row[1]),
        avg_processing_time_ms=_f(row[2]),
        avg_detection_time_ms=_f(row[3]),
        avg_memory_usage_mb=_f(row[4]),
        avg_cpu_usage_percent=_f(row[5]),
        samples_count=row[6] or 0,
    )
