# -*- coding: utf-8 -*-
"""
analytics.py — Relatórios e dashboards analytics do event-service.

Endpoints:
  GET /api/analytics/events/summary      — resumo de eventos por período
  GET /api/analytics/events/daily        — eventos por dia (últimos N dias)
  GET /api/analytics/events/by-type      — distribuição por tipo de evento
  GET /api/analytics/devices/active      — dispositivos ativos vs inativos
  GET /api/analytics/tenants/usage       — uso por tenant (admin only)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ── Schemas de resposta ────────────────────────────────────────────────────────

class DailyStat(BaseModel):
    date: str
    total_events: int
    presence_events: int
    fall_events: int
    no_presence_events: int


class EventTypeStat(BaseModel):
    event_type: str
    count: int
    percentage: float


class AnalyticsSummary(BaseModel):
    period_start: str
    period_end: str
    total_events: int
    fall_detected: int
    unique_devices: int
    avg_confidence: float
    busiest_hour: int         # 0-23
    most_common_event: str


class DeviceActivity(BaseModel):
    device_id: str
    tenant_id: str
    total_events: int
    last_seen: str
    is_active: bool


class TenantUsage(BaseModel):
    tenant_id: str
    total_events: int
    active_devices: int
    falls_detected: int
    last_activity: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/events/summary", response_model=AnalyticsSummary)
async def get_events_summary(
    tenant_id: str = Query(..., description="ID do tenant"),
    days: int = Query(default=30, ge=1, le=365, description="Período em dias"),
):
    """
    Resumo analítico de eventos para o tenant no período especificado.

    Em produção, consulta o banco de dados do event-service.
    Retorna mock estruturado para demonstração.
    """
    now = datetime.utcnow()
    period_start = now - timedelta(days=days)

    # TODO: substituir por query real ao banco de dados
    # SELECT COUNT(*), event_type, AVG(confidence), MAX(detected_at)
    # FROM events WHERE tenant_id = :tenant_id AND detected_at >= :period_start
    return AnalyticsSummary(
        period_start=period_start.isoformat(),
        period_end=now.isoformat(),
        total_events=days * 48,            # ~48 eventos/dia como referência
        fall_detected=max(0, days // 10),
        unique_devices=3,
        avg_confidence=0.83,
        busiest_hour=14,                   # 14h mais movimentado
        most_common_event="PRESENCE_STILL",
    )


@router.get("/events/daily", response_model=list[DailyStat])
async def get_daily_events(
    tenant_id: str = Query(...),
    days: int = Query(default=7, ge=1, le=90),
):
    """
    Evolução diária de eventos nos últimos N dias.

    Útil para gráficos de linha/barra no painel do cliente.
    """
    now = datetime.utcnow()
    result: list[DailyStat] = []

    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).date()
        # TODO: query real — GROUP BY DATE(detected_at)
        total = 40 + (i % 7) * 8
        result.append(DailyStat(
            date=day.isoformat(),
            total_events=total,
            presence_events=int(total * 0.6),
            fall_events=1 if i % 14 == 0 else 0,
            no_presence_events=int(total * 0.35),
        ))

    return result


@router.get("/events/by-type", response_model=list[EventTypeStat])
async def get_events_by_type(
    tenant_id: str = Query(...),
    days: int = Query(default=30, ge=1, le=365),
):
    """Distribuição percentual por tipo de evento."""
    # TODO: query real — SELECT event_type, COUNT(*) GROUP BY event_type
    raw = [
        ("PRESENCE_STILL", 45),
        ("PRESENCE_MOVING", 28),
        ("NO_PRESENCE", 20),
        ("PROLONGED_INACTIVITY", 5),
        ("FALL_SUSPECTED", 2),
    ]
    total = sum(c for _, c in raw)
    return [
        EventTypeStat(event_type=et, count=c, percentage=round(c / total * 100, 1))
        for et, c in raw
    ]


@router.get("/devices/active", response_model=list[DeviceActivity])
async def get_active_devices(
    tenant_id: str = Query(...),
    inactive_threshold_hours: int = Query(default=24),
):
    """
    Lista dispositivos com indicação de ativo/inativo
    baseado no threshold de inatividade.
    """
    # TODO: query real — JOIN devices + events, verificar last heartbeat
    cutoff = datetime.utcnow() - timedelta(hours=inactive_threshold_hours)
    return [
        DeviceActivity(
            device_id="dev-001",
            tenant_id=tenant_id,
            total_events=1250,
            last_seen=datetime.utcnow().isoformat(),
            is_active=True,
        ),
        DeviceActivity(
            device_id="dev-002",
            tenant_id=tenant_id,
            total_events=380,
            last_seen=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
            is_active=True,
        ),
    ]


@router.get("/tenants/usage", response_model=list[TenantUsage])
async def get_tenants_usage(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, le=200),
):
    """
    Relatório de uso por tenant — disponível apenas para admins.

    Em produção, validar que o usuário tem role=admin antes de expor.
    """
    # TODO: query real multi-tenant com agregação por tenant_id
    now = datetime.utcnow()
    return [
        TenantUsage(
            tenant_id="tenant-demo-001",
            total_events=days * 52,
            active_devices=3,
            falls_detected=2,
            last_activity=now.isoformat(),
        ),
        TenantUsage(
            tenant_id="tenant-demo-002",
            total_events=days * 18,
            active_devices=1,
            falls_detected=0,
            last_activity=(now - timedelta(hours=3)).isoformat(),
        ),
    ]
